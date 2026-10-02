#!/usr/bin/env python3

# Copyright (c) 2026 FABulous Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import sys
import glob
import yaml
import fnmatch
import argparse
from decimal import Decimal, getcontext
getcontext().prec = 9

from contextlib import redirect_stdout

from pathlib import Path

from librelane.flows import Flow, FlowError
from librelane.common import get_pdk_hash
from librelane.logging import (
    verbose,
    debug,
    info,
    rule,
    success,
    warn,
    err,
    subprocess,
)

__dir__ = os.path.dirname(os.path.realpath(__file__))

FABRIC_NAME = "classic_fabric_heichips26"
FABRIC_HEIGHT = 11
FABRIC_WIDTH = 6
FABRIC_NUM_IO_NORTH = 16
FABRIC_NUM_IO_SOUTH = 16
BELS_PER_IO_TILE = ['A', 'B', 'C', 'D']
NUM_SRAM = 1
SRAM_WIDTH = 32

def main(gui, nodrc, pdk, pdk_root, scl, tag=None, last_run=False):
    target_flow = Flow.factory.get("Chip")

    # Magic reports some overlaps which can be ignored
    target_flow = target_flow.Substitute([("Checker.IllegalOverlap", None)])
    
    # Render the layout after sealring insertion
    target_flow = target_flow.Substitute([("KLayout.Render", None)])
    target_flow = target_flow.Substitute([("+KLayout.SealRing", "KLayout.Render")])

    # No IR-drop report
    target_flow = target_flow.Substitute([("OpenROAD.IRDropReport", None)])

    # Apply custom PDN script before general PDN generation
    target_flow = target_flow.Substitute([("+Odb.AddPDNObstructions", "Odb.CustomPDN")])

    # Use Magic filler generation instead of KLayout
    target_flow = target_flow.Substitute([("KLayout.Filler", "Magic.Filler")])

    # Write OASIS
    target_flow = target_flow.Substitute([("+Magic.Filler", "KLayout.ConvertOASIS")])
    
    # Always disable Magic.DRC
    target_flow = target_flow.Substitute([("Magic.DRC", None)])
    
    # Disable DRC checks
    if nodrc:
        target_flow = target_flow.Substitute([("KLayout.DRC", None)])
        target_flow = target_flow.Substitute([("KLayout.Antenna", None)])
        target_flow = target_flow.Substitute([("KLayout.Density", None)])

    # GUI flows
    if gui == "openroad":
        target_flow = Flow.factory.get("OpenInOpenROAD")

    if gui == "klayout":
        target_flow = Flow.factory.get("OpenInKLayout")

    common_config_path = os.path.join(__dir__, "config.yaml")

    # Run the flow
    config = yaml.safe_load(open(common_config_path))
    
    config["DRT_OPT_ITERS"] = 10 # TODO
    
    print(config["HEICHIPS_SLOTS"])
    
    slot_map = config["HEICHIPS_SLOTS"]
    
    add_user_projects(config)
    
    instantiate_user_projects(config, slot_map)
    
    generate_rtl_wrapper(os.path.join(__dir__, "../src/fabric_wrapper.sv"), slot_map)

    design_dir = os.path.join(__dir__)
    print(f"design_dir: {design_dir}")
    
    print(f"pdk_root: {pdk_root}")
    print(f"pdk: {pdk}")
    print(f"scl: {scl}")
    
    flow = target_flow(
        config,
        design_dir=design_dir,
        pdk_root=pdk_root,
        pdk=pdk,
    )
    
    state_out = flow.start(tag=tag, last_run=last_run)

    print("Done!")


def add_user_projects(config):

    # Add the user projects
    keys = ["project-name", "top-cell", "team-members", "slot-size", "analog-pins", "short-description", "long-description", "gds-path", "lef-path", "header-path"]
    for config_path in glob.glob(os.path.join(__dir__, "../ip/user_projects/*/submission.yaml")):
        print(f"Reading: {config_path}")
        
        with open(config_path) as ifile:
            project_config = yaml.safe_load(ifile)
        
            for key in keys:
                if not key in project_config:
                    err(f"Config is missing a key ({key})")
                    sys.exit(1)
        
                print(f"{key}: {project_config[key]}")
            
            gds = list(Path(config_path).parent.glob(project_config["gds-path"]))
            if len(gds) > 1:
                print(f"'gds-path' can only refer to a single gds. ({gds})")
                sys.exit(1)
            input_layout = gds[0]
            
            lef = list(Path(config_path).parent.glob(project_config["lef-path"]))
            if len(lef) > 1:
                print(f"'lef-path' can only refer to a single lef. ({lef})")
                sys.exit(1)
            input_lef = lef[0]
            
            header = list(Path(config_path).parent.glob(project_config["header-path"]))
            if len(header) > 1:
                print(f"'header-path' can only refer to a single header. ({header})")
                sys.exit(1)
            input_header = header[0]
            
            print(input_layout)
            print(input_lef)
            print(input_header)
            
            config["MACROS"][project_config["top-cell"]] = {
                "gds": [input_layout],
                "lef": [input_lef],
                "vh": [input_header],
                "instances": {},
            }

