MAKEFILE_DIR := $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

RUN_TAG = $(shell ls librelane/runs/ | tail -n 1)
TOP = heichips26_top

PDK_ROOT ?= $(MAKEFILE_DIR)/IHP-Open-PDK
PDK ?= ihp-sg13cmos5l

PDK_REPO_IHP ?= https://github.com/IHP-GmbH/IHP-Open-PDK
PDK_COMMIT_IHP ?= 22f2a25f1734796de3debbbf29cf697cbbc54081

PDK_REPO ?= https://github.com/IHP-GmbH/ihp-sg13cmos5l
PDK_COMMIT ?= e8a87d708b8977e7c07684b033658a0f80af59a0
#PDK_BRANCH ?= heichips25

SCL ?= sg13cmos5l_stdcell

.DEFAULT_GOAL := help

$(PDK_ROOT)/$(PDK):
	#ciel enable $(PDK_COMMIT) --pdk-root $(PDK_ROOT) --pdk-family $(PDK)
	mkdir -p $(PDK_ROOT)
	#git clone $(PDK_REPO) --recurse-submodules --depth=1 --single-branch -b $(PDK_BRANCH) $(PDK_ROOT)
	git clone $(PDK_REPO_IHP) --recurse-submodules --depth=1 --revision $(PDK_COMMIT_IHP) $(PDK_ROOT)
	git clone $(PDK_REPO) --recurse-submodules --depth=1 --revision $(PDK_COMMIT) $(PDK_ROOT)/$(PDK)

