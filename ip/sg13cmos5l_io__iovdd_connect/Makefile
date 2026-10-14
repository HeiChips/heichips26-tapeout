PDK_ROOT ?= ~/.ciel
PDK ?= ihp-sg13cmos5l
TOP ?= sg13cmos5l_io__iovdd_connect

lef: ## Export LEF from the TOP cell layout using Magic
	printf '%s\n' \
		'gds read gds/$(TOP).gds' \
		'load $(TOP)' \
		'lef write lef/$(TOP).lef -hide -pinonly' | \
		magic -dnull -noconsole \
		-rcfile $(PDK_ROOT)/$(PDK)/libs.tech/magic/ihp-sg13cmos5l.magicrc
.PHONY: lef