def instantiate_user_projects(config, slot_map):
    
    # Instantiate the user projects
    for i, (coords, project_tuple) in enumerate(slot_map.items()):
    
        if project_tuple is None:
            continue
    
        module, instance = project_tuple[0]
        
        # Adjust if fabric changes
        coords_x = int(coords[1])
        coords_y = 9 - int(coords[3])
        
        if module == "RM_IHPSG13_1P_1024x32_c2_bm_bist":
        
            instance_x = 0.48 * 873 + 100 if coords_x == 0 else 0.48 * 4340 + 100
            instance_y = 1333*0.42 + 512*coords_y*0.42
        
            config["MACROS"][module]["instances"][f"heichips26_core.fabric_wrapper.{instance}"] = {
                "location": (instance_x, instance_y),
                "orientation": "FE" if coords_x == 0 else "E",
            }
        
            config["PDN_MACRO_CONNECTIONS"].append(f"heichips26_core.fabric_wrapper.{instance} VDD VSS VDD! VSS!")
            config["PDN_MACRO_CONNECTIONS"].append(f"heichips26_core.fabric_wrapper.{instance} VDD VSS VDDARRAY! VSS!")
        
        elif "small" in instance:
        
            instance_x = Decimal(0.48) * 873 if coords_x == 0 else Decimal(0.48) * 4340
            instance_y = Decimal(1333)*Decimal(0.42) + Decimal(512)*Decimal(coords_y)*Decimal(0.42)
            instance_width = Decimal(500)
            instance_height = Decimal(200)
        
            config["MACROS"][module]["instances"][f"heichips26_core.fabric_wrapper.{instance}"] = {
                "location": (instance_x, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # LV power gate
            config["MACROS"]["hm_pg_lv_17x200"]["instances"][f"heichips26_core.fabric_wrapper.{instance}_pg_lv"] = {
                "location": (instance_x - 18 if coords_x == 0 else instance_x + 501, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # HV power gate
            config["MACROS"]["hm_pg_hv_17x200"]["instances"][f"heichips26_core.fabric_wrapper.{instance}_pg_hv"] = {
                "location": (instance_x - 36 if coords_x == 0 else instance_x + 519, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }

            config["PDN_MACRO_CONNECTIONS"].append(f"heichips26_core.fabric_wrapper.{instance} VSS VSS VGND VGND")
            
            for metal in ["Metal4", "TopMetal1"]:
                config["ROUTING_OBSTRUCTIONS"].append([metal, instance_x, instance_y, instance_x + instance_width, instance_y + instance_height])

            for metal in ["Metal4"]:
                config["PDN_OBSTRUCTIONS"].append([metal, instance_x, instance_y, instance_x + instance_width, instance_y + instance_height])

        elif "large" in instance:
        
            instance_x = Decimal(Decimal(0.48) * 873 if coords_x == 0 else Decimal(0.48) * 4340)
            instance_y = Decimal(Decimal(1333)*Decimal(0.42) + Decimal(512)*Decimal(coords_y)*Decimal(0.42))
            instance_width = Decimal(500)
            instance_height = Decimal(415)
        
            config["MACROS"][module]["instances"][f"heichips26_core.fabric_wrapper.{instance}"] = {
                "location": (instance_x, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # LV power gate
            config["MACROS"]["hm_pg_lv_17x415"]["instances"][f"heichips26_core.fabric_wrapper.{instance}_pg_lv"] = {
                "location": (instance_x - 18 if coords_x == 0 else instance_x + 501, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # HV power gate
            config["MACROS"]["hm_pg_hv_17x415"]["instances"][f"heichips26_core.fabric_wrapper.{instance}_pg_hv"] = {
                "location": (instance_x - 36 if coords_x == 0 else instance_x + 519, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }

            config["PDN_MACRO_CONNECTIONS"].append(f"heichips26_core.fabric_wrapper.{instance} VSS VSS VGND VGND")
            
            for metal in ["Metal4", "TopMetal1"]:
                config["ROUTING_OBSTRUCTIONS"].append([metal, instance_x, instance_y, instance_x + instance_width, instance_y + instance_height])

            for metal in ["Metal4"]:
                config["PDN_OBSTRUCTIONS"].append([metal, instance_x, instance_y, instance_x + instance_width, instance_y + instance_height])

        elif "tiny" in instance:
        
            module_2, instance_2 = project_tuple[1]

            instance_x = Decimal(0.48) * 873 if coords_x == 0 else Decimal(0.48) * 4340
            instance_y = Decimal(1333)*Decimal(0.42) + Decimal(512)*Decimal(coords_y)*Decimal(0.42)
            instance_width = Decimal(200)
            instance_height = Decimal(200)

            config["MACROS"][module]["instances"][f"heichips26_core.fabric_wrapper.{instance}"] = {
                "location": (instance_x, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # LV power gate
            config["MACROS"]["hm_pg_lv_17x200"]["instances"][f"heichips26_core.fabric_wrapper.{instance}_pg_lv"] = {
                "location": (instance_x - 17 if coords_x == 0 else instance_x + 201, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # HV power gate
            config["MACROS"]["hm_pg_hv_17x200"]["instances"][f"heichips26_core.fabric_wrapper.{instance}_pg_hv"] = {
                "location": (instance_x - 35 if coords_x == 0 else instance_x + 219, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }

            config["PDN_MACRO_CONNECTIONS"].append(f"heichips26_core.fabric_wrapper.{instance} VDD VSS VPWR VGND")

            for metal in ["Metal4", "TopMetal1"]:
                config["ROUTING_OBSTRUCTIONS"].append(["Metal4", instance_x, instance_y, instance_x + instance_width, instance_y + instance_height])

            for metal in ["Metal4"]:
                config["PDN_OBSTRUCTIONS"].append(["Metal4", instance_x, instance_y, instance_x + instance_width, instance_y + instance_height])

            config["MACROS"][module_2]["instances"][f"heichips26_core.fabric_wrapper.{instance_2}"] = {
                "location": (instance_x + 300 if coords_x == 0 else instance_x + 300, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # LV power gate
            config["MACROS"]["hm_pg_lv_17x200"]["instances"][f"heichips26_core.fabric_wrapper.{instance_2}_pg_lv"] = {
                "location": (instance_x + 250 - 17 if coords_x == 0 else instance_x + 250 + 251, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }
            
            # HV power gate
            config["MACROS"]["hm_pg_hv_17x200"]["instances"][f"heichips26_core.fabric_wrapper.{instance_2}_pg_hv"] = {
                "location": (instance_x + 250 - 35 if coords_x == 0 else instance_x + 250 + 269, instance_y),
                "orientation": "FN" if coords_x == 0 else "N",
            }

            config["PDN_MACRO_CONNECTIONS"].append(f"heichips26_core.fabric_wrapper.{instance_2} VSS VSS VGND VGND")

            for metal in ["Metal4", "TopMetal1"]:
                config["ROUTING_OBSTRUCTIONS"].append([metal, instance_x + 300, instance_y, instance_x + instance_width + 300, instance_y + instance_height])

            for metal in ["Metal4"]:
                config["PDN_OBSTRUCTIONS"].append([metal, instance_x + 300, instance_y, instance_x + instance_width + 300, instance_y + instance_height])
        else:
            print(f"Error: Couldn't match {module} {instance}")
            return 1


def generate_rtl_wrapper(file, slot_map):
    
    with open(file, 'w') as f:
        with redirect_stdout(f):

            print("""`default_nettype none

    module fabric_wrapper #(
        parameter FrameBitsPerRow = 32,
        parameter MaxFramesPerCol = 20,
        
        parameter NumColumns = 6,
        parameter NumRows = 11,
        
        parameter FABRIC_NUM_IO_NORTH = 16,
        parameter FABRIC_NUM_IO_SOUTH = 16
    )(""")
            print("    `ifdef USE_POWER_PINS")
            print("    inout wire VPWR,")
            print("    inout wire VGND,")
            print("    inout wire VAPWR,")
            print("    `endif\n")

            print(f'    // Configuration')
            print("""    input  logic [(FrameBitsPerRow*NumRows)-1:0]    FrameData_i,""")
            print("""    input  logic [(MaxFramesPerCol*NumColumns)-1:0] FrameStrobe_i,\n""")

            print(f'    // Fabric is configured')
            print("""    input                                configured_i,""")
            print("""    input                                sys_reset_i,\n""")

            # I/Os
            print(f'    // I/Os North')
            print("""    input  [FABRIC_NUM_IO_NORTH-1:0]      io_north_in_i,
    output [FABRIC_NUM_IO_NORTH-1:0]      io_north_out_o,
    output [FABRIC_NUM_IO_NORTH-1:0]      io_north_oe_o,\n""")

            print(f'    // I/Os South')
            print("""    input  [FABRIC_NUM_IO_SOUTH-1:0]      io_south_in_i,
    output [FABRIC_NUM_IO_SOUTH-1:0]      io_south_out_o,
    output [FABRIC_NUM_IO_SOUTH-1:0]      io_south_oe_o\n""")

            print(");\n")

            for i, (coords, projects) in enumerate(slot_map.items()):
            
                if projects is None:
                    continue
            
                if any(x in projects[0][1] for x in ["tiny", "small", "large"]):
            
                    print(f'    // TT_PROJECT {i} ({coords})')
                    if "large" in projects[0][1]:
                        print(f'    logic [15:0] tt_project_{i}_ui_in;')
                        print(f'    logic [15:0] tt_project_{i}_uo_out;')
                        print(f'    logic [15:0] tt_project_{i}_uio_in;')
                        print(f'    logic [15:0] tt_project_{i}_uio_out;')
                        print(f'    logic [15:0] tt_project_{i}_uio_oe;')
                    else:
                        if len(projects) > 1:
                            print(f'    logic tt_project_{i}_select_slot;')
                        print(f'    logic [7:0] tt_project_{i}_ui_in;')
                        print(f'    logic [7:0] tt_project_{i}_uo_out;')
                        print(f'    logic [7:0] tt_project_{i}_uio_in;')
                        print(f'    logic [7:0] tt_project_{i}_uio_out;')
                        print(f'    logic [7:0] tt_project_{i}_uio_oe;')
                    print(f'    logic  tt_project_{i}_ena;')
                    print(f'    logic  tt_project_{i}_clk;')
                    print(f'    logic  tt_project_{i}_rst_n;')
                    print(f'    logic  tt_project_{i}_enable_power;\n')

                # SRAM
                if "sram" in projects[0][1]:
                    print(f'    // SRAM {i}')
                    print(f"""    logic [{SRAM_WIDTH-1}:0] fabric_sram_{i}_dout_i;
    logic [9 :0] fabric_sram_{i}_addr_o;
    logic [{SRAM_WIDTH-1}:0] fabric_sram_{i}_bm_o;
    logic [{SRAM_WIDTH-1}:0] fabric_sram_{i}_din_o;
    logic        fabric_sram_{i}_wen_o;
    logic        fabric_sram_{i}_men_o;
    logic        fabric_sram_{i}_ren_o;
    logic        fabric_sram_{i}_clk_o;
    logic        fabric_sram_{i}_tie_high_o;
    logic        fabric_sram_{i}_tie_low_o;\n""")


            print(f"""    {FABRIC_NAME}
    //#(
    //    .MaxFramesPerCol(MaxFramesPerCol),
    //    .FrameBitsPerRow(FrameBitsPerRow)
    //)
    {FABRIC_NAME}
    (""")

            print(f"""        .FrameData      (FrameData_i),""")
            print(f"""        .FrameStrobe    (FrameStrobe_i),\n""")

            # I/Os
            print(f"""        // North I/Os""")
            num_bels = len(BELS_PER_IO_TILE)
            IO_NORTH_OFFSET = 1
            for i in range(IO_NORTH_OFFSET,(FABRIC_NUM_IO_NORTH//num_bels)+1):
                for j, bel in enumerate(BELS_PER_IO_TILE):
                    print(f"""        .Tile_X{i}Y0_{bel}_OUT_top(io_north_in_i[{(i-IO_NORTH_OFFSET)*num_bels+j}]),
        .Tile_X{i}Y0_{bel}_IN_top(io_north_out_o[{(i-IO_NORTH_OFFSET)*num_bels+j}]),
        .Tile_X{i}Y0_{bel}_EN_top(io_north_oe_o[{(i-IO_NORTH_OFFSET)*num_bels+j}]),\n""")

            # I/Os
            print(f"""        // South I/Os""")
            num_bels = len(BELS_PER_IO_TILE)
            IO_SOUTH_OFFSET = 1
            for i in range(IO_SOUTH_OFFSET,(FABRIC_NUM_IO_SOUTH//num_bels)+1):
                for j, bel in enumerate(BELS_PER_IO_TILE):
                    print(f"""        .Tile_X{i}Y{FABRIC_HEIGHT-1}_{bel}_OUT_top(io_south_in_i[{(i-IO_SOUTH_OFFSET)*num_bels+j}]),
        .Tile_X{i}Y{FABRIC_HEIGHT-1}_{bel}_IN_top(io_south_out_o[{(i-IO_SOUTH_OFFSET)*num_bels+j}]),
        .Tile_X{i}Y{FABRIC_HEIGHT-1}_{bel}_EN_top(io_south_oe_o[{(i-IO_SOUTH_OFFSET)*num_bels+j}]),\n""")

            # SYS_RESET
            print(f"""        // SYS_RESET""")
            print(f"""        .Tile_X0Y10_SYS_RESET_RESET_top(sys_reset_i),\n""")

            # TT_PROJECT
            for i, (coords, projects) in enumerate(slot_map.items()):
            
                if projects is None:
                    continue
            
                if any(x in projects[0][1] for x in ["tiny", "small", "large"]):
            
                    if "large" in projects[0][1]:
                        bits = 16
                    else:
                        bits = 8
                    print(f'        // TT_PROJECT {i} ({coords})')
                    
                    if len(projects) > 1:
                        print(f'        .Tile_{coords}_SELECT_SLOT_TT_PROJECT(tt_project_{i}_select_slot),')
                    for j in range(bits):
                        print(f'        .Tile_{coords}_UI_IN_TT_PROJECT{j}(tt_project_{i}_ui_in[{j}]),')
                    for j in range(bits):
                        print(f'        .Tile_{coords}_UO_OUT_TT_PROJECT{j}(tt_project_{i}_uo_out[{j}]),')
                    for j in range(bits):
                        print(f'        .Tile_{coords}_UIO_IN_TT_PROJECT{j}(tt_project_{i}_uio_in[{j}]),')
                    for j in range(bits):
                        print(f'        .Tile_{coords}_UIO_OUT_TT_PROJECT{j}(tt_project_{i}_uio_out[{j}]),')
                    for j in range(bits):
                        print(f'        .Tile_{coords}_UIO_OE_TT_PROJECT{j}(tt_project_{i}_uio_oe[{j}]),')

                    print(f'        .Tile_{coords}_ENA_TT_PROJECT(tt_project_{i}_ena),')
                    print(f'        .Tile_{coords}_CLK_TT_PROJECT(tt_project_{i}_clk),')
                    print(f'        .Tile_{coords}_RST_N_TT_PROJECT(tt_project_{i}_rst_n),')
                    print(f'        .Tile_{coords}_ENABLE_POWER_TT_PROJECT(tt_project_{i}_enable_power)', end="")

                # SRAM
                if "sram" in projects[0][1]:

                    print(f'        // SRAM {i}')
                    for j in range(SRAM_WIDTH):
                        print(f'        .Tile_{coords}_DOUT_SRAM{j}(fabric_sram_{i}_dout_i[{j}]),')
                    for j in range(10):
                        print(f'        .Tile_{coords}_ADDR_SRAM{j}(fabric_sram_{i}_addr_o[{j}]),')
                    for j in range(SRAM_WIDTH):
                        print(f'        .Tile_{coords}_BM_SRAM{j}(fabric_sram_{i}_bm_o[{j}]),')
                    for j in range(SRAM_WIDTH):
                        print(f'        .Tile_{coords}_DIN_SRAM{j}(fabric_sram_{i}_din_o[{j}]),')
                    print(f'        .Tile_{coords}_WEN_SRAM(fabric_sram_{i}_wen_o),')
                    print(f'        .Tile_{coords}_MEN_SRAM(fabric_sram_{i}_men_o),')
                    print(f'        .Tile_{coords}_REN_SRAM(fabric_sram_{i}_ren_o),')
                    print(f'        .Tile_{coords}_CLK_SRAM(fabric_sram_{i}_clk_o),')
                    print(f'        .Tile_{coords}_TIE_HIGH_SRAM(fabric_sram_{i}_tie_high_o),')
                    print(f'        .Tile_{coords}_TIE_LOW_SRAM(fabric_sram_{i}_tie_low_o),')
                    print(f'        .Tile_{coords}_CONFIGURED_top(configured_i)', end="")
                
                if i == len(slot_map)-1:
                    print('')
                else:
                    print(',\n')
                    
            print("    );\n")

            for i, (coords, projects) in enumerate(slot_map.items()):

                if projects is None:
                    continue

                if any(x in projects[0][1] for x in ["tiny", "small", "large"]):

                    # Default small height
                    pg_lv = "hm_pg_lv_17x200"
                    pg_hv = "hm_pg_hv_17x200"
                
                    # A single "large" or "small" user project
                    if len(projects) == 1:
                        if not projects[0]:
                            print(f"""    assign tt_project_{i}_uo_out  = '0;
                assign tt_project_{i}_uio_out = '0;
                assign tt_project_{i}_uio_oe  = '0;\n""")
                        else:
                            module, instance = projects[0]

                            if "heichips26_instance_large" in instance:
                                pg_lv = "hm_pg_lv_17x415"
                                pg_hv = "hm_pg_hv_17x415"

                            print(f"""    (* keep *) {module} {instance} (
            .clk        (tt_project_{i}_clk),
            .rst_n      (tt_project_{i}_rst_n),
            .ena        (tt_project_{i}_ena),
            .ui_in      (tt_project_{i}_ui_in),
            .uio_in     (tt_project_{i}_uio_in),
            .uo_out     (tt_project_{i}_uo_out),
            .uio_out    (tt_project_{i}_uio_out),
            .uio_oe     (tt_project_{i}_uio_oe)""")
                            print(f"""    );\n""")
                            
                            print(f"""    (* keep *) {pg_lv} {instance}_pg_lv (
            `ifdef USE_POWER_PINS
            .VPWR (VPWR),
            .GND  (VGND),
            .GPWR (),
            `endif
            .CTRL (tt_project_{i}_enable_power && configured_i)""")
                            print(f"""    );\n""")
                            
                            print(f"""    (* keep *) {pg_hv} {instance}_pg_hv (
            `ifdef USE_POWER_PINS
            .VAPWR (VAPWR),
            .VDPWR (VPWR),
            .GND   (VGND),
            .GPWR  (),
            `endif
            .CTRL (tt_project_{i}_enable_power && configured_i)""")
                            print(f"""    );\n""")
                            
                    # Two "tiny" user projects
                    else:
                            module, instance = projects[0]
                            
                            print(f'    logic [7:0] tt_project_{i}_0_uo_out;')
                            print(f'    logic [7:0] tt_project_{i}_0_uio_out;')
                            print(f'    logic [7:0] tt_project_{i}_0_uio_oe;')
                            print(f'')
                            print(f'    logic [7:0] tt_project_{i}_1_uo_out;')
                            print(f'    logic [7:0] tt_project_{i}_1_uio_out;')
                            print(f'    logic [7:0] tt_project_{i}_1_uio_oe;')
                            print(f'')
                            print(f'    assign tt_project_{i}_uo_out  = tt_project_{i}_select_slot ? tt_project_{i}_1_uo_out : tt_project_{i}_0_uo_out;')
                            print(f'    assign tt_project_{i}_uio_out = tt_project_{i}_select_slot ? tt_project_{i}_1_uio_out : tt_project_{i}_0_uio_out;')
                            print(f'    assign tt_project_{i}_uio_oe  = tt_project_{i}_select_slot ? tt_project_{i}_1_uio_oe : tt_project_{i}_0_uio_oe;')
                            print(f'')
                    
                            print(f"""    (* keep *) {module} {instance} (
            .clk        (tt_project_{i}_clk),
            .rst_n      (tt_project_{i}_rst_n),
            .ena        (tt_project_{i}_ena),
            .ui_in      (tt_project_{i}_ui_in),
            .uio_in     (tt_project_{i}_uio_in),
            .uo_out     (tt_project_{i}_0_uo_out),
            .uio_out    (tt_project_{i}_0_uio_out),
            .uio_oe     (tt_project_{i}_0_uio_oe)""")
                            print(f"""    );\n""")

                            print(f"""    (* keep *) {pg_lv} {instance}_pg_lv (
            `ifdef USE_POWER_PINS
            .VPWR  (VPWR),
            .GND   (VGND),
            .GPWR  (),
            `endif
            .CTRL (tt_project_{i}_enable_power && configured_i)""")
                            print(f"""    );\n""")
                            
                            print(f"""    (* keep *) {pg_hv} {instance}_pg_hv (
            `ifdef USE_POWER_PINS
            .VAPWR (VAPWR),
            .VDPWR (VPWR),
            .GND   (VGND),
            .GPWR  (),
            `endif
            .CTRL (tt_project_{i}_enable_power && configured_i)""")
                            print(f"""    );\n""")

                            module, instance = projects[1]
                    
                            print(f"""    (* keep *) {module} {instance} (
            .clk        (tt_project_{i}_clk),
            .rst_n      (tt_project_{i}_rst_n),
            .ena        (tt_project_{i}_ena),
            .ui_in      (tt_project_{i}_ui_in),
            .uio_in     (tt_project_{i}_uio_in),
            .uo_out     (tt_project_{i}_1_uo_out),
            .uio_out    (tt_project_{i}_1_uio_out),
            .uio_oe     (tt_project_{i}_1_uio_oe)""")
                            print(f"""    );\n""")

                            print(f"""    (* keep *) {pg_lv} {instance}_pg_lv (
            `ifdef USE_POWER_PINS
            .VPWR  (VPWR),
            .GND   (VGND),
            .GPWR  (),
            `endif
            .CTRL (tt_project_{i}_enable_power && configured_i)""")
                            print(f"""    );\n""")
                            
                            print(f"""    (* keep *) {pg_hv} {instance}_pg_hv (
            `ifdef USE_POWER_PINS
            .VAPWR (VAPWR),
            .VDPWR (VPWR),
            .GND   (VGND),
            .GPWR  (),
            `endif
            .CTRL (tt_project_{i}_enable_power && configured_i)""")
                            print(f"""    );\n""")

                if "sram" in projects[0][1]:

                    module, instance = projects[0]

                    print(f"""    // SRAM {i} instance

    (* keep *) {module} {instance} (
        .A_CLK      (fabric_sram_{i}_clk_o),
        .A_MEN      (fabric_sram_{i}_men_o),
        .A_WEN      (fabric_sram_{i}_wen_o),
        .A_REN      (fabric_sram_{i}_ren_o),
        .A_ADDR     (fabric_sram_{i}_addr_o),
        .A_DIN      (fabric_sram_{i}_din_o),
        .A_DLY      (fabric_sram_{i}_tie_high_o),
        .A_DOUT     (fabric_sram_{i}_dout_i),
        .A_BM       (fabric_sram_{i}_bm_o),

        .A_BIST_EN      (fabric_sram_{i}_tie_low_o),
        .A_BIST_CLK     (fabric_sram_{i}_tie_low_o),
        .A_BIST_MEN     (fabric_sram_{i}_tie_low_o),
        .A_BIST_WEN     (fabric_sram_{i}_tie_low_o),
        .A_BIST_REN     (fabric_sram_{i}_tie_low_o),
        .A_BIST_ADDR    ({{9{{fabric_sram_{i}_tie_low_o}}}}),
        .A_BIST_DIN     ({{32{{fabric_sram_{i}_tie_low_o}}}}),
        .A_BIST_BM      ({{32{{fabric_sram_{i}_tie_low_o}}}})
    );

    """)

            print("\nendmodule")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
                description="Flow to implement the HeiChips Chip.",
                epilog="Copyright © 2026, FABulous Contributors")

    parser.add_argument('--gui', choices=["openroad", "klayout"])
    parser.add_argument('--nodrc', action="store_true")
    
    args = parser.parse_args()
    
    pdk = os.getenv("PDK")
    pdk_root = os.getenv("PDK_ROOT")
    scl = os.getenv("SCL")
    
    if pdk is None:
        raise FlowError(f"Please define PDK") from None
    
    last_run = False
    if args.gui:
        last_run = True

    # Implement the tile
    main(gui=args.gui, nodrc=args.nodrc, pdk=pdk, pdk_root=pdk_root, scl=scl, last_run=last_run)

