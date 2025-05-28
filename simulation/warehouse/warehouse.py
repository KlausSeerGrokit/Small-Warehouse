import os
import math
import carb
import numpy as np
import omni.appwindow

from isaacsim.robot.manipulators.examples.franka import Franka
from isaacsim.core.api import World
from isaacsim.core.utils.stage import add_reference_to_stage

# from isaacsim.core.debug_draw import DebugDraw

from .franka_actor import create_franka_instance
from .spot_actor import create_spot_instance

from paranet_agent import connector
from paranet_agent.actor import deploy

from .spot_isaac import Spot
from .franka_isaac import FrankaSim

ASSET_PATH = os.environ.get(
    "ASSET_PATH", os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)


class WarehouseSim:
    def __init__(self, sim_actors_cfg: dict) -> None:
        super().__init__()
        self.sim_actors_cfg = sim_actors_cfg

        self._world_settings = {
            "stage_units_in_meters": 1.0,
            "physics_dt": 1.0 / 200.0,
            "rendering_dt": 8.0 / 200.0,
        }

        self._world = World(**self._world_settings)
        self._world.warehouse = self

        self._input_keyboard_mapping = {
            "NUMPAD_8": [0.50, 0.0, 0.0],
            "UP": [0.50, 0.0, 0.0],
            "NUMPAD_4": [0.0, 0.0, 0.50],
            "LEFT": [0.0, 0.0, 0.50],
            "NUMPAD_6": [0.0, 0.0, -0.50],
            "RIGHT": [0.0, 0.0, -0.50],
        }

        self._physics60_steps = 0
        self._physics200_steps = 0

        self.frankas = []
        self.franka_actors = []
        self.spots = []
        self.spot_actors = []

    def setup_scene(self) -> None:
        self._world.scene.add_default_ground_plane(
            z_position=0,
            name="default_ground_plane",
            prim_path="/World/defaultGroundPlane",
            static_friction=0.2,
            dynamic_friction=0.2,
            restitution=0.01,
        )

        usd_file_path = os.path.join(ASSET_PATH, "Warehouse.usd")
        print(f"Adding {usd_file_path} to stage ...")
        add_reference_to_stage(usd_path=usd_file_path, prim_path="/World")

        for arm in self.sim_actors_cfg.get("robot_arm", []):
            name = arm["name"]
            pos = np.array(arm["position"])
            self._world.scene.add(
                Franka(prim_path=f"/World/{name}", name=name, position=pos)
            )

        for spot_cfg in self.sim_actors_cfg.get("robot_quadruped", []):
            name = spot_cfg["name"]
            loc = spot_cfg["position"]
            color = spot_cfg.get("color", "default")
            spot = Spot(f"/World/{name}", loc, color)
            spot.setup_scene()
            self.spots.append(spot)
            self.spot_actors.append(create_spot_instance(name, spot))

    async def setup_post_load(self) -> None:
        for arm in self.sim_actors_cfg.get("robot_arm", []):
            name = arm["name"]
            target_pos = arm.get("target_position", arm["position"])
            franka_obj = self._world.scene.get_object(name)
            franka_sim = FrankaSim(name, franka_obj, self, np.array(target_pos))
            self.frankas.append(franka_sim)
            self.franka_actors.append(create_franka_instance(name, franka_sim, self))

        for spot in self.spots:
            spot.setup_post_load()

        self._appwindow = omni.appwindow.get_default_app_window()
        self._input = carb.input.acquire_input_interface()
        self._keyboard = self._appwindow.get_keyboard()
        self._sub_keyboard = self._input.subscribe_to_keyboard_events(
            self._keyboard, self._sub_keyboard_event
        )

        # self.draw()

        self._physics_ready = False
        self._world.add_physics_callback("sim_step", self.on_physics_step)

    async def setup_post_reset(self) -> None:
        self._physics_ready = False
        for franka in self.frankas:
            franka.post_reset()
        for spot in self.spots:
            spot.setup_post_load()

    def on_physics_step(self, step_size) -> None:
        t60 = math.floor(self._physics200_steps / 200 * 60)
        if t60 == self._physics60_steps:
            for franka in self.frankas:
                franka.physics_step()
            self._physics60_steps += 1

        if self._physics_ready:
            for spot in self.spots:
                spot.on_physics_step(step_size, np.zeros((3,)))
            self._physics200_steps += 1
        else:
            print("Physics Start")
            self._physics_ready = True

    def _sub_keyboard_event(self, event, *args, **kwargs) -> bool:
        return True

    # def draw(self):
    #     draw = DebugDraw()
    #     draw.clear_lines()

    def start_actors(self):
        connector.start()

        for actor in self.spot_actors:
            actor.register()

        for actor in self.franka_actors:
            actor.register()

        deploy("isaac", restart=True)
        print("ACTORS started")

    def stop_actors(self):
        connector.stop()
        print("ACTORS stopped")

    def world_cleanup(self):
        if self._world.physics_callback_exists("sim_step"):
            self._world.remove_physics_callback("sim_step")
