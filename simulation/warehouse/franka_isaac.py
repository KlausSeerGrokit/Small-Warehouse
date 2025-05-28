from enum import Enum
from isaacsim.robot.manipulators.examples.franka.controllers import (
    RMPFlowController,
    PickPlaceController,
)
from isaacsim.robot.manipulators.examples.franka.tasks import (
    FollowTarget as FollowTargetTask,
)
import numpy as np


class FrankaState(Enum):
    IDLE = 0
    DISABLED = 1
    WAVING = 2


class FrankaHoming:
    def __init__(self, franka):
        self.franka = franka
        self.controller = RMPFlowController(
            name="franka_homing", robot_articulation=franka
        )
        self.home, _ = franka.gripper.get_world_pose()
        self.reset()

    def reset(self):
        self.controller.reset()
        self.steps = 125

    def is_done(self):
        return self.steps <= 0

    def forward(self):
        self.steps -= 1
        return self.controller.forward(target_end_effector_position=self.home)


offset = np.array([0.3, 0.0, 0.2])


class FrankaPose:
    def __init__(self, franka, offset):
        self.franka = franka
        self.controller = RMPFlowController(
            name="franka_pose", robot_articulation=franka
        )
        start_pos, _ = franka.gripper.get_world_pose()
        self.target_position = start_pos - offset
        self.reset()

    def reset(self):
        self.controller.reset()
        self.steps = 125

    def is_done(self):
        return self.steps <= 0

    def forward(self):
        self.steps -= 1
        return self.controller.forward(
            target_end_effector_position=self.target_position
        )


class FrankaSim:
    def __init__(self, name, franka, sim, target):
        self.name = name
        self.sim = sim
        self.target = target
        self.pick_n_place = -1
        self.placed = False
        self._pickup = None
        self._place = None
        self.state = FrankaState.IDLE
        self.franka = franka

        self.arm_controller = PickPlaceController(
            name="pick_place_controller",
            gripper=self.franka.gripper,
            robot_articulation=self.franka,
            end_effector_initial_height=1.0,
        )

        self.franka.gripper.set_joint_positions(
            self.franka.gripper.joint_opened_positions
        )

        self.franka_home = FrankaHoming(self.franka)
        self.franka_move = FrankaPose(self.franka, offset)

        self.waving_complete = False
        self.moving_to_disabled = False
        self.moving_to_idle = False

    def place_block(self):
        self.pick_n_place = 10
        self.placed = False

    def disable(self):
        self.state = FrankaState.DISABLED
        self.pick_n_place = 10
        self.placed = False
        self.moving_to_disabled = False
        self.franka_home.reset()
        print(f"[{self.name}] Transitioning to DISABLED state")

    def enable(self):
        self.state = FrankaState.IDLE
        self.pick_n_place = -1
        self.placed = False
        self.moving_to_idle = True
        self.franka_home.reset()
        print(f"[{self.name}] Transitioning to IDLE state")

    def wave(self):
        if self.state == FrankaState.DISABLED:
            print(f"[{self.name}] Cannot wave while DISABLED")
            return

        self.state = FrankaState.WAVING
        pickup_pose = self.franka.get_world_pose()
        pickup_pos = np.array(pickup_pose[0])
        self._pickup = (pickup_pos[0], pickup_pos[1] + 0.25, pickup_pos[2] + 1.5)
        self._place = (pickup_pos[0], pickup_pos[1] - 0.25, pickup_pos[2] + 1.5)
        self.arm_controller.reset()
        self.pick_n_place = 10
        self.placed = False
        self.waving_complete = False
        print(f"[{self.name}] Transitioning to WAVING state")

    def go_home(self):
        if self.state == FrankaState.DISABLED:
            print(f"[{self.name}] Cannot go home while DISABLED")
            return
        self.state = FrankaState.IDLE
        self.franka_home.reset()
        print(f"[{self.name}] Transitioning to IDLE")

    def getLocation(self):
        pickup_pose = self.franka.get_world_pose()
        return np.array(pickup_pose[0])

    def physics_step(self):
        if self.state == FrankaState.IDLE:
            if self.moving_to_idle:
                if self.franka_home.is_done():
                    print(f"[{self.name}] Reached IDLE pose")
                    self.moving_to_idle = False
                    self.pick_n_place = -1
                else:
                    actions = self.franka_home.forward()
                    self.franka.apply_action(actions)

            elif self.pick_n_place == 0 and self._pickup and self._place:
                if self.arm_controller.is_done():
                    if not self.placed:
                        self.placed = True
                    if self.franka_home.is_done():
                        print(f"[{self.name}] Pick-and-place done")
                        self.franka_home.reset()
                        self.pick_n_place = -1
                    else:
                        actions = self.franka_home.forward()
                        self.franka.apply_action(actions)
                else:
                    current_joints = self.franka.get_joint_positions()
                    actions = self.arm_controller.forward(
                        picking_position=self._pickup,
                        placing_position=self._place,
                        current_joint_positions=current_joints,
                    )
                    self.franka.apply_action(actions)

            elif self.pick_n_place > 0:
                self.pick_n_place -= 1
                if self.pick_n_place == 0:
                    print(f"[{self.name}] Starting pick-and-place")

        elif self.state == FrankaState.DISABLED:
            if self.pick_n_place > 0:
                self.pick_n_place -= 1
                if self.pick_n_place == 0:
                    print(f"[{self.name}] Moving to DISABLED pose")
                    self.franka_move.reset()
                    self.moving_to_disabled = True
            elif self.moving_to_disabled:
                if self.franka_move.is_done():
                    print(f"[{self.name}] Reached DISABLED pose")
                    self.moving_to_disabled = False
                    self.pick_n_place = -1
                else:
                    actions = self.franka_move.forward()
                    self.franka.apply_action(actions)

        elif self.state == FrankaState.WAVING:
            if self.pick_n_place > 0:
                self.pick_n_place -= 1
                if self.pick_n_place == 0:
                    print(f"[{self.name}] Start waving")
                    self.arm_controller.reset()
            elif self.pick_n_place == 0:
                if not self.waving_complete:
                    if self.arm_controller.is_done():
                        self.waving_complete = True
                        self.franka_home.reset()
                        print(f"[{self.name}] Waving done, going home")
                    else:
                        current_joints = self.franka.get_joint_positions()
                        actions = self.arm_controller.forward(
                            picking_position=self._pickup,
                            placing_position=self._place,
                            current_joint_positions=current_joints,
                        )
                        self.franka.apply_action(actions)
                else:
                    if self.franka_home.is_done():
                        print(f"[{self.name}] Homing complete, back to IDLE")
                        self.state = FrankaState.IDLE
                        self.waving_complete = False
                        self.franka_home.reset()
                    else:
                        actions = self.franka_home.forward()
                        self.franka.apply_action(actions)

    def is_done(self):
        return self.placed

    def post_reset(self):
        self.arm_controller.reset()
        self.franka.gripper.set_joint_positions(
            self.franka.gripper.joint_opened_positions
        )
        self.pick_n_place = -1
        self.state = FrankaState.IDLE
        self.waving_complete = False
        self.moving_to_disabled = False
        self.moving_to_idle = False
