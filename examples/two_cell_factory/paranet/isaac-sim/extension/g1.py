# Copyright (c) 2024, NVIDIA CORPORATION. All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto. Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#

import os
import io
from typing import List, Optional

import carb
import numpy as np
import omni
import omni.kit.commands
import torch
from omni.isaac.core.articulations import Articulation
from omni.isaac.core.utils.prims import define_prim, get_prim_at_path
from omni.isaac.core.utils.rotations import quat_to_rot_matrix
from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.core.utils.types import ArticulationAction
from omni.isaac.nucleus import get_assets_root_path

from omni.isaac.examples.user_examples.joint_config import ImplicitActuatorCfg
from omni.isaac.examples.user_examples.walker import XYWalker

g1_joint_cfg ={
        "legs": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_hip_yaw_joint",
                ".*_hip_roll_joint",
                ".*_hip_pitch_joint",
                ".*_knee_joint",
                "torso_joint",
            ],
            effort_limit=300,
            velocity_limit=100.0,
            stiffness={
                ".*_hip_yaw_joint": 150.0,
                ".*_hip_roll_joint": 150.0,
                ".*_hip_pitch_joint": 200.0,
                ".*_knee_joint": 200.0,
                "torso_joint": 200.0,
            },
            damping={
                ".*_hip_yaw_joint": 5.0,
                ".*_hip_roll_joint": 5.0,
                ".*_hip_pitch_joint": 5.0,
                ".*_knee_joint": 5.0,
                "torso_joint": 5.0,
            },
            armature={
                ".*_hip_.*": 0.01,
                ".*_knee_joint": 0.01,
                "torso_joint": 0.01,
            },
        ),
        "feet": ImplicitActuatorCfg(
            effort_limit=20,
            joint_names_expr=[".*_ankle_pitch_joint", ".*_ankle_roll_joint"],
            stiffness=20.0,
            damping=2.0,
            armature=0.01,
        ),
        "arms": ImplicitActuatorCfg(
            joint_names_expr=[
                ".*_shoulder_pitch_joint",
                ".*_shoulder_roll_joint",
                ".*_shoulder_yaw_joint",
                ".*_elbow_pitch_joint",
                ".*_elbow_roll_joint",
                ".*_five_joint",
                ".*_three_joint",
                ".*_six_joint",
                ".*_four_joint",
                ".*_zero_joint",
                ".*_one_joint",
                ".*_two_joint",
            ],
            effort_limit=300,
            velocity_limit=100.0,
            stiffness=40.0,
            damping=10.0,
            armature={
                ".*_shoulder_.*": 0.01,
                ".*_elbow_.*": 0.01,
                ".*_five_joint": 0.001,
                ".*_three_joint": 0.001,
                ".*_six_joint": 0.001,
                ".*_four_joint": 0.001,
                ".*_zero_joint": 0.001,
                ".*_one_joint": 0.001,
                ".*_two_joint": 0.001,
            },
        )
    }


