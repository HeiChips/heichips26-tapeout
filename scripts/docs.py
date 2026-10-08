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

def main():

    common_config_path = os.path.join(__dir__, "../librelane/config.yaml")
    config = yaml.safe_load(open(common_config_path))
    
    slot_map = config["HEICHIPS_SLOTS"]
    
    # Read user projects submission.yaml
    user_projects_metadata = {}
    
    keys = ["project-name", "top-cell", "team-members", "slot-size", "analog-pins", "short-description", "long-description", "gds-path", "lef-path", "header-path"]
    for config_path in glob.glob(os.path.join(__dir__, "../ip/user_projects/*/submission.yaml")):
        print(f"Reading: {config_path}")
        
        with open(config_path) as ifile:
            project_config = yaml.safe_load(ifile)
            
            # Collect metadate
            user_projects_metadata[project_config["project-name"]] = {}
            user_projects_metadata[project_config["project-name"]]["repo-name"] = config_path.split("user_projects/")[1].split("/")[0]
        
            for key in keys:
                if not key in project_config:
                    err(f"Config is missing a key ({key})")
                    sys.exit(1)
        
                print(f"{key}: {project_config[key]}")
            
            gds = list(Path(config_path).parent.glob(project_config["gds-path"]))
            if len(gds) > 1:
                print(f"'gds-path' can only refer to a single gds. ({gds})")
                sys.exit(1)
            project_config["gds-path"] = gds[0]
            
            # Render GDS image
            import klayout.lay as lay
            import klayout.db as db
            
            lv = lay.LayoutView()

            lv.set_config("grid-visible", "false")
            lv.set_config("grid-show-ruler", "false")
            lv.set_config("text-visible", "false")

            lv.load_layout(project_config["gds-path"])
            lv.max_hier()
            
            # Get aspect ratio
            top_cell = lv.active_cellview().layout().top_cell()
            top_bbox = top_cell.dbbox()
            aspect_ratio = top_bbox.width() / top_bbox.height()
            
            resolution = 1024
            oversampling = 8
            
            width = resolution
            height = int(width / aspect_ratio)
            
            lv.load_layer_props(os.path.join(__dir__, "../librelane/sg13cmos5l_render.lyp"))
            
            lv.set_config("background-color", "#FFFFFF")
            lv.save_image_with_options(
                os.path.join(__dir__, f"../img/user_projects/{project_config['top-cell']}.png"),
                width,
                height,
                oversampling=oversampling,
            )
            
            lef = list(Path(config_path).parent.glob(project_config["lef-path"]))
            if len(lef) > 1:
                print(f"'lef-path' can only refer to a single lef. ({lef})")
                sys.exit(1)
            project_config["lef-path"] = lef[0]
            
            header = list(Path(config_path).parent.glob(project_config["header-path"]))
            if len(header) > 1:
                print(f"'header-path' can only refer to a single header. ({header})")
                sys.exit(1)
            project_config["header-path"] = header[0]
            
            # Add remaining keys
            for key in keys:
                user_projects_metadata[project_config["project-name"]][key] = project_config[key]
    
    update_readme(os.path.join(__dir__, "../README.md"), user_projects_metadata, slot_map)

def update_readme(readme, user_projects_metadata, slot_map):

    content = []

    with open(readme, "r") as ifile:
        while line := ifile.readline():
            content.append(line)
    
    print(content)
    
    with open(readme, "w") as ofile:
    
        content_iter = iter(content)
    
        for line in content_iter:
        
            if "<!--- project_table_start -->" in line:
                ofile.write(line)
                ofile.write("\n")
                ofile.write("| Project       | Size          | Location      | Description  | Link |\n")
                ofile.write("|---------------|---------------|---------------|--------------|------|\n")
                
                for project_name, entries in user_projects_metadata.items():
                
                    project_coords = ""
                
                    for i, (coords, project_tuple) in enumerate(slot_map.items()):
    
                        if project_tuple is None:
                            continue
                    
                        module, instance = project_tuple[0]
                        
                        if len(project_tuple) > 1:
                        
                            module_2, instance_2 = project_tuple[1]
                            
                            if module == entries['top-cell']:
                                project_coords = coords + "/0"
                            
                            if module_2 == entries['top-cell']:
                                project_coords = coords + "/1"
                            
                        else:
                            if module == entries['top-cell']:
                                project_coords = coords
                
                    ofile.write(f"| {project_name} | {entries['slot-size']} | {project_coords} | {entries['short-description'].replace('\n', '')} | [Repo](https://github.com/HeiChips/{entries['repo-name']}) |\n")
                
                while line:= next(content_iter):
                    if "<!--- project_table_end -->" in line:
                        ofile.write("\n")
                        break

            if "<!--- project_list_start -->" in line:
                ofile.write(line)
                ofile.write("\n")
                
                for project_name, entries in user_projects_metadata.items():
                
                    if not "uses-vapwr" in entries:
                        entries["uses-vapwr"] = False
                
                    team = "\n".join([f"- {person}" for person in entries['team-members']])

                    ofile.write(f"### {project_name}\n\n")

                    ofile.write(f"{entries['short-description']}\n\n")

                    ofile.write(f"""<p align="center">
  <a href="img/user_projects/{entries['top-cell']}.png">
    <img src="img/user_projects/{entries['top-cell']}.png" alt="Render of {entries['top-cell']}" width=40%>
  </a>
</p>\n\n""")

                    ofile.write(f"""Top cell: `{entries['top-cell']}`
Slot size: {entries['slot-size']}
Analog pins: {entries['analog-pins']}
Uses VAPRW: {entries['uses-vapwr']}

Team members:\n
{team}\n\n""")

                    ofile.write(f"Long description:\n\n")
                    
                    for long_line in entries['long-description'].split("\n"):
                        if len(long_line) > 0 and long_line[0] == '#':
                            ofile.write("###")
                    
                        ofile.write(f"{long_line}\n")
                    
                    ofile.write("\n")
                
                while line:= next(content_iter):
                    if "<!--- project_list_end -->" in line:
                        ofile.write("\n")
                        break

            ofile.write(line)

if __name__ == "__main__":
    main()

