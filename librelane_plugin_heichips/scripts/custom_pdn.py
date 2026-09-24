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

@click.command()
@click_odb
def custom_pdn(reader):
    tech = reader.db.getTech()

    # Config
    PDN = {
        'heichips26_instance_large_0_VDD_GATED' : {
            'type' :  'POWER',
            'pins' : [ 'VPWR' ],
            'pg' : ( 'tt_pg_vdd_I', 'VPWR', 'GPWR' ),
        },
    }
    
    for net_name, net_desc in PDN.items():

        print(net_name)
        net = reader.block.findNet(net_name)
        if net is None:
            # Create net
            print(f"Creating net: {net_name} {net_desc['type']}")
            net = odb.dbNet.create(reader.block, net_name)
            net.setSpecial()
            net.setSigType(net_desc['type'])
    
    #reader.block.findInst(pg_name)
    
    for blk_inst in reader.block.getInsts():
        if "heichips26_instance_large_0" in blk_inst.getName():
            print(blk_inst.getName())
            
            if "_pg_" in  blk_inst.getName():
                # Scan all ITerms
                for iterm in blk_inst.getITerms():
                    pin_name = iterm.getMTerm().getName()
                    print(pin_name)
                    
                    if pin_name == "GPWR":
                        iterm.connect(net)
            
            if blk_inst.getName() == "heichips26_instance_large_0":
                # Scan all ITerms
                for iterm in blk_inst.getITerms():
                    pin_name = iterm.getMTerm().getName()
                    print(pin_name)
                    
                    if pin_name == "VPWR":
                        iterm.connect(net)

    # Create new SWire for our straps
    sw = odb.dbSWire.create(net, "ROUTED")
    
    # Stripe
    odb.createSBoxes(sw, tech.findLayer("TopMetal1"), [odb.Rect(383_040, 2200_000, 419_040 + 500_000, 2220_000)], "STRIPE")


    vg = ViaGenerator(reader, "viaTop1Array")
    
    # Via
    v = vg.get4sz_ext(7_000, 20_000)
    odb.createSBoxes(sw, v, [odb.Point(383_040 + 7_000//2, 2200_000 + 20_000//2)], "STRIPE")


if __name__ == "__main__":
    custom_pdn()


