import random
import numpy as np
import omni
import omni.appwindow

from omni.isaac.core.utils.prims import create_prim
from omni.isaac.nucleus import get_assets_root_path
from omni.isaac.core.prims import RigidPrim, XFormPrim

from omni.isaac.franka import Franka
from omni.isaac.core.objects import DynamicCuboid


from omni.isaac.examples.user_examples.h1 import H1Sim, H1_DigitSim
from omni.isaac.examples.user_examples.g1 import G1_DigitSim
from omni.isaac.examples.user_examples.franka import FrankaSim
from omni.isaac.examples.user_examples.belt import BeltSim

from pxr import PhysxSchema
from pxr import UsdPhysics, PhysxSchema
from pxr import Sdf

from pxr import UsdShade, Sdf

########## Utility functions


def get_visibility_attribute(stage, prim_path):
    path = Sdf.Path(prim_path)
    prim = stage.GetPrimAtPath(path)
    if not prim.IsValid():
        return None
    visibility_attribute = prim.GetAttribute("visibility")
    return visibility_attribute


def hide_prim(prim_path):
    stage = omni.usd.get_context().get_stage()
    visibility_attribute = get_visibility_attribute(stage, prim_path)
    if visibility_attribute is None:
        return
    visibility_attribute.Set("invisible")


def show_prim(prim_path):
    stage = omni.usd.get_context().get_stage()
    visibility_attribute = get_visibility_attribute(stage, prim_path)
    if visibility_attribute is None:
        return
    visibility_attribute.Set("inherited")


def remove_collision_api(prim_path: str):
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        print(f"Prim not found at path: {prim_path}")
        return

    # Remove any PhysX Collision API
    if prim.HasAPI(PhysxSchema.PhysxCollisionAPI):
        prim.RemoveAPI(PhysxSchema.PhysxCollisionAPI)

    # Remove USD Physics Collision API
    if prim.HasAPI(UsdPhysics.CollisionAPI):
        prim.RemoveAPI(UsdPhysics.CollisionAPI)


def set_rigid_body_enabled(prim_path, enabled=True):
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(prim_path)
    if not prim.IsValid():
        print(f"Prim not found at path: {prim_path}")
        return

    if enabled:
        # Apply PhysX Rigid Body
        PhysxSchema.PhysxRigidBodyAPI.Apply(prim)
    else:
        # Remove the PhysX Rigid Body if it exists
        if prim.HasAPI(PhysxSchema.PhysxRigidBodyAPI):
            prim.RemoveAPI(PhysxSchema.PhysxRigidBodyAPI)

########## Workcell class

# Container/manager for all objects in a cell


