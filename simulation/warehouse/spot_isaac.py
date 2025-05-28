import io
import math
import numpy as np
import torch
import os
import omni.kit.commands
from isaacsim.core.prims import SingleArticulation
from isaacsim.core.utils.prims import define_prim, get_prim_at_path
from isaacsim.core.prims import SingleRigidPrim
from isaacsim.core.utils.rotations import quat_to_rot_matrix
from isaacsim.core.utils.stage import get_current_stage
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.robot.policy.examples.controllers import PolicyController
from isaacsim.storage.native import get_assets_root_path
from pxr import UsdGeom

# from isaacsim.range_sensor import _range_sensor

from .math_util import euler_from_quaternion
from .vfh import VFH

CLOUD_CLIP_DIST = 10

ASSET_PATH = os.environ.get(
    "ASSET_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)


class LidarDebugTrace:
    def __init__(self):
        self.hist = []

    def dump(self):
        for obj in self.hist:
            print("POS", obj["origin"], "ROT", obj["rot"])
            print("DEPTH", obj["depth"])
            print("AZIMUTH", obj["azimuth"])
            print("CLOUD", obj["cloud"])


from typing import Optional

import numpy as np
import omni
import omni.kit.commands
from isaacsim.core.utils.rotations import quat_to_rot_matrix
from isaacsim.core.utils.types import ArticulationAction
from isaacsim.robot.policy.examples.controllers import PolicyController
from isaacsim.storage.native import get_assets_root_path


class CustomSpotFlatTerrainPolicy(PolicyController):
    """The Spot quadruped"""

    def __init__(
        self,
        prim_path: str,
        root_path: Optional[str] = None,
        name: str = "spot",
        color: str = None,
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize robot and load RL policy.

        Args:
            prim_path (str) -- prim path of the robot on the stage
            root_path (Optional[str]): The path to the articulation root of the robot
            name (str) -- name of the quadruped
            usd_path (str) -- robot usd filepath in the directory
            position (np.ndarray) -- position of the robot
            orientation (np.ndarray) -- orientation of the robot

        """
        self._stage = get_current_stage()
        self._prim_path = prim_path
        prim = get_prim_at_path(self._prim_path)

        assets_root_path = get_assets_root_path()
        if not prim.IsValid():
            prim = define_prim(self._prim_path, "Xform")
            if usd_path:
                prim.GetReferences().AddReference(usd_path)
            else:
                if not color:
                    asset_path = (
                        f"{assets_root_path}/Isaac/Robots/BostonDynamics/spot/spot.usd"
                    )
                else:
                    asset_path = os.path.join(ASSET_PATH, f"{color}_spot.usd")

                print(f"Adding {asset_path} to stage ...")
                prim.GetReferences().AddReference(asset_path)

        self.robot = SingleArticulation(
            prim_path=self._prim_path,
            name=name,
            position=position,
            orientation=orientation,
        )

        super().__init__(name, prim_path, root_path, usd_path, position, orientation)

        self.load_policy(
            assets_root_path + "/Isaac/Samples/Policies/Spot_Policies/spot_policy.pt",
            assets_root_path + "/Isaac/Samples/Policies/Spot_Policies/spot_env.yaml",
        )
        self._action_scale = 0.2
        self._previous_action = np.zeros(12)
        self._policy_counter = 0
        self.default_pos = np.array(
            [0.1, -0.1, 0.1, -0.1, 0.9, 0.9, 1.1, 1.1, -1.5, -1.5, -1.5, -1.5]
        )

    def _compute_observation(self, command):
        """
        Compute the observation vector for the policy

        Argument:
        command (np.ndarray) -- the robot command (v_x, v_y, w_z)

        Returns:
        np.ndarray -- The observation vector.

        """
        lin_vel_I = self.robot.get_linear_velocity()
        ang_vel_I = self.robot.get_angular_velocity()
        pos_IB, q_IB = self.robot.get_world_pose()

        R_IB = quat_to_rot_matrix(q_IB)
        R_BI = R_IB.transpose()
        lin_vel_b = np.matmul(R_BI, lin_vel_I)
        ang_vel_b = np.matmul(R_BI, ang_vel_I)
        gravity_b = np.matmul(R_BI, np.array([0.0, 0.0, -1.0]))

        obs = np.zeros(48)
        # Base lin vel
        obs[:3] = lin_vel_b
        # Base ang vel
        obs[3:6] = ang_vel_b
        # Gravity
        obs[6:9] = gravity_b
        # Command
        obs[9:12] = command
        # Joint states
        current_joint_pos = self.robot.get_joint_positions()
        current_joint_vel = self.robot.get_joint_velocities()
        obs[12:24] = current_joint_pos - self.default_pos
        obs[24:36] = current_joint_vel
        # Previous Action
        obs[36:48] = self._previous_action

        return obs

    def advance(self, dt, command):
        """
        Compute the desired torques and apply them to the articulation

        Argument:
        dt (float) -- Timestep update in the world.
        command (np.ndarray) -- the robot command (v_x, v_y, w_z)

        """
        if self._policy_counter % self._decimation == 0:
            obs = self._compute_observation(command)
            self.action = self._compute_action(obs)
            self._previous_action = self.action.copy()

        action = ArticulationAction(
            joint_positions=self.default_pos + (self.action * self._action_scale)
        )
        self.robot.apply_action(action)

        self._policy_counter += 1

    def initialize(self, physics_sim_view=None):
        self.robot.initialize(physics_sim_view=physics_sim_view)
        self.robot.get_articulation_controller().set_effort_modes("force")
        self.robot.get_articulation_controller().switch_control_mode("position")
        self.robot._articulation_view.set_gains(np.zeros(12) + 60, np.zeros(12) + 1.5)

    def post_reset(self):
        self.robot.post_reset()


class Spot:
    def __init__(self, root_path, drop_loc, color):
        self.name = " ".join(root_path[1:].split("/"))
        self.prefix = "_".join(root_path[1:].split("_")) + "_"
        self.root_path = root_path
        self.body_path = root_path + "/spot" if color else root_path
        self.drop_loc = drop_loc
        self.color = color

        self.cmd = np.zeros(3)
        self.iter = 0
        self.moving = False
        self.callback = None
        self.trace = LidarDebugTrace()

    def grid_world_position(self, pos):
        return np.append(pos, 0.8)

    def get_approx_loc(self):
        pos, _ = self.lidar.get_world_pose()
        return (pos[0], pos[1])

    def setup_scene(self):
        self.controller = CustomSpotFlatTerrainPolicy(
            prim_path=self.root_path,
            name=self.name,
            position=self.grid_world_position(self.drop_loc),
            color=self.color,
        )

        print("Spot Position:", self.controller.robot.get_world_pose())
        # self.controller.robot.set_joints_default_state(self.controller.default_pos)

        result, prim = omni.kit.commands.execute(
            "RangeSensorCreateLidar",
            path="Lidar",
            parent=self.body_path + "/body",
            rotation_rate=0.0,
            horizontal_fov=180,
        )
        UsdGeom.XformCommonAPI(prim).SetTranslate((0.5, 0.0, -0.12))
        self.lidar_path = self.body_path + "/body/Lidar"
        self.lidar = SingleRigidPrim(self.lidar_path)
        # self.lidarInterface = _range_sensor.acquire_lidar_sensor_interface()

    def setup_post_load(self):
        self.controller.initialize()
        self.nav = VFH(self.controller.robot, id=self.name)

    def on_physics_step(self, step_size, keyboard_cmd):
        if self.moving:
            if (self.iter % 5) == 0:
                # cloud = self.get_world_cloud()
                # if cloud is not None:
                #    self.nav.update_cloud(cloud)
                if (self.iter % 10) == 0:
                    self.cmd = self.nav.get_command(trace=self.trace)
                    self.trace = LidarDebugTrace()
                    if self.nav.done:
                        self.moving = False
                        self.iter = 0
                        cb = self.callback
                        self.callback = None
                        if cb:
                            cb()
            cmd = self.cmd
        else:
            cmd = keyboard_cmd

        self.controller.advance(step_size, cmd)
        self.iter += 1

    def get_world_cloud(self):
        depth = self.lidarInterface.get_linear_depth_data(self.lidar_path)
        azimuth = self.lidarInterface.get_azimuth_data(self.lidar_path)
        idx = depth[:, 0] < CLOUD_CLIP_DIST
        origin, rot = self.lidar.get_world_pose()
        rot = euler_from_quaternion(rot)
        deg_rot = np.round(rot / math.pi * 180)

        if abs(deg_rot[0]) + deg_rot[1] >= 3:
            return None

        x = depth[idx, 0] * np.cos(azimuth[idx] + rot[2]) + origin[0]
        y = depth[idx, 0] * np.sin(azimuth[idx] + rot[2]) + origin[1]
        cloud = np.stack([x, y], axis=-1)

        self.trace.hist.append(
            {
                "depth": depth[idx, 0],
                "azimuth": azimuth[idx],
                "rot": deg_rot,
                "cloud": cloud,
                "origin": origin,
            }
        )

        return cloud

    def run_nav(self, loc, callback, midpoint=False):
        self.callback = callback
        target = self.grid_world_position(loc)
        self.nav.clear()
        self.nav.set_target(target[0:2], midpoint=midpoint)
        self.moving = True

    def stop_nav(self):
        if self.moving:
            self.nav.stop()

    def get_loc(self):
        return self.get_approx_loc()

    def get_direction(self):
        _, rot = self.lidar.get_world_pose()
        rot = euler_from_quaternion(rot)
        deg = math.degrees(rot[2])
        return deg if deg >= 0 else 360 + deg

    def get_distance(self, loc):
        pos, _ = self.lidar.get_world_pose()
        target = self.grid_world_position(loc)
        return np.linalg.norm([pos[0:2], target[0:2]])
