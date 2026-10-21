MAKEFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

PDK_ROOT ?= $(MAKEFILE_DIR)/../../IHP-Open-PDK
PDK ?= ihp-sg13cmos5l
TOP ?= logo_ziti

PRBOUNDARY = "189/4"
METAL4 = "50/0"
METAL4_NOFILL = "50/23"
TOPMETAL1_NOFILL = "126/23"

all: logo drc
.PHONY: all

logo:
	python3 script/make_gds.py image/${TOP}.png gds/${TOP}.gds --cellname ${TOP} --invert-alpha --merge --pixel-size 0.21 --height 380 --foreground ${METAL4} --boundary ${PRBOUNDARY} ${METAL4_NOFILL} ${TOPMETAL1_NOFILL} \
	--lib lib/${TOP}.lib \
	--lef lef/${TOP}.lef \
	--vh  vh/${TOP}.vh
.PHONY: logo

drc:
	PDK_ROOT=${PDK_ROOT} PDK=${PDK} klayout -b -zz -r ${PDK_ROOT}/${PDK}/libs.tech/klayout/tech/drc/${PDK}.drc -rd input=gds/${TOP}.gds -rd report=report.lyrdb
.PHONY: drc