class Workcell:
    def __init__(self, root_path, offset=np.zeros((3,))):
        self.name = " ".join(root_path[1:].split("/"))
        self.prefix = "_".join(root_path[1:].split("_")) + "_"
        self.root_path = root_path

        self._offset = offset
        self._attached_cube_path = self.root_path + "/Robots/H1/right_elbow_link/cube"
        self._free_cube_path = self.root_path + "/free_cube"

        self._attached_tote_path = self.root_path + "/Robots/H1_Digit/torso_link/tote"
        self._free_tote_path = self.root_path + "/Props/Tote"

        self._base_command = np.array([0.0, 0.0, 0.0])

        # workcell state
        self._has_detached_cube = False
        self._free_cube = None
        self._trial_outcome = "good"
        self._trial_count = 0

    def setup_scene(self, world):
        self._world = world

        world.scene.add(
            Franka(
                prim_path=self.root_path + "/fancy_franka",
                name=self.prefix + "fancy_franka",
                position=np.array([0, 0, 0.635 * 1.2] + self._offset),
            )
        )

        # Create H1 at some position
        h1_drop = np.array([-3, 0.5, 1.04]) + self._offset
        h1_target = np.array([-0.6, 0.0, 0.0]) + self._offset

        # Get Material for lights
        stage = omni.usd.get_context().get_stage()
        # Path to the Shader prim under the material
        green_shader_prim_path = self.root_path + "/Props/Light_Panel/Light/Looks/GreenEmissive/Shader"
        green_shader_prim = stage.GetPrimAtPath(green_shader_prim_path)

        if green_shader_prim.IsValid():
            green_mdl_shader = UsdShade.Shader(green_shader_prim)

            # Now get or create the emission_intensity input
            self.green_emissive_input = green_mdl_shader.GetInput("emission_intensity")
            if not self.green_emissive_input:
                self.green_emissive_input = green_mdl_shader.CreateInput(
                    "emission_intensity", Sdf.ValueTypeNames.Float
                )

            # Path to the Shader prim under the material
        red_shader_prim_path = self.root_path + "/Props/Light_Panel/Light/Looks/RedEmissive/Shader"
        red_shader_prim = stage.GetPrimAtPath(red_shader_prim_path)

        if red_shader_prim.IsValid():
            red_mdl_shader = UsdShade.Shader(red_shader_prim)

            # Now get or create the emission_intensity input
            self.red_emissive_input = red_mdl_shader.GetInput("emission_intensity")
            if not self.red_emissive_input:
                self.red_emissive_input = red_mdl_shader.CreateInput(
                    "emission_intensity", Sdf.ValueTypeNames.Float
                )

        self._h1 = H1Sim(self.root_path, self.prefix + "humanoid_0", h1_drop, h1_target)
        self._digit = H1_DigitSim(
            self.root_path,
            self.prefix + "humanoid_1",
            self._offset,
            self,
            np.array([1.2, 1.0, 1.04]),
            # Digit locations
            {
                "corner": np.array([1.2, 1.0]),
                "belt_approach": np.array([4.33, 1.0]),
                "belt_pickup": np.array([4.33, 0.8]),
                "good_approach": np.array([1.2, 2.4]),
                "good_place": np.array([1.0, 2.4]),
                "bad_approach": np.array([1.2, 3.4]),
                "bad_place": np.array([1.0, 3.4]),
                # tote locations on table
                "good_tote": np.array([0.3, 2.4, 0.8]),
                "bad_tote": np.array([0.3, 3.4, 0.8]),
            },
        )

        # self._digit = G1_DigitSim(
        #     self.root_path,
        #     self.prefix+'humanoid_1',
        #     self._offset,
        #     self,
        #     np.array([1.2, 1.0, 0.74]),
        #     # Digit locations
        #     {'corner': np.array([1.2, 1.0]),
        #      'belt_approach': np.array([4.33, 1.0]),
        #      'belt_pickup': np.array([4.33, 0.9]),
        #      'good_approach': np.array([1.2,2.4]),
        #      'good_place': np.array([1.1,2.4]),
        #      'bad_approach': np.array([1.2,3.4]),
        #      'bad_place': np.array([1.0,3.4]),
        #      # tote locations on table
        #      'good_tote': np.array([0.3,2.4,0.8]),
        #      'bad_tote': np.array([0.3,3.4,0.8])}
        # )

        # Create a dynamic cube prim. We'll attach it to H1 so it "carries" it.
        self.cube = DynamicCuboid(
            prim_path=self._attached_cube_path,
            name=self.prefix + "cube",
            position=h1_drop + np.array([0.325, -0.2, 0.11]),  # Slightly above H1
            scale=np.array([0.0515, 0.0515, 0.0515]),
            color=np.array([0, 1, 0]),
        )
        set_rigid_body_enabled(self._attached_cube_path, False)
        remove_collision_api(self._attached_cube_path)

        assets_root_path = get_assets_root_path()
        if assets_root_path != None:
            prim = create_prim(
                prim_path=self._attached_tote_path,
                prim_type="Xform",
                translation=np.array([0.4, 0.0, 0.1]),
                scale=np.array([1.5, 1.0, 1.0]),
            )
            prim.GetReferences().AddReference(
                assets_root_path + "/Isaac/Props/KLT_Bin/small_KLT.usd"
            )
            hide_prim(self._attached_tote_path)

    def setup_post_load(self, world):
        self._franka = FrankaSim(
            self.root_path + "/Arm",
            world.scene.get_object(self.prefix + "fancy_franka"),
            self,
            np.array([0.57, 0.04, 1.02] + self._offset),
        )

        self._belt = BeltSim(self.root_path, self.root_path + "/Belt", self)

        self._tote = RigidPrim(self._free_tote_path)
        self._tote_home_pose = self._tote.get_world_pose()

        self._h1.initialize()
        self._digit.initialize()
        self._belt.initialize()

    def setup_post_reset(self):
        self._has_detached_cube = False

        self._h1.post_reset()
        self._digit.post_reset()
        self._h1.initialize()
        self._digit.initialize()

        self._franka.post_reset()

    # physics_dt=1/60 step
    def physics_60(self) -> None:
        self._franka.physics_step()
        self._belt.physics_step()

    # physics_dt=1/200 step
    def physics_200(self, step_size) -> None:
        self._h1.physics_step(step_size, self._base_command)
        self._digit.physics_step(step_size, self._base_command)

        if not self._has_detached_cube and self._h1.is_done():
            pos, _ = self.cube.get_world_pose()
            print(f"[{self._h1.name}] Drop cube on table", pos)
            hide_prim(self._attached_cube_path)
            self._free_cube = DynamicCuboid(
                prim_path=self._free_cube_path,
                name=self.prefix + "free_cube",
                position=pos,
                scale=np.array([0.0515, 0.0515, 0.0515]),
                color=self.block_color(),
            )
            self._world.scene.add(self._free_cube)
            self._has_detached_cube = True

    def h1(self):
        return self._h1

    def arm(self):
        return self._franka

    def belt(self):
        return self._belt

    def digit(self):
        return self._digit

    def block_color(self):
        if self._trial_outcome == "good":
            return np.array([0, 1, 0])
        else:
            return np.array([1, 0, 0])

    def get_cube(self):
        return self._free_cube

    def set_lights(self, green=False, red=False):
        if green:
            self.green_emissive_input.Set(3.0)
        else:
            self.green_emissive_input.Set(0.0)
        if red:
            self.red_emissive_input.Set(3.0)
        else:
            self.red_emissive_input.Set(0.0)

    def attach_tote(self):
        hide_prim(self._free_tote_path)
        show_prim(self._attached_tote_path)
        position, _ = self._digit.get_world_pose()
        self._free_cube.set_world_pose(position = position + np.array([0.0, -0.32, 0.1]) + np.array([0.0, -0.1, 0.0]))

    def detach_tote(self, position):
        hide_prim(self._attached_tote_path)
        self._tote.set_world_pose(position=position + self._offset)
        self._free_cube.set_world_pose(
            position=position + np.array([0.0, -0.1, 0.0]) + self._offset
        )
        show_prim(self._free_tote_path)

    def reset_cell(self):
        # select outcome for new demo
        self._trial_outcome = random.choice(["good", "bad"])
        self.cube.get_applied_visual_material().set_color(self.block_color())
        self._trial_count += 1
        print(f"[{self.name}] Trial {self._trial_count}: {self._trial_outcome}")

        # free block
        if self._free_cube != None:
            self._world.scene.remove_object(self.prefix + "free_cube")
            self._free_cube = None
        self._has_detached_cube = False

        # H1 attached block
        show_prim(self._attached_cube_path)

        # tote
        hide_prim(self._attached_tote_path)
        self._tote.set_world_pose(position=self._tote_home_pose[0])
        show_prim(self._free_tote_path)

        self._franka.post_reset()
        self._digit.goto_corner()

    def crash(self):
        self._h1.fall()
        self._digit.halt()
        self.set_lights(red=True)
