from paranet_agent import actor
from paranet_agent.actor import BaseActor, Conversation


@actor.type
class FrankaStatus:
    status: str


@actor.type
class Location:
    row: float
    col: float


def create_franka_instance(id, robot, sim=None):
    @actor.actor(name=id, subject="franka")
    class FrankaPhy(BaseActor):
        id: str
        robot: object
        sim: object
        conversation: Conversation = None

        @actor.skill(id="franka@1.0.0")
        def wave(self) -> FrankaStatus:
            self.robot.wave()
            return FrankaStatus(status="waving")

        @actor.skill(id="franka@1.0.0")
        def getLocation(self) -> Location:
            pos = self.robot.getLocation()
            return Location(row=pos[0], col=pos[1])

        @actor.skill(id="franka@1.0.0")
        def disable(self) -> FrankaStatus:
            self.robot.disable()
            return FrankaStatus(status="disabled")

        @actor.skill(id="franka@1.0.0")
        def enable(self) -> FrankaStatus:
            self.robot.enable()
            return FrankaStatus(status="enabled")

        @actor.skill(id="franka@1.0.0")
        def status(self) -> FrankaStatus:
            return FrankaStatus(status="idle")

        def register(self):
            actor.register_actor(self)

    return FrankaPhy(robot=robot, id=id, sim=sim)
