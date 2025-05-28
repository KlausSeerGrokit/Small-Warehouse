import asyncio
from paranet_agent import actor, connector
from paranet_agent.actor import BaseActor, Conversation

@actor.type
class TaskStatus:
    status: str

@actor.type
class BeltStatus:
    condition: str

@actor.broadcast(subject='workcell',action='sos')
class SosMsg:
    cell: int
    message: str

@actor.actor
class Isaac_H1(BaseActor):
    cells: object
    h1s: object

    def __post_init__(self):
        for i,h1 in enumerate(self.h1s):
            h1.add_listener(self, i)

    @actor.skill(subject='h1', response=TaskStatus, instance_param='cell')
    def put_widget(self, cell: int, conv: Conversation) -> None:
        # auto-reset scene
        self.cells[cell-1].reset_cell()
        self.cells[cell-1].set_lights(green=True)

        print(f"[{self.h1s[cell-1].name}] Request: put widget")
        self.h1s[cell-1].place_block(lambda status: conv.send_response(TaskStatus(status=status)))

    def handle_event(self, cell, event, message):
        if event == 'sos':
            print('BROADCAST SOS')
            self.send_broadcast(SosMsg(cell=1+cell,message=message))


@actor.actor
class Isaac_UR5(BaseActor):
    ur5s: object

    @actor.skill(subject='ur_arm', response=TaskStatus, instance_param='cell')
    def fill_tote(self, cell: int, conv: Conversation) -> None:
        print(f"[{self.ur5s[cell-1].name}] Request: place widget")
        self.ur5s[cell-1].place_block(lambda status: conv.send_response(TaskStatus(status=status)))

@actor.actor
class Isaac_ConveyorBelt(BaseActor):
    belts: object

    @actor.skill(subject='belt', response=BeltStatus, instance_param='cell')
    def move_check_tote(self, cell: int, message: str, conv: Conversation) -> None:
        print(f"[{self.belts[cell-1].name}] Request: check tote {message}")
        self.belts[cell-1].check_tote(lambda condition: conv.send_response(BeltStatus(condition=condition)))

@actor.actor
class Isaac_Digit(BaseActor):
    digits: object

    @actor.skill(subject='phy_digit', response=TaskStatus, instance_param='cell')
    def pickup_tote(self, cell: int, conv: Conversation) -> None:
        print(f"[{self.digits[cell-1].name}] Request: pickup tote")
        self.digits[cell-1].get_tote(lambda status: conv.send_response(TaskStatus(status=status)))

    @actor.skill(subject='phy_digit', response=TaskStatus, instance_param='cell')
    def place_tote(self, cell: int, target: str, conv: Conversation) -> None:
        print(f"[{self.digits[cell-1].name}] Request: place tote {target}")
        self.digits[cell-1].place_tote(target, lambda status: conv.send_response(TaskStatus(status=status)))

    @actor.skill(subject='phy_digit', instance_param='cell')
    def fall(self, cell: int) -> TaskStatus:
        self.digits[cell-1].fall()
        return TaskStatus(status='done')

async def do_something(conv, resp):
    await asyncio.sleep(3)
    conv.send_response(resp)

def start_actors(cells, h1s, ur5s, belts, digits):
    connector.start()
    actor.register_actor(Isaac_H1(h1s=h1s, cells=cells),broadcast=[SosMsg])
    actor.register_actor(Isaac_UR5(ur5s=ur5s),broadcast=[SosMsg])
    actor.register_actor(Isaac_ConveyorBelt(belts=belts),broadcast=[SosMsg])
    actor.register_actor(Isaac_Digit(digits=digits),broadcast=[SosMsg])
    actor.deploy('isaac', restart=False)
    print('ACTORS started')

def stop_actors():
    connector.stop()
    print('ACTORS stopped')
