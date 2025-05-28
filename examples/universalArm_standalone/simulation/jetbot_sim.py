import numpy as np
from omni.isaac.core.utils.nucleus import get_assets_root_path
from omni.isaac.wheeled_robots.controllers.differential_controller import DifferentialController
from omni.isaac.wheeled_robots.robots import WheeledRobot

class JetbotSim:
    """
    Creates and manages an instance of a Jetbot style robot.
    Usage:
        demo_jetbot = JetbotSim()
    Alternative usage:
        jetbot = JetbotSim(position=np.array([1.0, 0.5, 0.1]))
        or
        jetbot = JetbotSim(name="second_jetbot", prim_path="/World/SecondJetbot")
    Alternative usage:
        custom_robot = WheeledRobot(...)  # with different parameters
        demo_jetbot = JetbotSim(robot=custom_robot)
    """
    def __init__(self, robot=None, **robot_kwargs):
        if robot is None:
            # Set default USD path and position, allow override via kwargs
            defaults = {
                "prim_path": "/World/Jetbot",
                "name": "my_jetbot",
                "wheel_dof_names": ["left_wheel_joint", "right_wheel_joint"],
                "create_robot": True,
                "usd_path": get_assets_root_path() + "/Isaac/Robots/Jetbot/jetbot.usd",
                "position": np.array([0.0, 0.0, 0.1]),
            }
            defaults.update(robot_kwargs)
            robot = WheeledRobot(**defaults)

        self._robot = robot
        self._controller = DifferentialController(name="simple_control", wheel_radius=0.03, wheel_base=0.1125)
        self._command = np.array([0.0, 0.0])
    
    def initialize(self):
        self._robot.initialize()

    def physics_step(self, step_size):
        self._robot.apply_wheel_actions(self._controller.forward(self._command))

    def set_command(self, cmd):
        self._command = np.array(cmd)
