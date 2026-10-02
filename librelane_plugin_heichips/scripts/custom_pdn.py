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
    print(f"data: {data} result: {result}")
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
    print(f"data: {data} result: {result}")
    assert(is_overlapping_2d(data[0], data[1]) == result)

@click.option('--instance', "instances", multiple=True)
@click.command()
@click_odb
def custom_pdn(instances, reader):
    tech = reader.db.getTech()
    
    print(instances)
    
    # Create the power gated nets for each instance
    for instance in instances:
    
        if "heichips26_instance_sram" in instance:
            continue
    
        for power_domain in ["VPWR_GATED", "VAPWR_GATED"]:
            net_name = f"{instance}_{power_domain}"
            net = reader.block.findNet(net_name)
            if net is None:
                # Create net
                print(f"Creating net: {net_name} POWER")
                net = odb.dbNet.create(reader.block, net_name)
                net.setSpecial()
                net.setSigType("POWER")
                
                # Create new SWire for our straps
                sw = odb.dbSWire.create(net, "ROUTED")

    # Via library
    via_library = {}
    vg = ViaGenerator(reader, "viaTop1Array")
    
    #reader.block.findInst(pg_name)
    
    # TODO get the union over instance + pg_hv + pg_lv
    # use that to generate the power straps
    # then connect each instance
    
    # Find instance + both power gates
    for instance in instances:
    
        if "heichips26_instance_sram" in instance:
            continue
    
        print(f"Working on {instance}!")
    
        project_inst = None
        pg_lv_inst = None
        pg_hv_inst = None
    
        for blk_inst in reader.block.getInsts():     
            if blk_inst.getName().endswith(f"{instance}_pg_lv"):
                pg_lv_inst = blk_inst
            elif blk_inst.getName().endswith(f"{instance}_pg_hv"):
                pg_hv_inst = blk_inst
            elif blk_inst.getName().endswith(instance):
                project_inst = blk_inst

        assert project_inst
        assert pg_lv_inst
        assert pg_hv_inst
        
        x_min = project_inst.getBBox().xMin()
        y_min = project_inst.getBBox().yMin()
        x_max = project_inst.getBBox().xMax()
        y_max = project_inst.getBBox().yMax()
        
        x_min = min(x_min, pg_lv_inst.getBBox().xMin())
        y_min = min(y_min, pg_lv_inst.getBBox().yMin())
        x_max = max(x_max, pg_lv_inst.getBBox().xMax())
        y_max = max(y_max, pg_lv_inst.getBBox().yMax())
        
        x_min = min(x_min, pg_hv_inst.getBBox().xMin())
        y_min = min(y_min, pg_hv_inst.getBBox().yMin())
        x_max = max(x_max, pg_hv_inst.getBBox().xMax())
        y_max = max(y_max, pg_hv_inst.getBBox().yMax())
        
        print(f"boundary: {x_min} {y_min} {x_max} {y_max}")
        
        # Draw the stripes
        for power_domain in ["VPWR_GATED", "VAPWR_GATED"]:
                
            net = reader.block.findNet(f"{instance}_{power_domain}")
            assert(net)
            
            sw = net.getSWires()[0]
            assert(sw)
        
            # Create VPWR stripes
            stripe_offset = {
                "VPWR_GATED"  : 19_000,
                "VAPWR_GATED" : 19_000 + 6_000,
            }
            stripe_pitch = round(215.04/6*1_000) # TODO use PDN_HPITCH
            stripe_width = 4_000
            
            pg_extension = 36_000
        
            for i in range(stripe_offset[power_domain], y_max - y_min - stripe_width, stripe_pitch):

                stripe_rect = odb.Rect(
                    x_min,
                    y_min + i,
                    x_max,
                    y_min + i + stripe_width
                )

                assert(stripe_rect.xMin() % 5 == 0)
                assert(stripe_rect.yMin() % 5 == 0)
                assert(stripe_rect.xMax() % 5 == 0)
                assert(stripe_rect.yMax() % 5 == 0)
                
                # Stripe
                odb.createSBoxes(sw, tech.findLayer("TopMetal1"), [stripe_rect], "STRIPE")
                
                # Create connections to ITerms of user project
                for iterm in project_inst.getITerms():
                    pin_name = iterm.getMTerm().getName()
                    print(pin_name)
                    
                    # Found the right ITerm
                    if pin_name in power_domain:
                        iterm.connect(net)

                        for mpin in iterm.getMTerm().getMPins():
                            for box in mpin.getGeometry():
                                # user project straps
                                if project_inst.getOrient() == "R0":
                                    box1 = (
                                        (project_inst.getLocation()[0] + box.xMin(), project_inst.getLocation()[1] + box.yMin()),
                                        (project_inst.getLocation()[0] + box.xMax(), project_inst.getLocation()[1] + box.yMax())
                                    )
                                else:
                                    box1 = (
                                        (project_inst.getLocation()[0] + (project_inst.getBBox().getDX() - box.xMax()), project_inst.getLocation()[1] + (project_inst.getBBox().getDY() - box.yMax())),
                                        (project_inst.getLocation()[0] + (project_inst.getBBox().getDX() - box.xMin()), project_inst.getLocation()[1] + (project_inst.getBBox().getDY() - box.yMin()))
                                    )
                        
                                # power strap
                                box2 = (
                                    (
                                        stripe_rect.xMin(),
                                        stripe_rect.yMin()
                                    ),
                                    (
                                        stripe_rect.xMax(),
                                        stripe_rect.yMax()
                                    )
                                )
                                
                                print(f"box1: {box1}")
                                print(f"box2: {box2}")
                        
                                if overlap := is_overlapping_2d(box1, box2):
                                    print(f"overlap: {overlap}")
                                    
                                    overlap_dx = overlap[1][0] - overlap[0][0]
                                    overlap_dy = overlap[1][1] - overlap[0][1]

                                    via_x = overlap[0][0] + overlap_dx//2
                                    via_y = overlap[0][1] + overlap_dy//2
                                    
                                    print(f"Creating via: w={overlap_dx} h={overlap_dy} x={via_x} y={via_y}")

                                    # The minimum value for Metal4 is 0.62um
                                    if overlap_dx < 620 or overlap_dy < 620:
                                        continue
                                    
                                    # The minimum value for TopMetal1 is 1.26um
                                    overlap_dx = max(overlap_dx, 1_260)
                                    overlap_dy = max(overlap_dy, 1_260)
                                    
                                    # Via
                                    v = vg.get4sz_ext(overlap_dx, overlap_dy)
                                    
                                    odb.createSBoxes(sw, v, [odb.Point(via_x, via_y)], "STRIPE")

                # Create connections to ITerms of the power gates
                for pg_instance, domain in [(pg_lv_inst, "VPWR_GATED"), (pg_hv_inst, "VAPWR_GATED")]:
                    if power_domain == domain:
                        for iterm in pg_instance.getITerms():
                            pin_name = iterm.getMTerm().getName()
                            print(pin_name)
                            
                            # Found the right ITerm
                            if pin_name == "GPWR":
                                iterm.connect(net)

                                for mpin in iterm.getMTerm().getMPins():
                                    for box in mpin.getGeometry():
                                        # user project straps
                                        if pg_instance.getOrient() == "R0":
                                            box1 = (
                                                (pg_instance.getLocation()[0] + box.xMin(), pg_instance.getLocation()[1] + box.yMin()),
                                                (pg_instance.getLocation()[0] + box.xMax(), pg_instance.getLocation()[1] + box.yMax())
                                            )
                                        else:
                                            box1 = (
                                                (pg_instance.getLocation()[0] + (pg_instance.getBBox().getDX() - box.xMax()), pg_instance.getLocation()[1] + (pg_instance.getBBox().getDY() - box.yMax())),
                                                (pg_instance.getLocation()[0] + (pg_instance.getBBox().getDX() - box.xMin()), pg_instance.getLocation()[1] + (pg_instance.getBBox().getDY() - box.yMin()))
                                            )
                                
                                        # power strap
                                        box2 = (
                                            (
                                                stripe_rect.xMin(),
                                                stripe_rect.yMin()
                                            ),
                                            (
                                                stripe_rect.xMax(),
                                                stripe_rect.yMax()
                                            )
                                        )
                                        
                                        print(f"box1: {box1}")
                                        print(f"box2: {box2}")
                                
                                        if overlap := is_overlapping_2d(box1, box2):
                                            print(f"overlap: {overlap}")
                                            
                                            overlap_dx = overlap[1][0] - overlap[0][0]
                                            overlap_dy = overlap[1][1] - overlap[0][1]

                                            via_x = overlap[0][0] + overlap_dx//2
                                            via_y = overlap[0][1] + overlap_dy//2
                                            
                                            print(f"Creating via: w={overlap_dx} h={overlap_dy} x={via_x} y={via_y}")

                                            # The minimum value for Metal4 is 0.62um
                                            if overlap_dx < 620 or overlap_dy < 620:
                                                continue
                                            
                                            # The minimum value for TopMetal1 is 1.26um
                                            overlap_dx = max(overlap_dx, 1_260)
                                            overlap_dy = max(overlap_dy, 1_260)
                                            
                                            # Via
                                            v = vg.get4sz_ext(overlap_dx, overlap_dy)
                                            
                                            odb.createSBoxes(sw, v, [odb.Point(via_x, via_y)], "STRIPE")
    
    
    # use the slot list as the starting point
    """
    for blk_inst in reader.block.getInsts():
        if "heichips26_instance_large_0" in blk_inst.getName():
            print(blk_inst.getName())
            
            if "_pg_hv" in blk_inst.getName():
                # Scan all ITerms
                for iterm in blk_inst.getITerms():

                    pin_name = iterm.getMTerm().getName()
                    
                    print(iterm.getName())
                    print(pin_name)
                    print(iterm.getAvgXY())
                    
                    if pin_name == "GPWR":
                        iterm.connect(net)
                    
                    for mpin in iterm.getMTerm().getMPins():
                        print(mpin.getGeometry()) #.getTechLayer()
                        
                        for box in mpin.getGeometry():
                            print(box.getTechLayer().getName())
                            print(box.getDY())
                            print(box.getDX())
                            print(box.xMin())
                            print(box.yMin())
                            print(box.xMax())
                            print(box.yMax())

            elif "_pg_lv" in blk_inst.getName():

                for net_name in ["VPWR"]:
                
                    net = reader.block.findNet(f"heichips26_instance_large_0_{net_name}_GATED")
                    assert(net)
                    
                    sw = net.getSWires()[0]
                    assert(sw)
                
                    # Create VPWR stripes
                    stripe_offset = {
                        "VPWR"  : 20_000,
                        "VAPWR" : 25_000
                    }
                    stripe_pitch = 60_000
                    stripe_width = 4_000
                    
                    pg_extension = 36_000
                
                    for i in range(stripe_offset[net_name], blk_inst.getBBox().getDY(), stripe_pitch):
                        print(i)

                        stripe_rect = odb.Rect(
                            blk_inst.getLocation()[0] - pg_extension, # TODO orient
                            blk_inst.getLocation()[1] + i,
                            blk_inst.getLocation()[0] + blk_inst.getBBox().getDX(),
                            blk_inst.getLocation()[1] + i + stripe_width
                        )
                        
                        print(dir(stripe_rect))
                        
                        # Scan all ITerms
                        for iterm in blk_inst.getITerms():
                            pin_name = iterm.getMTerm().getName()
                            print(pin_name)
                            
                            # Found the right ITerm
                            if pin_name == PDN[net.getName()]["pg"][2]:
                                iterm.connect(net)

                                for mpin in iterm.getMTerm().getMPins():
                                    for box in mpin.getGeometry():
                                        # user project straps
                                        if blk_inst.getOrient() == "R0":
                                            box1 = (
                                                (blk_inst.getLocation()[0] + box.xMin(), blk_inst.getLocation()[1] + box.yMin()),
                                                (blk_inst.getLocation()[0] + box.xMax(), blk_inst.getLocation()[1] + box.yMax())
                                            )
                                        else:
                                            box1 = (
                                                (blk_inst.getLocation()[0] + (blk_inst.getBBox().getDX() - box.xMax()), blk_inst.getLocation()[1] + (blk_inst.getBBox().getDY() - box.yMax())),
                                                (blk_inst.getLocation()[0] + (blk_inst.getBBox().getDX() - box.xMin()), blk_inst.getLocation()[1] + (blk_inst.getBBox().getDY() - box.yMin()))
                                            )
                                
                                        # power strap
                                        box2 = (
                                            (
                                                stripe_rect.xMin(),
                                                stripe_rect.yMin()
                                            ),
                                            (
                                                stripe_rect.xMax(),
                                                stripe_rect.yMax()
                                            )
                                        )
                                        
                                        print(f"box1: {box1}")
                                        print(f"box2: {box2}")
                                
                                        if overlap := is_overlapping_2d(box1, box2):
                                            print(f"overlap: {overlap}")
                                            
                                            overlap_dx = overlap[1][0] - overlap[0][0]
                                            overlap_dy = overlap[1][1] - overlap[0][1]

                                            via_x = overlap[0][0] + overlap_dx//2
                                            via_y = overlap[0][1] + overlap_dy//2
                                            
                                            print(f"Creating via: w={overlap_dx} h={overlap_dy} x={via_x} y={via_y}")

                                            # The minimum value for Metal4 is 0.62um
                                            if overlap_dx < 620 or overlap_dy < 620:
                                                continue
                                            
                                            # The minimum value for TopMetal1 is 1.26um
                                            overlap_dx = max(overlap_dx, 1_260)
                                            overlap_dy = max(overlap_dy, 1_260)
                                            
                                            # Via
                                            v = vg.get4sz_ext(overlap_dx, overlap_dy)
                                            
                                            odb.createSBoxes(sw, v, [odb.Point(via_x, via_y)], "STRIPE")
            
            # Check full hierarchy with dots?
            elif "heichips26_instance_large_0" in blk_inst.getName():
            
                for net_name in ["VPWR", "VAPWR"]:
                
                    net = reader.block.findNet(f"heichips26_instance_large_0_{net_name}_GATED")
                    assert(net)
                    
                    sw = net.getSWires()[0]
                    assert(sw)
                
                    # Create VPWR stripes
                    stripe_offset = {
                        "VPWR"  : 20_000,
                        "VAPWR" : 25_000
                    }
                    stripe_pitch = 60_000
                    stripe_width = 4_000
                    
                    pg_extension = 36_000
                
                    for i in range(stripe_offset[net_name], blk_inst.getBBox().getDY(), stripe_pitch):
                        print(i)

                        stripe_rect = odb.Rect(
                            blk_inst.getLocation()[0] - pg_extension, # TODO orient
                            blk_inst.getLocation()[1] + i,
                            blk_inst.getLocation()[0] + blk_inst.getBBox().getDX(),
                            blk_inst.getLocation()[1] + i + stripe_width
                        )
                        
                        print(dir(stripe_rect))
                        
                        # Stripe
                        odb.createSBoxes(sw, tech.findLayer("TopMetal1"), [stripe_rect], "STRIPE")
            
                        # Scan all ITerms
                        for iterm in blk_inst.getITerms():
                            pin_name = iterm.getMTerm().getName()
                            print(pin_name)
                            
                            # Found the right ITerm
                            if pin_name == net_name:
                                iterm.connect(net)

                                for mpin in iterm.getMTerm().getMPins():
                                    
                                    for box in mpin.getGeometry():
                                        print(box.getTechLayer().getName())
                                        print(box.getDY())
                                        print(box.getDX())
                                        print(box.xMin())
                                        print(box.yMin())
                                        print(box.xMax())
                                        print(box.yMax())
                                        
                                        print(f"blk_inst.getLocation(): {blk_inst.getLocation()}")
                                        
                                        if blk_inst.getOrient() == "R0":
                                        
                                            # user project straps
                                            box1 = (
                                                (blk_inst.getLocation()[0] + box.xMin(), blk_inst.getLocation()[1] + box.yMin()),
                                                (blk_inst.getLocation()[0] + box.xMax(), blk_inst.getLocation()[1] + box.yMax())
                                            )
                                        else:
                                            box1 = (
                                                (blk_inst.getLocation()[0] + (blk_inst.getBBox().getDX() - box.xMax()), blk_inst.getLocation()[1] + (blk_inst.getBBox().getDY() - box.yMax())),
                                                (blk_inst.getLocation()[0] + (blk_inst.getBBox().getDX() - box.xMin()), blk_inst.getLocation()[1] + (blk_inst.getBBox().getDY() - box.yMin()))
                                            )
                                
                                        # power strap
                                        box2 = (
                                            (
                                                stripe_rect.xMin(),
                                                stripe_rect.yMin()
                                            ),
                                            (
                                                stripe_rect.xMax(),
                                                stripe_rect.yMax()
                                            )
                                        )
                                        
                                        print(f"box1: {box1}")
                                        print(f"box2: {box2}")
                                
                                        if overlap := is_overlapping_2d(box1, box2):
                                            print(f"overlap: {overlap}")
                                            
                                            overlap_dx = overlap[1][0] - overlap[0][0]
                                            overlap_dy = overlap[1][1] - overlap[0][1]

                                            via_x = overlap[0][0] + overlap_dx//2
                                            via_y = overlap[0][1] + overlap_dy//2
                                            
                                            print(f"Creating via: w={overlap_dx} h={overlap_dy} x={via_x} y={via_y}")

                                            # The minimum value for Metal4 is 0.62um
                                            if overlap_dx < 620 or overlap_dy < 620:
                                                continue
                                            
                                            # The minimum value for TopMetal1 is 1.26um
                                            overlap_dx = max(overlap_dx, 1_260)
                                            overlap_dy = max(overlap_dy, 1_260)
                                            
                                            # Via
                                            v = vg.get4sz_ext(overlap_dx, overlap_dy)
                                            
                                            odb.createSBoxes(sw, v, [odb.Point(via_x, via_y)], "STRIPE")"""

    """vg = ViaGenerator(reader, "viaTop1Array")
    
    # Via
    v = vg.get4sz_ext(7_000, 20_000)
    odb.createSBoxes(sw, v, [odb.Point(383_040 + 7_000//2, 2200_000 + 20_000//2)], "STRIPE")"""


if __name__ == "__main__":
    custom_pdn()


