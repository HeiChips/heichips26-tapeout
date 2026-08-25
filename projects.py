import os
import sys
import glob
import yaml
import pathlib

keys = ["project-name", "top-cell", "team-members", "slot-size", "analog-pins", "short-description", "long-description", "gds-path", "lef-path"]

for config_path in glob.glob("ip/user_projects/*/submission.yaml"):
    print(f"Reading: {config_path}")
    
    with open(config_path) as ifile:
        config = yaml.safe_load(ifile)
    
        for key in keys:
            if not key in config:
                err(f"Config is missing a key ({key})")
                sys.exit(1)
    
            print(f"{key}: {config[key]}")
        
        gds = list(pathlib.Path(config_path).parent.glob(config["gds-path"]))
        if len(gds) > 1:
            print(f"'gds-path' can only refer to a single gds. ({gds})")
            sys.exit(1)
        input_layout = gds[0]
        
        lef = list(pathlib.Path(config_path).parent.glob(config["lef-path"]))
        if len(lef) > 1:
            print(f"'lef-path' can only refer to a single lef. ({lef})")
            sys.exit(1)
        input_lef = lef[0]
        
        header = list(pathlib.Path(config_path).parent.glob(config["header-path"]))
        if len(header) > 1:
            print(f"'header-path' can only refer to a single header. ({header})")
            sys.exit(1)
        input_header = header[0]
        
        print(input_layout)
        print(input_lef)
        print(input_header)
        
        print(f"""  {config['top-cell']}:
    gds:
      - dir::../{input_layout}
    lef:
      - dir::../{input_lef}
    vh:
      - dir::../{input_header}
    instances:""")
    
        print(f"| {config['project-name']} | {config['slot-size']} |               | {config['short-description']} | [Link]() |")
