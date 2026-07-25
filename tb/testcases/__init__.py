# SPDX-FileCopyrightText: © 2026 FABulous Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from .common import tile_library

if tile_library == "classic":

    from .classic.all_ones import test_all_ones
    from .classic.all_zeros import test_all_zeros
    from .classic.passthrough import test_passthrough
    from .classic.addition import test_addition
    from .classic.counter import test_counter
    
    # makes issues in GL simulation
    if not os.getenv("GL", None):
        from .classic.multiplication import test_multiplication

    #from .classic.macc_8x8_20 import test_macc_8x8_20
    #from .classic.ram_32x4_2r_1w import test_ram_32x4_2r_1w
    from .classic.sys_reset import test_sys_reset
    #from .classic.register_file import test_register_file # why does it need to go last?
    #from .classic.ihp_sram_1024x32_1rw import test_ihp_sram_1024x32_1rw # needs SRAM model
    
elif tile_library == "tiny":

    from .tiny.all_ones import test_all_ones
    from .tiny.all_zeros import test_all_zeros
    from .tiny.counter import test_counter
    from .tiny.passthrough import test_passthrough
    from .tiny.addition import test_addition
    from .tiny.counter import test_counter
    from .tiny.multiplication import test_multiplication
    from .tiny.sys_reset import test_sys_reset

else:
    print(f"No test cases for tile library {tile_library}")
    sys.exit(0)
