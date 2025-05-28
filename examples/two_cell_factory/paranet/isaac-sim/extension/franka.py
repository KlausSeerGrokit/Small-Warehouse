from omni.isaac.franka.controllers import PickPlaceController, RMPFlowController

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

class FrankaSim:
    def __init__(self, name, franka, sim, target):
        self.name = name
        self.sim = sim
        self.target = target
        self.pick_n_place = -1
        self.placed = False

        self.franka = franka
        self.arm_controller = PickPlaceController(
            name="pick_place_controller",
            gripper=self.franka.gripper,
            robot_articulation=self.franka,
            end_effector_initial_height=1.0,
        )
        self.franka.gripper.set_joint_positions(self.franka.gripper.joint_opened_positions)
        self.franka_home = FrankaHoming(self.franka)

    def place_block(self, callback):
        self.callback = callback
        self.pick_n_place = 10
        self.placed = False

    def physics_step(self):
        if self.pick_n_place == 0:
            if self.arm_controller.is_done():
                if not self.placed:
                    self.placed = True
                    if self.callback:
                        self.callback('done')
                        self.callback = None
                if self.franka_home.is_done():
                    print("f[{self.name}] End pick-n-place")
                    self.franka_home.reset()
                    self.pick_n_place = -1
                else:
                    actions = self.franka_home.forward()
                    self.franka.apply_action(actions)
            else:
                cube_position, _ = self.sim.get_cube().get_world_pose()
                current_joint_positions = self.franka.get_joint_positions()
                actions = self.arm_controller.forward(
                    picking_position=cube_position,
                    placing_position=self.target,
                    current_joint_positions=current_joint_positions,
                )
                self.franka.apply_action(actions)
        elif self.pick_n_place > 0:
            self.pick_n_place -= 1
            if self.pick_n_place == 0:
                print("f[{self.name}] Start pick-n-place")

    def is_done(self):
        return self.placed

    def post_reset(self):
        self.arm_controller.reset()
        self.franka.gripper.set_joint_positions(self.franka.gripper.joint_opened_positions)
        self.pick_n_place = -1
