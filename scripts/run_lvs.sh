#!/bin/sh
#
# Run LVS on the chipalooza top level (sg13cmos5l_ocd_chipalooza)
#
export PROJECT=${PROJECT:-heichips26_top}

export PDK_ROOT=${PDK_ROOT:-../IHP-Open-PDK}
export PDK=${PDK:-ihp-sg13cmos5l}

export NETGEN_COLUMNS=75

cat > netgen.tcl << EOF
# Tcl script for project ${PROJECT} LVS

set circuit1 [readnet spice ${PROJECT}.spice]

# Read in libraries first, followed by all the verilog modules.
set circuit2 [readnet spice ${PDK_ROOT}/${PDK}/libs.ref/sg13cmos5l_stdcell/spice/sg13cmos5l_stdcell.spice]

# Issues in foundry I/O netlist require custom version.
readnet spice sg13cmos5l_io.spice \$circuit2
# readnet spice ${PDK_ROOT}/${PDK}/libs.ref/sg13cmos5l_io/spice/sg13cmos5l_io.spice \$circuit2

# NOTE: SRAM read from CDL; this has incorrect devices but the layout
# SRAM has been replaced with an abstract view and so the contents
# will not be compared.
readnet spice ${PDK_ROOT}/${PDK}/libs.ref/sg13cmos5l_sram/cdl/RM_IHPSG13_1P_1024x32_c2_bm_bist.cdl \$circuit2

# Here also the layout has been replaced with an abstract view, read in for the pins
readnet spice ../fabrics/classic_fabric_heichips26/macro/ihp-sg13cmos5l/spice/classic_fabric_heichips26.spice \$circuit2

readnet verilog ../final/pnl/${PROJECT}.pnl.v \$circuit2

lvs "\$circuit1 ${PROJECT}" "\$circuit2 ${PROJECT}" \
${PDK_ROOT}/${PDK}/libs.tech/netgen/${PDK}_setup.tcl \
comp_${PROJECT}.out
EOF

netgen -batch source netgen.tcl
rm netgen.tcl
echo "Done!"
exit 0

