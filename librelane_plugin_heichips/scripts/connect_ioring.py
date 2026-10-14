#!/usr/bin/env python3

# Copyright (c) 2026 Leo Moser <leo.moser@pm.me>
# Copyright (c) 2023 Sylvain Munaut <tnt@246tNt.com>
# SPDX-License-Identifier: Apache-2.0

import sys
from reader import click_odb, click, odb
import grt as GRT

class ViaGenerator:

    def __init__(self, reader, via_rule_name):
        # No known via
        self.vias = {}

        # Save interesting vars
        self.reader = reader
        self.tech = tech = reader.db.getTech()

        # Find Via Rule
        self.via_rule = tech.findViaGenerateRule(via_rule_name)

        # Identify rules for top/cut/bot
        met = []

        for i in range(self.via_rule.getViaLayerRuleCount()):
            ly_rule = self.via_rule.getViaLayerRule(i)
            ly = ly_rule.getLayer()

            # Is it the cut ?
            if ly.getType() == 'CUT':
                self.cut_ly  = ly
                self.cut_sz  = [ ly_rule.getRect().dx(), ly_rule.getRect().dy() ]
                self.cut_spc = ly_rule.getSpacing()

                # The cut spacing in the rule is center to center
                # but when creating the via we need it border to border ?!?!
                self.cut_spc[0] -= self.cut_sz[0]
                self.cut_spc[1] -= self.cut_sz[1]

            # Or Metal ?
            elif ly.getType() == 'ROUTING':
                enc = ly_rule.getEnclosure()
                met.append( (ly.getName(), ly, enc) )

            # WTF ?
            else:
                raise RuntimeError('Unknown via rule')

        met = sorted(met)

        self.bot_ly  = met[0][1]
        self.bot_enc = met[0][2]

        self.top_ly  = met[1][1]
        self.top_enc = met[1][2]

    def create(self, ncols, nrows, name=None):
        # Create via
        if name is None:
            name = f'vg_{(hash(self) & 0xffffffff):08x}_{ncols:d}x{nrows:d}'

        v = odb.dbVia.create(self.reader.block, name)
        v.setViaGenerateRule(self.via_rule)

        # Configure params
        vp = v.getViaParams()

        vp.setBottomLayer(self.bot_ly)
        vp.setCutLayer(self.cut_ly)
        vp.setTopLayer(self.top_ly)
        vp.setNumCutCols(ncols)
        vp.setNumCutRows(nrows)
        vp.setXCutSize(self.cut_sz[0])
        vp.setYCutSize(self.cut_sz[1])
        vp.setXCutSpacing(self.cut_spc[0])
        vp.setYCutSpacing(self.cut_spc[1])
        vp.setXBottomEnclosure(self.bot_enc[0])
        vp.setYBottomEnclosure(self.bot_enc[1])
        vp.setXTopEnclosure(self.top_enc[0])
        vp.setYTopEnclosure(self.top_enc[1])

        v.setViaParams(vp)

        # Done
        return v

    def get(self, ncols, nrows):
        k = (ncols, nrows)
        if k not in self.vias:
            self.vias[k] = self.create(ncols, nrows)
        return self.vias[k]

    def get4sz(self, vw, vh):
        # Compute row / columns
        ncols = (vw // (self.cut_sz[0] + self.cut_spc[0])) - 1
        nrows = (vh // (self.cut_sz[1] + self.cut_spc[1])) - 1
        return self.get(ncols, nrows)

    def get4sz_ext(self, vw, vh, bot_fit='xy', top_fit='xy'):
        # Constraints
        ncols = []
        nrows = []

        if 'x' in bot_fit:
            ncols.append( (vw - 2 * self.bot_enc[0] + self.cut_spc[0]) // (self.cut_sz[0] + self.cut_spc[0]) )

        if 'x' in top_fit:
            ncols.append( (vw - 2 * self.top_enc[0] + self.cut_spc[0]) // (self.cut_sz[0] + self.cut_spc[0]) )

        if 'y' in bot_fit:
            nrows.append( (vh - 2 * self.bot_enc[1] + self.cut_spc[1]) // (self.cut_sz[1] + self.cut_spc[1]) )

        if 'y' in top_fit:
            nrows.append( (vh - 2 * self.top_enc[1] + self.cut_spc[1]) // (self.cut_sz[1] + self.cut_spc[1]) )

        ncols = min(ncols)
        nrows = min(nrows)

        # Safety check
        if (ncols <= 0) or (nrows <= 0):
            return None

        # Get final via
        return self.get(ncols, nrows)

def is_overlapping_1d(interval1, interval2):
        
    assert(interval1[0] <= interval1[1])
    assert(interval2[0] <= interval2[1])
    
    # Swap the intervals so that
    # interval1 is always leftmost
    if interval1[0] > interval2[0]:
        tmp = interval1
        interval1 = interval2
        interval2 = tmp
    
    if interval1[1] > interval2[0]:
        return (max(interval1[0], interval2[0]), min(interval1[1], interval2[1]))

    return None

data = [
    [(10, 20), (15, 25)],
    [(10, 20), (20, 30)],
    [(10, 40), (20, 30)],
    
    [(15, 25), (10, 20)],
    [(20, 30), (10, 20)],
    [(20, 30), (10, 40)],
]

result = [
    (15, 20),
    None,
    (20, 30),
    (15, 20),
    None,
    (20, 30),
]

for data, result in zip(data, result):
    #print(f"data: {data} result: {result}")
    assert(is_overlapping_1d(data[0], data[1]) == result)


def is_overlapping_2d(box1, box2):
    x_overlap = is_overlapping_1d((box1[0][0], box1[1][0]), (box2[0][0], box2[1][0]))
    y_overlap = is_overlapping_1d((box1[0][1], box1[1][1]), (box2[0][1], box2[1][1]))

    # If both intervals are overlapping, then
    # the boxes are overlapping
    if x_overlap and y_overlap:
      return ((x_overlap[0], y_overlap[0]), (x_overlap[1], y_overlap[1]))
    
    return None

data = [
    [((10, 110), (20, 120)), ((15, 115),(25, 125))],
    [((10, 110), (20, 120)), ((20, 120),(30, 130))],
    [((10, 110), (40, 140)), ((20, 120),(30, 130))],
    
    [((15, 110), (25, 120)), ((10, 115),(20, 125))],
    [((20, 110), (30, 120)), ((10, 120),(20, 130))],
    [((20, 110), (30, 120)), ((10, 115),(40, 125))],
    
    [((10, 110), (20, 120)), ((15, 215),(25, 225))],
    [((10, 110), (20, 120)), ((20, 220),(30, 230))],
    [((10, 110), (40, 140)), ((20, 220),(30, 230))],
    
    [((15, 110), (25, 120)), ((10, 215),(20, 225))],
    [((20, 110), (30, 120)), ((10, 220),(20, 230))],
    [((20, 110), (30, 120)), ((10, 215),(40, 225))],
]

result = [
    ((15, 115), (20, 120)),
    None,
    ((20, 120), (30, 130)),
    ((15, 115), (20, 120)),
    None,
    ((20, 115), (30, 120)),
    None,
    None,
    None,
    None,
    None,
    None,
]

for data, result in zip(data, result):
    #print(f"data: {data} result: {result}")
    assert(is_overlapping_2d(data[0], data[1]) == result)

@click.command()
@click_odb
def custom_pdn(reader):
    tech = reader.db.getTech()
    
    print(reader.block)
    
    # Via library
    via_library = {}
    vg = ViaGenerator(reader, "viaTop1Array")
    
    strap_extensions = {
        "VSS": 36_080,
        "VDD": 73_280,
    }
    
    strap_obstructions_right = {
        "VSS": [],
        "VDD": [
            (2467_000, 2547_000),
            (347_000, 427_000),
        ],
    }

    strap_obstructions_left = {
        "VSS": [],
        "VDD": [
            (2467_000, 2547_000),
            (347_000, 427_000),
        ],
    }


    # get VDD VSS nets
    for net_name in ["VDD", "VSS"]:
        net = reader.block.findNet(net_name)
        
        for sw in net.getSWires():
            for sbox in sw.getWires():

                # Straps are 4um thick and >=2000um long
                if sbox.getTechLayer() and sbox.getTechLayer().getName() == "TopMetal1" and sbox.getDY() == 4_000 and sbox.getDX() >= 2000_000:

                    # Check if it's obstructed
                    skip = False
                    for obs in strap_obstructions_right[net_name]:
                        if sbox.yMin() >= obs[0] and sbox.yMin() <= obs[1]:
                            skip = True
                            break
                        if sbox.yMax() >= obs[0] and sbox.yMax() <= obs[1]:
                            skip = True
                            break
                    if skip:
                        continue
                    
                    strap_extension = strap_extensions[net_name]
                    v = vg.get4sz_ext(15_800, 4_000)
                    
                    # Right extension
                    odb.createSBoxes(sw, tech.findLayer("TopMetal1"), [odb.Rect(sbox.xMax(), sbox.yMin(), sbox.xMax() + strap_extension, sbox.yMax())], "STRIPE")
                    
                    # Add via right
                    odb.createSBoxes(sw, v, [odb.Point(sbox.xMax() + strap_extension - 15_800//2, sbox.yMin() + sbox.getDY()//2)], "STRIPE")
                    
                    # Left extension
                    odb.createSBoxes(sw, tech.findLayer("TopMetal1"), [odb.Rect(sbox.xMin() - strap_extension, sbox.yMin(), sbox.xMin(), sbox.yMax())], "STRIPE")

                    # Add via left
                    odb.createSBoxes(sw, v, [odb.Point(sbox.xMin() - strap_extension + 15_800//2, sbox.yMin() + sbox.getDY()//2)], "STRIPE")

if __name__ == "__main__":
    custom_pdn()
