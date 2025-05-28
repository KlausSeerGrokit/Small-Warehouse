import os
import asyncio
import requests
from paranet_agent import actor, connector
from paranet_agent.actor import BaseActor, Conversation

ar_skill_server = os.environ.get('AR_SERVER_ENDPOINT', "http://54.202.102.142:5000")

# Skill response type for action skills
@actor.type
class TaskStatus:
    status: str

# SimDigit Actor
@actor.actor
class SimDigit(BaseActor):
    @actor.skill(subject='digit_phy', response=TaskStatus)
    def stage_tote(self, target: str, conv: Conversation) -> None:
        asyncio.ensure_future(self.sim_stage_tote(target, conv))

    async def sim_stage_tote(self, target, conv):
        print("SimDigit: Starting stage tote operation...")
        await asyncio.to_thread(self.sim_pick)  # Call pick operation
        await asyncio.to_thread(self.sim_place, target)  # Call place operation
        print("SimDigit: Stage tote operation complete")
        conv.send_response(TaskStatus(status='done'))
    
    def sim_pick(self):
        print("SimDigit: Sending request to pick tote...")
        route = f"{ar_skill_server}/ces/pick"
        response = requests.post(
            route,
            json={
                "stand_distance": 0.38,
                "grasp_depth_factor": 2
                }
        )
        if response.status_code == 200:
            print("SimDigit: Pick complete")
        else:
            print(f"SimDigit: Pick failed with status {response.status_code}")

    def sim_place(self, target):
        print(f"SimDigit: Sending request to place tote at {target}...")
        route = f"{ar_skill_server}/ces/place"
        response = requests.post(
            route,
            json={
                "drop_off_location": target,
                # "stand_distance": 0.45,
                # "place_depth_offset": 0,
                # "hold_buffer": 0.25,
                # "max_walking_speed": {
                #                     "vx": 0.8,
                #                     "vy": 0.5,
                #                     "wz": 1.0
                #                     }
                }
        )
        if response.status_code == 200:
            print(f"SimDigit: Placed tote at {target}")
        else:
            print(f"SimDigit: Place failed with status {response.status_code}")


# Start the connector and register the actor
connector.start(8088)
actor.register_actor(SimDigit())
actor.deploy('sim', restart=False)

loop = asyncio.events.get_event_loop()
loop.run_until_complete(connector.get_task())
