# SPDX-FileCopyrightText: © 2026 FABulous Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, Timer
from cocotb.types import LogicArray, Logic

from ..common import zero_bitstream, upload_bitstream, PCF, fabric, tile_library

testname = Path(__file__).stem
proj_path = Path(__file__).resolve().parent

@cocotb.test()
async def test_ihp_sram_1024x32_1rw(dut):
    """Load bitstream for ihp_sram_1024x32_1rw"""

    pcf = PCF(dut, proj_path / f"../../../fabrics/{fabric}/constraints.pcf")
    pcf.write_gtkw(f"{testname}.gtkw", ["clk1", "ram_addr", "ram_be", "ram_wen", "ram_men", "ram_ren", "ram_din_byte", "ram_dout_byte"])

    # Reset
    pcf.set("clk1", Logic(0), index=0)
    await Timer(10, unit="ns")

    # Zero all config bits
    await zero_bitstream(dut)
    await Timer(10, unit="ns")

    # Upload the bitstream
    await upload_bitstream(dut, proj_path / f'../../../user_designs/designs/{tile_library}/{testname}/{testname}.bit')
    await Timer(10, unit="ns")
    
    # Start a clock on clk1
    clock1 = pcf.get_raw("clk1", "OUT")
    cocotb.start_soon(Clock(clock1, 10, 'ns').start())
    
    await ClockCycles(clock1, 10)
    
    pcf.set("ram_men", Logic(1), index=0)
    pcf.set("ram_wen", Logic(1), index=0)
    pcf.set("ram_ren", Logic(0), index=0)
    
    # Fill the memory with data
    for i in range(32):
        pcf.set("ram_addr", LogicArray.from_unsigned(i >> 2, len(pcf.get("ram_addr"))))
        pcf.set("ram_be", LogicArray.from_unsigned(i & 0x3, len(pcf.get("ram_be"))))
        pcf.set("ram_din_byte", LogicArray.from_unsigned(i & 0xFF, len(pcf.get("ram_din_byte"))))
        
        await ClockCycles(clock1, 1)

    await ClockCycles(clock1, 10)
    
    pcf.set("ram_men", Logic(1), index=0)
    pcf.set("ram_wen", Logic(0), index=0)
    pcf.set("ram_ren", Logic(1), index=0)
    
    # Read from read port
    for i in range(32):
        pcf.set("ram_addr", LogicArray.from_unsigned(i >> 2, len(pcf.get("ram_addr"))))
        pcf.set("ram_be", LogicArray.from_unsigned(i & 0x3, len(pcf.get("ram_be"))))
        await ClockCycles(clock1, 2)

        assert(pcf.get("ram_dout_byte").to_unsigned() == i & 0xFF)
