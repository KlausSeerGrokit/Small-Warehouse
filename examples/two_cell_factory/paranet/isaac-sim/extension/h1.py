import io
import math
from typing import List, Optional

import carb
import numpy as np
import omni
import omni.kit.commands
import torch
from omni.isaac.core.articulations import Articulation, ArticulationView
from omni.isaac.core.utils.prims import define_prim, get_prim_at_path
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.nucleus import get_assets_root_path

from omni.isaac.examples.user_examples.walker import XYWalker

class H1FlatTerrainPolicy:
    """The H1 Humanoid running Flat Terrain Policy Locomotion Policy"""

    def __init__(
        self,
        prim_path: str,
        name: str = "h1",
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize H1 robot and import flat terrain policy.

        Args:
            prim_path {str} -- prim path of the robot on the stage
            name {str} -- name of the quadruped
            usd_path {str} -- robot usd filepath in the directory
            position {np.ndarray} -- position of the robot
            orientation {np.ndarray} -- orientation of the robot

        """
        self._stage = get_current_stage()
        self._prim_path = prim_path
        prim = get_prim_at_path(self._prim_path)
        self.assets_root_path = get_assets_root_path()
        assets_root_path = get_assets_root_path()
        if prim.IsValid():
            print(f"Using {prim_path} from preloaded USD")
        else:
            prim = define_prim(self._prim_path, "Xform")
            if usd_path:
                print(f"Adding {prim_path} from {usd_path}")
                prim.GetReferences().AddReference(usd_path)
            else:
                if assets_root_path is None:
                    carb.log_error("Could not find Isaac Sim assets folder")

                asset_path = assets_root_path + "/Isaac/Robots/Unitree/H1/h1.usd"
                print(f"Adding {prim_path} from {asset_path}")

                prim.GetReferences().AddReference(asset_path)

        self.view = ArticulationView(
            [self._prim_path],
            name=name,
        )

        self.robot = Articulation(
            prim_path=self._prim_path,
            name=name,
            position=position,
            orientation=orientation,
        )

        self._dof_control_modes: List[int] = list()

        # Policy
        file_content = omni.client.read_file(
            assets_root_path + "/Isaac/Samples/Quadruped/H1_Policies/h1_policy.pt"
        )[2]
        file = io.BytesIO(memoryview(file_content).tobytes())

        self._policy = torch.jit.load(file)
        self._base_vel_lin_scale = 1
        self._base_vel_ang_scale = 1
        self._action_scale = 0.5
        self._default_joint_pos = [
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            -0.52,
            -0.52,
            -0.28,
            -0.28,
            0.0,
            0.0,
            0.79,
            0.79,
            0.0,
            0.0,
            -0.52,
            -0.52,
            0.52,
            0.52,
        ]
        self._previous_action = np.zeros(19)
        self._policy_counter = 0

    def _compute_observation(self, command):
        """
        Compute the observation vector for the policy.

        Argument:
        command {np.ndarray} -- the robot command (v_x, v_y, w_z)

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

        obs = np.zeros(69)
        # Base lin vel
        obs[:3] = self._base_vel_lin_scale * lin_vel_b
        # Base ang vel
        obs[3:6] = self._base_vel_ang_scale * ang_vel_b
        # Gravity
        obs[6:9] = gravity_b
        # Command
        obs[9] = self._base_vel_lin_scale * command[0]
        obs[10] = self._base_vel_lin_scale * command[1]
        obs[11] = self._base_vel_ang_scale * command[2]
        # Joint states
        current_joint_pos = self.robot.get_joint_positions()
        current_joint_vel = self.robot.get_joint_velocities()
        obs[12:31] = current_joint_pos - self._default_joint_pos
        obs[31:50] = current_joint_vel
        # Previous Action
        obs[50:69] = self._previous_action

        return obs

    def advance(self, dt, command):
        """
        Compute the desired articulation action and apply them to the robot articulation.

        Argument:
        dt {float} -- Timestep update in the world.
        command {np.ndarray} -- the robot command (v_x, v_y, w_z)

        """
        if self._policy_counter % 4 == 0:
            obs = self._compute_observation(command)
            with torch.no_grad():
                obs = torch.from_numpy(obs).view(1, -1).float()
                self.action = self._policy(obs).detach().view(-1).numpy()
            self._previous_action = self.action.copy()

        action = ArticulationAction(
            joint_positions=self._default_joint_pos + (self.action * self._action_scale)
        )
        self.robot.apply_action(action)

        self._policy_counter += 1

    def initialize(self, physics_sim_view=None) -> None:
        """
        Initialize the articulation interface, set up robot drive mode,
        """
        self.robot.initialize(physics_sim_view=physics_sim_view)
        self.robot.get_articulation_controller().set_effort_modes("force")
        self.robot.get_articulation_controller().switch_control_mode("position")
        self.view.initialize(physics_sim_view=physics_sim_view)
        # initialize robot parameter, set joint properties based on the values from env param

        # H1 joint order
        # ['left_hip_yaw_joint', 'right_hip_yaw_joint', 'torso_joint', 'left_hip_roll_joint', 'right_hip_roll_joint',
        #  'left_shoulder_pitch_joint', 'right_shoulder_pitch_joint', 'left_hip_pitch_joint', 'right_hip_pitch_joint',
        #  'left_shoulder_roll_joint', 'right_shoulder_roll_joint', 'left_knee_joint', 'right_knee_joint',
        # 'left_shoulder_yaw_joint', 'right_shoulder_yaw_joint', 'left_ankle_joint', 'right_ankle_joint', 'left_elbow_joint', 'right_elbow_joint']
        stiffness = np.array(
            [
                150,
                150,
                200,
                150,
                150,
                40,
                40,
                200,
                200,
                40,
                40,
                200,
                200,
                40,
                40,
                20,
                20,
                40,
                40,
            ]
        )
        damping = np.array(
            [5, 5, 5, 5, 5, 10, 10, 5, 5, 10, 10, 5, 5, 10, 10, 4, 4, 10, 10]
        )
        max_effort = np.array(
            [
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                300,
                100,
                100,
                300,
                300,
            ]
        )
        max_vel = np.zeros(19) + 100.0
        self.robot._articulation_view.set_gains(stiffness, damping)
        self.robot._articulation_view.set_max_efforts(max_effort)
        self.robot._articulation_view.set_max_joint_velocities(max_vel)

    def post_reset(self) -> None:
        """
        Post Reset robot articulation
        """
        self.robot.post_reset()
        self._previous_action = np.zeros(19)
        self._policy_counter = 0

class H1Sim:
    def __init__(self, root_path, name, position, target):
        self.name = name
        self.home_position = position
        self.target = target
        self.stand = False
        self.placing = False
        self.placed = False
        self.homing = False
        self.h1 = H1FlatTerrainPolicy(
            prim_path=root_path+"/Robots/H1",
            name=name,
            position=position,
        )
        self.walk = XYWalker(self.h1.robot, position, 0)
        self.falling = False
        self.callback = None
        self.listeners = []

    def initialize(self):
        self.h1.initialize()

    def post_reset(self):
        self.h1.post_reset()
        self.stand = False
        self.placing = False
        self.placed = False
        self.homing = False

    def halt(self):
        self.stand = True

    def place_block(self, callback):
        self.callback = callback
        self.placing = True
        self.placed = False
        self.homing = False
        self.walk.set_target(self.target[0])

    def physics_step(self, step_size, base_command):
        if self.stand:
            return

        if self.falling:
            cmd = np.zeros((3,))
            cmd[self.walk.axis] = -1.0
            self.h1.advance(step_size, cmd)
            return

        cmd = self.walk.get_command()
        cmd += base_command

        self.h1.advance(step_size, cmd)
        if self.placing and self.walk.holding:
            self.placing = False
            self.placed = True
            self.homing = True
            self.walk.set_target(self.home_position[0])
            if self.callback:
                self.callback('done')
                self.callback = None

        if self.homing and self.walk.holding:
            self.homing = False

    def is_done(self):
        return self.placed

    def add_listener(self, obj, arg):
        self.listeners.append((obj, arg))

    def fall(self):
        self.falling = True
        for l in self.listeners:
            l[0].handle_event(l[1], 'sos', 'H1 down')


class H1_DigitSim:
    def __init__(self, root_path, name, offset, sim, position, targets):
        self._offset = offset
        self.name = name
        self.sim = sim
        self.targets = targets
        self.corner = position
        self.h1 = H1FlatTerrainPolicy(
            prim_path=root_path+"/Robots/H1_Digit",
            name=name,
            position=self.corner + self._offset,
        )
        self.walk = XYWalker(self.h1.robot, self.corner + self._offset, 0)
        self.location = 'corner'
        self.execute = False
        self.action = None
        self.callback = None
        self.falling = False

    def initialize(self):
        self.h1.initialize()

    def post_reset(self):
        self.h1.post_reset()

    def get_world_pose(self):
        return self.h1.robot.get_world_pose()

    def start_plan(self):
        self.plan_state = 0
        self.phase = ''
        self.execute = True

    def run_plan_next(self):
        if self.phase == 'walk':
            # end of state, run associated action
            if self.plan_state == self.action[0]:
                if self.action[1] == 'get':
                    self.sim.attach_tote()
                elif 'good' in self.action[1]:
                    self.sim.detach_tote(self.targets['good_tote'])
                elif 'bad' in self.action[1]:
                    self.sim.detach_tote(self.targets['bad_tote'])

            # advance to next state
            self.plan_state += 1
            self.execute = self.plan_state < len(self.plan)
            if not self.execute:
                if self.action[1] == 'get':
                    self.location = 'belt'
                elif 'good' in self.action[1]:
                    self.location = 'tables'
                elif 'bad' in self.action[1]:
                    self.location = 'tables'
                elif self.action[1] == 'home':
                    self.location = 'corner'

                if self.callback:
                    self.callback('done')
                    self.callback = None

                return

        (axis, facing, position) = self.plan[self.plan_state]
        if self.walk.axis == axis and self.walk.facing == facing:
            print(f"[{self.name}] state {self.plan_state} walking")
            self.walk.set_target(position[axis] + self._offset[axis])
            self.phase = 'walk'
        else:
            print(f"[{self.name}] state {self.plan_state} orienting")
            self.walk.orient(axis, facing)
            self.phase = 'orient'

    def physics_step(self, step_size, base_command):
        if self.falling:
            cmd = np.zeros((3,))
            cmd[self.walk.axis] = -1.0
            self.h1.advance(step_size, cmd)
            return

        if self.execute and self.walk.holding:
            self.run_plan_next()

        cmd = self.walk.get_command()
        cmd += base_command

        self.h1.advance(step_size, cmd)

    def corner_plan(self):
        if self.location == 'tables':
            return [(1, -1, self.targets['corner'])]
        elif self.location == 'belt':
            return [(0, -1, self.targets['corner'])]
        return []

    def goto_corner(self):
        self.plan = self.corner_plan()
        if len(self.plan) > 0:
            self.action = (0, 'home')
            self.start_plan()

    def get_tote(self, callback = None):
        self.callback = callback
        self.plan = self.corner_plan()
        first_state = len(self.plan)
        self.plan.extend([
            (0, 1, self.targets['belt_approach']),
            (1, -1, self.targets['belt_pickup']),
            (1, -1, self.targets['belt_approach'])
        ])
        self.action = (first_state+1, 'get')
        self.start_plan()

    def place_tote(self, table, callback = None):
        self.callback = callback
        self.plan = self.corner_plan()
        first_state = len(self.plan)
        if 'good' in table:
            self.plan.extend([
                (1, 1, self.targets['good_approach']),
                (0, -1, self.targets['good_place']),
                (0, -1, self.targets['good_approach']),
            ])
        else:
            self.plan.extend([
                (1, 1, self.targets['bad_approach']),
                (0, -1, self.targets['bad_place']),
                (0, -1, self.targets['bad_approach']),
            ])
        self.action = (first_state+1, 'drop_'+table)
        self.start_plan()

    def halt(self):
        self.execute = False
        self.action = None

    def fall(self):
        self.falling = True
        self.execute = False
        self.action = None

    def is_done(self):
        return not self.execute
