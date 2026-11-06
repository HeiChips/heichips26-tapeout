#!/bin/bash
#
# set PROJECT to the chip top level name.  If not set, the top level
# name defaults to sg13cmos5l_ocd_chipalooza

export PROJECT=${PROJECT:-heichips26_top}

export PDK_ROOT=${PDK_ROOT:-../IHP-Open-PDK}
export PDK=${PDK:-ihp-sg13cmos5l}

magic -dnull -noconsole -rcfile $PDK_ROOT/$PDK/libs.tech/magic/${PDK}.magicrc << EOF

# Read the LEFs to be used as abstract views

# SRAM
lef read $PDK_ROOT/$PDK/libs.ref/sg13cmos5l_sram/lef/RM_IHPSG13_1P_1024x32_c2_bm_bist.lef

# Fabric
lef read ../fabrics/classic_fabric_heichips26/macro/ihp-sg13cmos5l/lef/classic_fabric_heichips26.lef

# Bondpads and connect slices
lef read ../ip/bondpad_70x70_novias/lef/bondpad_70x70_novias.lef
lef read ../ip/sg13cmos5l_io__iovdd_connect/lef/sg13cmos5l_io__iovdd_connect.lef

# Logos
lef read ../ip/logo_bmftr/lef/logo_bmftr.lef
lef read ../ip/logo_chipdesigngermany/lef/logo_chipdesigngermany.lef
lef read ../ip/logo_credits/lef/logo_credits.lef
lef read ../ip/logo_fabulous/lef/logo_fabulous.lef
lef read ../ip/logo_heichips/lef/logo_heichips.lef
lef read ../ip/logo_heidelberg/lef/logo_heidelberg.lef
lef read ../ip/logo_nct/lef/logo_nct.lef
lef read ../ip/logo_ziti/lef/logo_ziti.lef

# Marker
lef read ../ip/alignment_mark/lef/alignment_mark.lef

# User Projects
lef read ../ip/user_projects/heichips26-aiaccel/macros/heichips26_event_snn/final/lef/heichips26_event_snn.lef
lef read ../ip/user_projects/heichips26-FAIfplus/macros/heichips26_FAIf/final/lef/heichips26_FAIf.lef
lef read ../ip/user_projects/heichips26-e2spike/macros/heichips26_e2spike/final/lef/heichips26_e2spike.lef
lef read ../ip/user_projects/heichips26-multimode_dll/macros/heichips26_multimode_dll/final/lef/heichips26_multimode_dll.lef
lef read ../ip/user_projects/heichips26-sramcell-test/macros/heichips26_sramcell_test/final/lef/heichips26_sramcell_test.lef
lef read ../ip/user_projects/heichips26_dram_replica/macros/heichips26_dram_replica/final/lef/heichips26_dram_replica.lef
lef read ../ip/user_projects/heichips26-rimax/macros/heichips26_rimax/final/lef/heichips26_RiMaX.lef
lef read ../ip/user_projects/heichips26-heiscore/macros/heichips26_heiscore/final/lef/heichips26_heiscore.lef
lef read ../ip/user_projects/heichips26-minimal-processor/macros/heichips26_minimal_multicore_processor/final/lef/heichips26_minimal_multicore_processor.lef
lef read ../ip/user_projects/heichips26_noise_gen/macros/heichips26_digital_project/final/lef/heichips26_noise_gen.lef
lef read ../ip/user_projects/heichips26-DNA_sequencer/macros/heichips26_dna_sequencer/final/lef/heichips26_dna_sequencer.lef
lef read ../ip/user_projects/heichips26-on-off/macros/heichips26_ook_top/final/lef/heichips26_ook_top.lef
lef read ../ip/user_projects/heichips26-voltage-controlled-resistor/macros/heichips26_vcr/final/lef/heichips26_vcr.lef
lef read ../ip/user_projects/heichips26-daftasic/macros/heichips26_daftASIC/final/lef/heichips26_daftASIC.lef
lef read ../ip/user_projects/heichips26-ballmer-peak-detector/macros/heichips26_digital_project/final/lef/heichips26_ballmer_peak_detector.lef

# Pre-load the SRAM and mark it as abstract.  Ideally the SRAM should be part of
# LVS but currently is failing extraction in magic for an unknown reason (nets
# are split which are obviously not split in the layout).
load RM_IHPSG13_1P_1024x32_c2_bm_bist
property LEFview true

load classic_fabric_heichips26
property LEFview true

load bondpad_70x70_novias
property LEFview true
load sg13cmos5l_io__iovdd_connect
property LEFview true

load logo_bmftr
property LEFview true
load logo_chipdesigngermany
property LEFview true
load logo_credits
property LEFview true
load logo_fabulous
property LEFview true
load logo_heichips
property LEFview true
load logo_heidelberg
property LEFview true
load logo_nct
property LEFview true
load logo_ziti
property LEFview true

load alignment_mark
property LEFview true

# Mark all user projects as abstract
load heichips26_event_snn
property LEFview true
load heichips26_ballmer_peak_detector
property LEFview true
load heichips26_dna_sequencer
property LEFview true
load heichips26_noise_gen
property LEFview true
load heichips26_e2spike
property LEFview true
load heichips26_RiMaX
property LEFview true
load heichips26_dram_replica
property LEFview true
load heichips26_minimal_multicore_processor
property LEFview true
load heichips26_ook_top
property LEFview true
load heichips26_vcr
property LEFview true
load heichips26_FAIf
property LEFview true
load heichips26_daftASIC
property LEFview true
load heichips26_heiscore
property LEFview true
load heichips26_multimode_dll
property LEFview true
load heichips26_sramcell_test
property LEFview true

# Set no duplicates, so the abstract views are not
# overwritten with the actual cells from the GDS
gds noduplicates true

gds read ../final/gds/$PROJECT.gds

# Now read the project top level and extract it
load $PROJECT
select top cell
extract path extfiles
extract no all
extract do unique
extract all
ext2spice lvs
ext2spice -p extfiles -o ${PROJECT}.spice
quit -noprompt
EOF
# rm -r extfiles
exit 0

