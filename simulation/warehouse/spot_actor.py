import asyncio
from paranet_agent import actor
from paranet_agent.actor import BaseActor, Conversation

IDLE_STATE = "idle"
MOVING_STATE = "moving"


@actor.input
class Position:
    x: int
    y: int


@actor.type
class Target:
    x: int
    y: int


@actor.type
class SpotTaskStatus:
    status: str


@actor.type
class DistanceResult:
    distance: float


def create_spot_instance(id, robot, sim=None):
    @actor.actor(name=id, subject="spot")
    class SpotPhy(BaseActor):
        id: str
        robot: object
        sim: object
        target: list[int] = None
        conversation: Conversation = None
        state: str = IDLE_STATE

        @actor.skill(id="spot@1.0.0", response=SpotTaskStatus)
        def goto(self, x: int, y: int, conversation: Conversation) -> None:
            asyncio.ensure_future(self.run_goto(x, y, conversation))

        async def run_goto(self, x: int, y: int, conversation: Conversation):
            if self.state == IDLE_STATE:
                self.state = MOVING_STATE
                self.target = [x, y]
                self.conversation = conversation
                self.robot.run_nav(self.target, self)
            else:
                conversation.send_response(SpotTaskStatus(status=self.state))

        @actor.skill(id="spot@1.0.0")
        def get_position(self, conversation: Conversation) -> Target:
            pos = self.robot.get_loc()
            return Target(x=pos[0], y=pos[1])

        @actor.skill(id="spot@1.0.0")
        def get_state(self) -> SpotTaskStatus:
            return SpotTaskStatus(status=self.state)

        @actor.skill(id="spot@1.0.0")
        def get_target(self) -> Target:
            return Target(x=self.target[0], y=self.target[1])

        def __call__(self):
            print("GOTO COMPLETE FOR", self.conversation)
            self.state = IDLE_STATE
            if self.conversation:
                self.conversation.send_response(SpotTaskStatus(status=self.state))
                self.conversation = None

        def register(self):
            actor.register_actor(self)

    return SpotPhy(robot=robot, id=id, sim=sim)
