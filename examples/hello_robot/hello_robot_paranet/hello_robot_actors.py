import os
from paranet_agent import actor, connector
from paranet_agent.actor import BaseActor, Conversation

@actor.type
class TaskStatus:
    status: str

@actor.type
class RobotPosition:
    position: str

@actor.actor
class HelloRobot(BaseActor):
    def __init__(self, sim: "HelloWorld"):  # Use a string type hint to avoid circular import
        super().__init__()
        self.sim = sim
        self.demo_status_options = ['waiting', 'running', 'stopped', 'failed']

    def update_status(self, new_status):
        if new_status in self.demo_status_options:
            self.sim.current_status = new_status
        else:
            self.sim.current_status = "failed"

    @actor.skill(subject='hello_robot', response=TaskStatus)
    async def start(self, conv: Conversation) -> None:
        try:
            await self.sim._world.play_async()
            self.update_status("running")
            conv.send_response(TaskStatus(status=self.sim.current_status))
        except Exception as e:
            self.update_status("failed")
            conv.send_response(TaskStatus(status=f"{self.sim.current_status}: {str(e)}"))

    @actor.skill(subject='hello_robot', response=TaskStatus)
    def ping(self, conv: Conversation) -> None:
        """Retrieve current status of the demo."""
        conv.send_response(TaskStatus(status=self.sim.current_status))

    @actor.skill(subject='hello_robot', response=RobotPosition)
    def get_position(self, conv: Conversation) -> None:
        robo_pos, _ = self.sim._jetbot.get_world_pose()
        conv.send_response(RobotPosition(position=str(robo_pos))) 


def setup_actors(sim):
    """Handles actor registration separately for clarity."""
    print("Starting Paranet Connector...")
    # os.environ['PARAFLOW_HOST'] = "http://localhost:3030"
    connector.start(3000)
    print("Registering HelloRobot Actor...")
    hello_robot = HelloRobot(sim=sim)
    actor.register_actor(hello_robot)
    actor.deploy('isaac', restart=False)
    print("Actor successfully deployed.")

def cleanup():
    connector.stop()
