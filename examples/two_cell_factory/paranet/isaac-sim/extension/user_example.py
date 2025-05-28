import os
import math
import carb
import numpy as np
import omni
import omni.appwindow

from omni.isaac.examples.base_sample import BaseSample
from omni.isaac.core.utils import stage as stage_utils
from omni.isaac.core.utils.prims import is_prim_path_valid, get_prim_attribute_value

from omni.isaac.examples.user_examples.workcell import Workcell
from omni.isaac.examples.user_examples.actors import start_actors, stop_actors

CES_ASSET_PATH = os.environ.get(
    "CES_ASSET_PATH", "/home/devops/code/robot-ces/paranet/isaac-sim"
)


class HumanoidExample(BaseSample):
    def __init__(self) -> None:
        super().__init__()
        self._world_settings["stage_units_in_meters"] = 1.0
        self._world_settings["physics_dt"] = 1.0 / 200.0
        self._world_settings["rendering_dt"] = 8.0 / 200.0

        # Key binding for keyboard controlling H1
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

        self._workcells = []

    # ---------------------------------------------------
    # Before Load
    def setup_scene(self) -> None:
        world = self.get_world()

        world.scene.add_default_ground_plane(
            z_position=0,
            name="default_ground_plane",
            prim_path="/World/defaultGroundPlane",
            static_friction=0.2,
            dynamic_friction=0.2,
            restitution=0.01,
        )

        # Load your main USD scene with the conveyor, table, etc.
        usd_file_path = CES_ASSET_PATH + "/factory.usd"
        print(f"Adding {usd_file_path} to stage ...")
        stage_utils.add_reference_to_stage(usd_path=usd_file_path, prim_path="/World")

        for i in range(10):
            path = "/World/workcell_%02d" % (1 + i,)
            if is_prim_path_valid(path):
                stage = omni.usd.get_context().get_stage()
                prim = stage.GetPrimAtPath(path)
                transform = omni.usd.get_world_transform_matrix(prim)
                translation = transform.ExtractTranslation()
                print(f"Creating {path} at {translation}")
                cell = Workcell(path, offset=np.array(translation))
                self._workcells.append(cell)
            else:
                break

        for cell in self._workcells:
            cell.setup_scene(world)

    async def setup_post_load(self) -> None:
        self._world = self.get_world()

        self._appwindow = omni.appwindow.get_default_app_window()
        self._input = carb.input.acquire_input_interface()
        self._keyboard = self._appwindow.get_keyboard()
        self._sub_keyboard = self._input.subscribe_to_keyboard_events(
            self._keyboard, self._sub_keyboard_event
        )

        self._physics_ready = False
        self._world.add_physics_callback("sim_step", callback_fn=self.on_physics_step)

        for cell in self._workcells:
            cell.setup_post_load(self._world)

        h1s = [cell.h1() for cell in self._workcells]
        arms = [cell.arm() for cell in self._workcells]
        belts = [cell.belt() for cell in self._workcells]
        digits = [cell.digit() for cell in self._workcells]
        start_actors(self._workcells, h1s, arms, belts, digits)

        #await self._world.play_async()

    async def setup_post_reset(self) -> None:
        self._physics_ready = False

        for cell in self._workcells:
            cell.setup_post_reset()

    def on_physics_step(self, step_size) -> None:
        # Franka controller only works at 60 steps/sec
        # H1 controller only works at 200 steps/sec
        # This function is called at 200 steps/sec, and we calculate when to call the Franka
        # controller to get an effective 60 steps/sec

        t60 = math.floor(self._physics200_steps / 200 * 60)
        if t60 == self._physics60_steps:
            for cell in self._workcells:
                cell.physics_60()
            self._physics60_steps += 1

        if self._physics_ready:
            for cell in self._workcells:
                cell.physics_200(step_size)
            self._physics200_steps += 1
        else:
            print("Physics Start")
            self._physics_ready = True

    def _sub_keyboard_event(self, event, *args, **kwargs) -> bool:
        if event.type == carb.input.KeyboardEventType.KEY_PRESS:
            if event.input.name == "NUMPAD_5":
                # self.reset_demo()
                self._digit.get_tote()
            if event.input.name == 'NUMPAD_4':
                self._digit.place_tote('good_table')
            if event.input.name == 'NUMPAD_6':
                self._digit.place_tote('bad_table')
            if event.input.name == 'NUMPAD_7':
                self._workcells[1].crash()
            if event.input.name == 'NUMPAD_9':
                self._workcells[0].crash()
            if event.input.name == 'NUMPAD_1':
                self._workcells[0]._h1.halt()

        elif event.type == carb.input.KeyboardEventType.KEY_RELEASE:
            pass

        return True

    def world_cleanup(self):
        world = self.get_world()
        if world.physics_callback_exists("physics_step"):
            world.remove_physics_callback("physics_step")
        stop_actors()
