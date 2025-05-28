from paranet_agent import actor, connector
from paranet_agent.actor import BaseActor, Conversation


@actor.input
class pickplacelocation:
  pickup: float
  place: float

@actor.type
class TaskStatus:
  status: str

@actor.actor(name='franka')
class universalArm(BaseActor):
    status: str = "Stopped"
    robot: object

    @actor.skill(subject="franka", response=TaskStatus)
    def pickUpandPlace(self, conv: Conversation) -> None:
        self.robot.set_command()
        self.status = "Moving"
        conv.send_response(TaskStatus(status=self.status))

    # Registers this actor instance with the SDK
    def register(self):
       actor.register_actor(self)