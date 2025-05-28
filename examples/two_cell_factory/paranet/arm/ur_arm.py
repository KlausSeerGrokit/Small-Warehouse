import sys
sys.path.append('./plc4py')

import logging
import asyncio
import os

from paranet_agent import actor, connector
from paranet_agent.actor import BaseActor, Conversation


logging.basicConfig(level=logging.INFO)

from plc4py.PlcDriverManager import PlcDriverManager
from plc4py.spi.values.PlcValues import PlcBOOL, PlcINT

modbus = os.environ['MODBUS_HOST']
port = os.environ.get('MODBUS_PORT', '502')
if not modbus:
    exit(1)

connection_string = f"modbus://{modbus}:{port}"
print(f"Connecting to {connection_string}")
driver_manager = PlcDriverManager()

@actor.type
class TaskStatus:
    status: str

@actor.actor
class UrArmActor(BaseActor):
    @actor.skill(subject='ur_arm_phy', response=TaskStatus)
    def fill_tote(self, conv: Conversation) -> None:
        # asyncio.ensure_future(self.run_all(conv))
        asyncio.ensure_future(self.run_all(conv))

    async def run_all(self, conv: Conversation):
        await run_all()
        conv.send_response(TaskStatus(status='done'))

    @actor.skill(subject='ur_arm_phy', response=TaskStatus)
    def halt(self, conv: Conversation) -> None:
        asyncio.ensure_future(self.halt_arm(conv))

    async def halt_arm(self, conv: Conversation):
        await writeaddr(130, 99)
        conv.send_response(TaskStatus(status='done'))
    
    @actor.skill(subject='ur_arm_phy', response=TaskStatus)
    def getstatus(self, conv: Conversation) -> None:
        asyncio.ensure_future(self.run_status(conv))

    async def run_status(self, conv: Conversation):
        statuses = ["disconnected", "confirm_safety", "booting", "power_off", "power_on", "idle", "backdrive", "running"]
        status = await readaddr(258)
        conv.send_response(TaskStatus(status=statuses[status]))

    @actor.skill(subject='ur_arm_phy', response=TaskStatus)
    def readaddr(self, addr: int, conv: Conversation) -> None:
        asyncio.ensure_future(self.run_readaddr(addr, conv))

    async def run_readaddr(self, addr: int, conv: Conversation) -> None:
        reg = await readaddr(addr)
        conv.send_response(TaskStatus(status=f"{reg}"))


async def readaddr(addr):
    async with driver_manager.connection(connection_string) as connection:
        with connection.read_request_builder() as builder:
            builder.add_item("rd", "4x%05d" % (1+addr,))
            request = builder.build()
        response = await connection.execute(request)
        print(f"Response code: {response.response_code}")
        item = response.get_plc_value('rd')
        # print(addr,item)
        return item.get_int()

async def readaddr_n(addr, n):
    async with driver_manager.connection(connection_string) as connection:
        with connection.read_request_builder() as builder:
            builder.add_item("rd", "4x%05d[%d]" % (1+addr,n))
            request = builder.build()
        response = await connection.execute(request)
        # print(f"Response code: {response.response_code}")
        items = response.get_plc_value('rd').get_list()

        # print("ITEMS", response.get_plc_value('rd').get_list());
        if (hasattr(items, '__iter__')):
            lst = [item for item in response.get_plc_value('rd').get_list()]        
        else:
            lst = [items]

        # print(addr,lst)
        return lst

async def writeaddr(addr, n):
    async with driver_manager.connection(connection_string) as connection:
        with connection.write_request_builder() as builder:
            builder.add_item("ctrl", "4x%05d" % (1+addr,), PlcINT(n))
            request = builder.build()
        response = await connection.execute(request)
        print(f"Response code: {response.response_code}")

async def last_action():
    return await readaddr(129)

async def run_action(action):
    state = await readaddr_n(129, action)

    print("ACTION", action)
    print("START STATE", state)

    # if state[0] != 0:
    #     raise Exception('bad state')

    await writeaddr(128, action)
    await asyncio.sleep(0.5)
    await writeaddr(128, 0)

    while True:
        await asyncio.sleep(1)
        cur = await readaddr(129)
        print("   WAITING ", action, "")
        if cur == action:
            break

    print('action done', action)

async def check_pose():
    print(await readaddr_n(270, 5))

async def check_analog():
    first = await readaddr_n(16, 2)
    second = await readaddr_n(18, 2)
    print(first)
    print(second)

async def run_all():
    await run_action(1)
    await run_action(2)
    await run_action(3)

async def full_run():
    last = await last_action()
    print("LAST ACTION", last)
    if last == 3:
        last = 0
    while last < 3:
        next = last + 1
        print("NEXT ACTION", next)
        await run_action(next)
        last = await last_action()

# asyncio.run(run_all())

connector.start(8083)
actor.register_actor(UrArmActor())

actor.deploy('sim', restart=False)

loop = asyncio.events.get_event_loop()
loop.run_until_complete(connector.get_task())
