import io
import os
import sys
import yaml
import pathlib
import textwrap
from glob import glob
from decimal import Decimal
from typing import Callable, List, Literal, Mapping, Tuple, Union, Optional, Dict, Any
from librelane.steps import Step, OdbpyStep, OpenROADStep
from librelane.steps.klayout import KLayoutStep
from librelane.steps.step import (
    ViewsUpdate,
    MetricsUpdate,
)
from librelane.steps.common_variables import io_layer_variables
from librelane.flows import Flow, FlowError
from librelane.state import DesignFormat, State
from librelane.common import Path, aggregate_metrics
from librelane.config import Variable
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
from librelane.steps import (
    Yosys,
    OpenROAD,
    Magic,
    KLayout,
    Odb,
    Netgen,
    Checker,
    Verilator,
    Misc,
)

DesignFormat(
    "oas",
    "oas",
    "OASIS Stream",
    alts=["OASIS"],
    multiple=True,
).register()

@Step.factory.register()
class CustomPDN(OdbpyStep):
    """
    Create a custom PDN.
    """

    id = "Odb.CustomPDN"
    name = "Custom PDN"
    long_name = "Create a custom Power Distribution Network"
    
    config_vars = Variable(
            "HEICHIPS_SLOTS",
            Dict[str, List[Tuple[str,str]]|None],
            """
            The HeiChips slot assignment.
            """,
        ),

    def get_script_path(self):
        return os.path.join(os.path.dirname(__file__), "scripts", "custom_pdn.py")

    def get_command(self) -> List[str]:
        args = []
        
        for coord, entry in self.config["HEICHIPS_SLOTS"].items():
            if entry:
                for module, instance in entry:
                    print(f"{module} {instance}")
                    args += ["--instance", instance]

        return super().get_command() + args

@Step.factory.register()
class ConnectIORing(OdbpyStep):
    """
    Connect PDN to IO ring.
    """

    id = "Odb.ConnectIORing"
    name = "Connect to IO Ring"
    long_name = "Connect the PDN to the IO ring for better connectivity"

    def get_script_path(self):
        return os.path.join(os.path.dirname(__file__), "scripts", "connect_ioring.py")

@Step.factory.register()
class ConnectIOVDD(OdbpyStep):
    """
    Connect IOVDD to core ring.
    """

    id = "Odb.ConnectIOVDD"
    name = "Connect IOVDD"
    long_name = "Connect IOVDD to core ring"

    def get_script_path(self):
        return os.path.join(os.path.dirname(__file__), "scripts", "connect_iovdd.py")

def get_psm_error_count(rpt: io.TextIOWrapper) -> int:
    sio = io.StringIO()

    # Turn almost-YAML into YAML
    VIO_TYPE_PFX = "violation type: "
    for line in rpt:
        if line.startswith(VIO_TYPE_PFX):
            vio_type = line[len(VIO_TYPE_PFX) :].strip()
            sio.write(f"- type: {vio_type}\n")
        elif "bbox = " in line:
            sio.write(f"    {textwrap.dedent(line.replace('bbox = ', '- bbox ='))}")
        else:
            sio.write(f"  {textwrap.dedent(line)}")

    sio.seek(0)
    violations = yaml.load(sio, Loader=yaml.SafeLoader) or []
    return sum(len(violation["srcs"]) for violation in violations)

@Step.factory.register()
class CheckPowerGrid(OpenROADStep):
    """
    Checks the power grid.
    """

    id = "OpenROAD.CheckPowerGrid"
    name = "Check Power Grid"
    long_name = "Check Power Grid"

    def get_script_path(self):
        return os.path.join(os.path.dirname(__file__), "scripts", "check_power_grid.tcl")

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        kwargs, env = self.extract_env(kwargs)
        views_updates, metrics_updates = super().run(state_in, env=env, **kwargs)

        alerts = self.alerts or []
        error_reports = glob(os.path.join(self.step_dir, "*-grid-errors.rpt"))
        for report in error_reports:
            net = os.path.basename(report).split("-", maxsplit=1)[0]
            no_terminals = any(
                alert.code == "PSM-0025" and alert.message.startswith(net)
                for alert in alerts
            )
            if no_terminals:
                count = 1
            else:
                count = get_psm_error_count(open(report, encoding="utf8"))
            metrics_updates[f"design__power_grid_violation__count__net:{net}"] = count

        metric_updates_with_aggregates = aggregate_metrics(
            metrics_updates,
            {"design__power_grid_violation__count": (0, lambda x: sum(x))},
        )

        return views_updates, metric_updates_with_aggregates

@Step.factory.register()
class ConvertOASIS(KLayoutStep):
    """
    Convert GDS to OASIS.
    """

    id = "KLayout.ConvertOASIS"
    name = "Convert OASIS"
    long_name = "Convert GDS to OASIS using KLayout"

    inputs = [
        DesignFormat.GDS,
    ]
    outputs = [
        DesignFormat.OASIS
    ]

    def run(self, state_in: State, **kwargs) -> Tuple[ViewsUpdate, MetricsUpdate]:
        views_updates: ViewsUpdate = {}

        gds_in = state_in[DesignFormat.GDS]
        oas_out = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.OASIS.extension}",
        )
        
        script = os.path.join(os.path.dirname(__file__), "scripts", "convert_oasis.py")

        self.run_pya_script(
            [
                sys.executable,
                script,
                gds_in,
                oas_out,
            ]
        )

        views_updates[DesignFormat.OASIS] = Path(oas_out)

        return views_updates, {}