class G1FlatTerrainPolicy:
    """The G1 Humanoid running Flat Terrain Policy Locomotion Policy"""

    def __init__(
        self,
        prim_path: str,
        name: str = "g1",
        usd_path: Optional[str] = None,
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
    ) -> None:
        """
        Initialize G1 robot and import flat terrain policy.

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
        local_dir = os.path.dirname(os.path.realpath(__file__))
        assets_root_path = get_assets_root_path()
        asset_path = assets_root_path + "/Isaac/IsaacLab/Robots/Unitree/G1/g1_minimal.usd"
        #asset_path = os.path.join(local_dir, 'g1_minimal_limited.usd')
        if not prim.IsValid():
            prim = define_prim(self._prim_path, "Xform")
        prim.GetReferences().AddReference(asset_path)

        self.robot = Articulation(prim_path=self._prim_path, name=name, position=position, orientation=orientation)

        self._dof_control_modes: List[int] = list()

        # Policy
        file_content = omni.client.read_file(os.path.join(local_dir, 'g1_policy4.pt'))[2]
        file = io.BytesIO(memoryview(file_content).tobytes())

        self._policy = torch.jit.load(file)
        self._action_scale = 0.5
        self._previous_action = np.zeros(37)
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
        current_joint_pos = self.robot.get_joint_positions() - self._default_joint_pos
        current_joint_vel = self.robot.get_joint_velocities()

        obs = np.concatenate((
            lin_vel_b, # 3
            ang_vel_b, # 3
            gravity_b, # 3
            command[:3], # 3
            current_joint_pos, # 37
            current_joint_vel, # 37
            self._previous_action # 37
        ))

        return obs

    def advance(self, dt, command):
        """
        Compute the desired articulation action and apply them to the robot articulation.

        Argument:
        dt {float} -- Timestep update in the world.
        command {np.ndarray} -- the robot command (v_x, v_y, w_z)

        """
        #if self._policy_counter > 0:
        #    return

        if self._policy_counter % 4 == 0:
            obs = self._compute_observation(command)
            #print(obs)
            with torch.no_grad():
                obs = torch.from_numpy(obs).view(1, -1).float()
                self.action = self._policy(obs).detach().view(-1).numpy()
                #print(self.action)
            self._previous_action = self.action.copy()
            #self.action[self._elbow_pitch_indices] = (0.0 - self._default_joint_pos[self._elbow_pitch_indices]) / self._action_scale
            self.action[self._shoulder_pitch_indices] = (0.0 - self._default_joint_pos[self._shoulder_pitch_indices]) / self._action_scale

        action = ArticulationAction(joint_positions=self._default_joint_pos + (self.action * self._action_scale))
        self.robot.apply_action(action)

        self._policy_counter += 1

    def initialize(self, physics_sim_view=None) -> None:
        """
        Initialize the articulation interface, set up robot drive mode,
        """
        self.robot.initialize(physics_sim_view=physics_sim_view)
        self.robot.get_articulation_controller().set_effort_modes("force")
        self.robot.get_articulation_controller().switch_control_mode("position")

        joints = self.robot.dof_names
        N = len(joints)
        print(joints)

        self._shoulder_pitch_indices = np.nonzero(np.array(['shoulder_pitch' in j for j in joints]))
        self._elbow_pitch_indices = np.nonzero(np.array(['elbow_pitch' in j for j in joints]))

        joint_pos={
            "hip_pitch_joint": -0.20,
            "knee_joint": 0.42,
            "ankle_pitch_joint": -0.23,
            "elbow_pitch_joint": 0.1, # 0.87,
            "left_shoulder_roll_joint": 0.16,
            "left_shoulder_pitch_joint": 0.1, # 0.35,
            "right_shoulder_roll_joint": -0.16,
            "right_shoulder_pitch_joint": 0.1, # 0.35,
            "left_one_joint": 1.0,
            "right_one_joint": -1.0,
            "left_two_joint": 0.52,
            "right_two_joint": -0.52,
        }

        self._default_joint_pos = np.zeros((N,))
        for dof in joint_pos.keys():
            for idx,name in enumerate(joints):
                if dof in name:
                    self._default_joint_pos[idx] = joint_pos[dof]

        self.robot.set_joints_default_state(positions=self._default_joint_pos, velocities=np.zeros((N,)))
        ImplicitActuatorCfg.apply(joints, g1_joint_cfg, self.robot._articulation_view)

    def post_reset(self) -> None:
        """
        Post Reset robot articulation
        """
        self.robot.post_reset()

class G1_DigitSim:
    def __init__(self, root_path, name, offset, sim, position, targets):
        self._offset = offset
        self.name = name
        self.sim = sim
        self.targets = targets
        self.corner = position
        self.g1 = G1FlatTerrainPolicy(
            prim_path=root_path+"/Robots/G1_Digit",
            name=name,
            position=self.corner + self._offset,
        )
        self.walk = XYWalker(self.g1.robot, self.corner + self._offset, 0)
        self.location = 'corner'
        self.execute = False
        self.action = None
        self.callback = None

    def initialize(self):
        self.g1.initialize()

    def post_reset(self):
        self.g1.post_reset()

    def get_world_pose(self):
        return self.g1.robot.get_world_pose()

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
        if self.execute and self.walk.holding:
            self.run_plan_next()

        cmd = self.walk.get_command()
        cmd += base_command

        self.g1.advance(step_size, cmd)

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


    def is_done(self):
        return not self.execute