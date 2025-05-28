import numpy as np
from simulation.block import Block
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.manipulators import SingleManipulator
from omni.isaac.manipulators.grippers import ParallelGripper
from omni.isaac.franka.controllers import PickPlaceController
from omni.isaac.core.utils.stage import add_reference_to_stage
from omni.isaac.core.prims import RigidPrim

class universalArmSim: #spawns the robot
    def __init__(self, robot=None, **robot_kwargs):
        if robot is None:
            usd_path = get_assets_root_path() + "/Isaac/Robots/Franka/franka.usd"
            prim_path = "/World/Franka"

            add_reference_to_stage(usd_path, prim_path)

            gripper = ParallelGripper(
                end_effector_prim_path="/World/Franka/panda_hand",
                joint_prim_names=["panda_finger_joint1", "panda_finger_joint2"],
                joint_opened_positions=[0.04, 0.04],
                joint_closed_positions=[0.0, 0.0]
            )

            robot = SingleManipulator(
                prim_path=prim_path,
                name="my_franka",
                position=np.array([0.0, 0.0, 0.0]),
                end_effector_prim_name="panda_hand",
                gripper=gripper,
            )

        self._robot = robot
        self._controller = PickPlaceController(
            name="franka_pick_place",
            robot_articulation=self._robot,
            gripper=self._robot.gripper
        )
        self._target_pose = None
        self._pickup = None
        self._place = None
        self._current_command = "idle"

    def initialize(self):
        self._robot.initialize()

    def assign_block(self, block):
        """Assigns a block object to be picked up."""
        self._block = block
        self._pickup = block.prim.get_world_pose()[0]  # get position

    def physics_step(self, step_size):
        # Ensure pickup and place positions are valid
        if self._pickup is None or self._place is None:
            return 
        current_joint_positions = self._robot.get_joint_positions()
        actions = self._controller.forward(
            picking_position=self._pickup,
            placing_position=self._place,
            current_joint_positions=current_joint_positions
        )
        self._robot.apply_action(actions)

    
    def set_command(self):
        self._pickup = np.array(self._block.get_position()) #block's location feature
        self._place = np.array([4.0,4.0,0]) #place block wherever

#   def set_command(self, block: Block, place: np.ndarray):
#         self._pickup = np.array(pick) #block's location feature
#         self._place = np.array(place) #place block wherever
