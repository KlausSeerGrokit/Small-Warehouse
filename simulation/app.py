# app.py (migrated for Isaac Sim 4.5.0)
import os
import asyncio
import argparse
import yaml
import omni.kit.app

from isaacsim.simulation_app import SimulationApp

# config folder
BASE_DIR = os.path.dirname(__file__)
CFG_DIR = os.path.join(BASE_DIR, "config")
available = [f for f in os.listdir(CFG_DIR) if f.endswith((".yml", ".yaml"))]

parser = argparse.ArgumentParser()
parser.add_argument("--config", "-c", choices=available, default="sim_config.yml")
args = parser.parse_args()

config_path = os.path.join(CFG_DIR, args.config)
with open(config_path, "r") as f:
    cfg = yaml.safe_load(f)

headless = cfg.get("headless", False)
low_res = cfg.get("low_res", False)

win_w, win_h = 1920, 1080
buf_w, buf_h = 1440, 900
if low_res:
    win_w //= 2
    win_h //= 2
    buf_w //= 2
    buf_h //= 2

simulation_app = SimulationApp(
    {
        "headless": headless,
        "window_width": win_w,
        "window_height": win_h,
        "width": buf_w,
        "height": buf_h,
    }
)

# Delay extension-related imports until after app starts
from isaacsim.core.utils.extensions import enable_extension
from isaacsim.core.utils.viewports import set_camera_view
from isaacsim.core.utils.stage import create_new_stage

# Enable necessary extensions
for ext in [
    "omni.kit.scripting",
    # "omni.isaac.conveyor",
    "omni.anim.graph.core",
    "omni.anim.graph.ui",
    "omni.anim.graph.schema",
    "omni.anim.people",
    # "omni.isaac.examples",
    "omni.warehouse_creator",
]:
    enable_extension(ext)

simulation_app._app.update()

from warehouse.warehouse import WarehouseSim

create_new_stage()
warehouse = WarehouseSim(cfg.get("sim_actors", {}))


async def setup():
    warehouse.setup_scene()

    await warehouse._world.reset_async()
    await warehouse._world.pause_async()
    await warehouse.setup_post_load()

    action_registry = omni.kit.actions.core.get_action_registry()
    # switches to camera lighting
    action = action_registry.get_action(
        "omni.kit.viewport.menubar.lighting", "set_lighting_mode_camera"
    )
    action.execute()

    warehouse.start_actors()


asyncio.ensure_future(setup())

while simulation_app.is_running():
    warehouse._world.step(render=True)

simulation_app.close()
