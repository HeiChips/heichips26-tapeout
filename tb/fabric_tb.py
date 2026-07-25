# SPDX-FileCopyrightText: © 2025 Leo Moser <leomoser99@gmail.com>
# SPDX-License-Identifier: Apache-2.0

import os
import re
import math
import random
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer, Edge, RisingEdge, FallingEdge
from cocotb.regression import TestFactory
from cocotb_tools.runner import get_runner
from cocotb.types import LogicArray, Logic

proj_path = Path(__file__).resolve().parent
fabric = os.getenv("FABRIC", "classic_fabric_heichips26")

if __name__ == "__main__":

    sim = os.getenv("SIM", "icarus")
    pdk_root = os.getenv("PDK_ROOT", Path("~/.ciel").expanduser())
    pdk = os.getenv("PDK", "ihp-sg13g2")
    scl = os.getenv("SCL", "sg13g2_stdcell")
    gl = os.getenv("GL", None)
    emulation = os.getenv("EMULATION", False)
    tile_library = os.getenv("TILE_LIBRARY", "classic")
    
    if emulation and gl:
        print("Error: EMULATION and GL can't be set at the same time.")
        sys.exit(1)
    
    tiles_path = Path(proj_path / ".." / "ip" / "fabulous-tiles")
    primitives_path = Path(tiles_path) / "primitives"
    tile_library_path = Path(tiles_path) / "tiles" / tile_library

    sources = []
    defines = {}
    test_filter = None
    
    # RTL
    if not gl:
        if emulation:
            sources.append(proj_path / f'../user_designs/designs/{tile_library}/{emulation}/{emulation}.vh')
            defines = {"EMULATION": True}
            test_filter = "test_" + emulation

        primitives_files = list(primitives_path.glob('**/fabulous/*.v'))
        tile_files = list(tile_library_path.glob(f'**/macro/{pdk}/fabulous/*.v'))

        #print(f"Primitive sources: {primitives_files}")
        #print(f"Tile sources: {tile_files}")
        
        sources.extend(primitives_files)
        sources.extend(tile_files)
        
        # Add models pack
        sources.append(tiles_path / "models_pack.v")

        # Add custom cells
        sources.append(tiles_path / "custom.v")

        # Add fabric netlist
        sources.append(proj_path / f'../fabrics/{fabric}/macro/{pdk}/fabulous/{fabric}.v')

    # Gate-level
    else:
        # SCL models
        sources.append(Path(pdk_root) / pdk / "libs.ref" / scl / "verilog" / f"{scl}.v")
        sources.append(Path(pdk_root) / pdk / "libs.ref" / scl / "verilog" / f"sg13cmos5l_udp.v")
        
        # Tile GL netlists
        tile_files = list(tile_library_path.glob(f'**/macro/{pdk}/nl/*.nl.v'))
        #print(f"Tile sources: {tile_files}")
        sources.extend(tile_files)
        
        # Fabric GL netlist
        sources.append(proj_path / f'../fabrics/{fabric}/macro/{pdk}/nl/{fabric}.nl.v')

    hdl_toplevel = fabric

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel=hdl_toplevel,
        defines=defines,
        always=True,
        clean=True,
        timescale=("1ns", "1ps"),
        waves=True,
    )

    runner.test(
        hdl_toplevel=hdl_toplevel,
        test_module="testcases",
        plusargs=['-fst'],
        waves=True,
        test_filter=test_filter,
    )
