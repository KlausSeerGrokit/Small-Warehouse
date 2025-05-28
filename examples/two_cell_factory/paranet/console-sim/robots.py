import asyncio
from paranet_agent import actor, connector
from paranet_agent.actor import BaseActor, Conversation


#### Skill response type of action skills

@actor.type
class TaskStatus:
    status: str


#### Actor

@actor.actor
class SimRobots(BaseActor):
    @actor.skill(subject='ur_arm_phy', response=TaskStatus)
    def fill_tote(self, conv: Conversation) -> None:
        asyncio.ensure_future(self.sim_fill_tote(conv))

    @actor.skill(subject='digit_phy', response=TaskStatus)
    def stage_tote(self, target: str, conv: Conversation) -> None:
        asyncio.ensure_future(self.sim_stage_tote(target, conv))

    async def sim_fill_tote(self, conv):
        print(f'UR: fill tote')
        await asyncio.sleep(1)

        print(f'UR: done')
        conv.send_response(TaskStatus(status='done'))

    async def sim_stage_tote(self, target, conv):
        print(f'Digit: stage tote to {target}')
        await asyncio.sleep(1)

        print(f'Digit: done')
        conv.send_response(TaskStatus(status='done'))


####################

connector.start(8083)
actor.register_actor(SimRobots())

actor.deploy('robots', restart=False)

loop = asyncio.events.get_event_loop()
loop.run_until_complete(connector.get_task())