# Get the fabric names
FABRICS :=  $(patsubst fabrics/%,%,$(wildcard fabrics/*)) 

FABRICS_OPENROAD := $(addsuffix -openroad,$(FABRICS))
FABRICS_KLAYOUT := $(addsuffix -klayout,$(FABRICS))
FABRICS_COPY := $(addsuffix -copy,$(FABRICS))

all: $(FABRICS)
.PHONY: all

$(FABRICS):
	librelane --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk fabrics/$@/config.yaml --save-views-to fabrics/$@/macro/${PDK}/
.PHONY: $(FABRICS)

$(FABRICS_OPENROAD):
	librelane --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk fabrics/$(subst -openroad,,$@)/config.yaml --last-run --flow OpenInOpenROAD
.PHONY: $(FABRICS_OPENROAD)

$(FABRICS_KLAYOUT):
	librelane --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk fabrics/$(subst -klayout,,$@)/config.yaml --last-run --flow OpenInKLayout
.PHONY: $(FABRICS_KLAYOUT)

$(FABRICS_COPY):
	# Copy fabric database
	mkdir -p user_designs/fabrics/$(subst -copy,,$@)/macro/${PDK}/
	cp -R fabrics/$(subst -copy,,$@)/macro/${PDK}/fabulous/ user_designs/fabrics/$(subst -copy,,$@)/macro/${PDK}/
	cp fabrics/$(subst -copy,,$@)/constraints.pcf user_designs/fabrics/$(subst -copy,,$@)/constraints.pcf
.PHONY: $(FABRICS_COPY)

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
.PHONY: help

clone-pdk: $(PDK_ROOT)/$(PDK) ## Clone the IHP-Open-PDK repository
.PHONY: clone-pdk

all: librelane ## Build the project (runs LibreLane)
.PHONY: all

templates: $(PDK_ROOT)/$(PDK) ## Run LibreLane
	cd ip/heichips26_template/; PDK=${PDK} PDK_ROOT=${PDK_ROOT} SCL=${SCL} python3 build.py
.PHONY: templates

example-small: $(PDK_ROOT)/$(PDK) ## Run LibreLane
	cd ip/user_projects/heichips26_example_small/; librelane config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --scl ${SCL} --save-views-to macro/
.PHONY: example-small

example-large: $(PDK_ROOT)/$(PDK) ## Run LibreLane
	cd ip/user_projects/heichips26_example_large/; librelane config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --scl ${SCL} --save-views-to macro/
.PHONY: example-large

example-tiny: $(PDK_ROOT)/$(PDK) ## Run LibreLane
	cd ip/user_projects/heichips26_example_tiny/; librelane config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --scl ${SCL} --save-views-to macro/
.PHONY: example-tiny

examples: example-small example-large example-tiny
.PHONY: examples

logos: $(PDK_ROOT)/$(PDK) ## Run LibreLane
	cd ip/logo_fabulous/; PDK=${PDK} PDK_ROOT=${PDK_ROOT} make all
	cd ip/logo_heichips/; PDK=${PDK} PDK_ROOT=${PDK_ROOT} make all
	cd ip/logo_credits/; PDK=${PDK} PDK_ROOT=${PDK_ROOT} make all
.PHONY: logos

librelane: $(PDK_ROOT)/$(PDK) ## Run LibreLane
	librelane librelane/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --scl ${SCL} --save-views-to final/
.PHONY: librelane

librelane-nodrc: $(PDK_ROOT)/$(PDK) ## Run LibreLane without DRC checks
	librelane librelane/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --save-views-to final/ --skip KLayout.DRC --skip Magic.DRC --skip KLayout.Antenna --skip KLayout.Density
.PHONY: librelane-nodrc

librelane-onlyfill: $(PDK_ROOT)/$(PDK) ## Run LibreLane onyl for filler generation and density checks
	RUN=$$(ls librelane/runs/ | tail -n 1) && librelane librelane/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --last-run --with-initial-state librelane/runs/$$RUN/62-magic-filler/state_in.json --from Magic.Filler --to KLayout.Density
.PHONY: librelane-onlyfill

librelane-magicdrc: $(PDK_ROOT)/$(PDK) ## Run LibreLane with only Magic DRC checks
	librelane librelane/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --save-views-to final/ --skip KLayout.DRC
.PHONY: librelane-magicdrc

librelane-klayoutdrc: $(PDK_ROOT)/$(PDK) ## Run LibreLane with only KLayout DRC checks
	librelane librelane/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --save-views-to final/ --skip Magic.DRC
.PHONY: librelane-nodrc

librelane-openroad: $(PDK_ROOT)/$(PDK) ## Open the last LibreLane run in OpenROAD GUI
	librelane librelane/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --last-run --flow OpenInOpenROAD
.PHONY: librelane-openroad

librelane-klayout: $(PDK_ROOT)/$(PDK) ## Open the last LibreLane run in KLayout
	librelane librelane/config.yaml --pdk ${PDK} --pdk-root ${PDK_ROOT} --manual-pdk --last-run --flow OpenInKLayout
.PHONY: librelane-klayout

sim-fabric: ## Runfabric  RTL simulation with cocotb
	cd tb/; PDK_ROOT=${PDK_ROOT} PDK=${PDK} SCL=${SCL} python3 fabric_tb.py
	! grep failure tb/sim_build/results.xml
.PHONY: sim-fabric

sim-fabric-emulation: ## Runfabric  RTL simulation with cocotb (emulation)
	cd tb/; EMULATION=counter PDK_ROOT=${PDK_ROOT} PDK=${PDK} SCL=${SCL} python3 fabric_tb.py
	! grep failure tb/sim_build/results.xml
.PHONY: sim-fabric-emulation

sim-fabric-gl: ## Runfabric  RTL simulation with cocotb
	cd tb/; GL=1 PDK_ROOT=${PDK_ROOT} PDK=${PDK} SCL=${SCL} python3 fabric_tb.py
	! grep failure tb/sim_build/results.xml
.PHONY: sim-fabric-gl

sim-top: ## Run RTL simulation with cocotb
	cd tb/; PDK_ROOT=${PDK_ROOT} PDK=${PDK} SCL=${SCL} python3 top_tb.py
	! grep failure tb/sim_build/results.xml
.PHONY: sim-top

sim-top-emulation: ## Run RTL simulation with cocotb (emulation)
	cd tb/; EMULATION=counter PDK_ROOT=${PDK_ROOT} PDK=${PDK} SCL=${SCL} python3 top_tb.py
	! grep failure tb/sim_build/results.xml
.PHONY: sim-top-emulation

sim-top-gl: $(PDK_ROOT)/$(PDK) ## Run gate-level simulation with cocotb
	cd tb/; GL=1 PDK_ROOT=${PDK_ROOT} PDK=${PDK} SCL=${SCL} python3 top_tb.py
	! grep failure tb/sim_build/results.xml
.PHONY: sim-top-gl

sim-fabric-view: ## View simulation waveforms in GTKWave
	gtkwave tb/sim_build/classic_fabric_heichips25.fst
.PHONY: sim-fabric-view

sim-top-view: ## View simulation waveforms in GTKWave
	gtkwave tb/sim_build/${TOP}_tb.fst
.PHONY: sim-top-view

resize-image:
	magick final/render/${TOP}.png -resize 25% final/render/${TOP}_small.png
.PHONY: resize-image

precheck:
	PDK_ROOT=${PDK_ROOT} PDK=${PDK} python3 ${PDK_ROOT}/${PDK}/libs.tech/klayout/tech/drc/run_drc.py \
	--precheck_drc --mp=$$(nproc) --no_offgrid --density_thr=$$(nproc) \
	--no_angle --disable_extra_rules --no_recommended --path=final/gds/${TOP}.gds
.PHONY: precheck
