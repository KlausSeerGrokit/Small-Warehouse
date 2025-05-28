import os
import sys

import asyncio
from typing import Optional
from paranet_agent import actor
from paranet_agent.actor import BaseActor, Conversation
from enum import Enum
import math

# Need spot to:
    # Discover if franka arm is disabled
    # Move from idle state to moving state to inspect franka
        # Communicate that it will be inspecting
    # Reach target destination based on (x,y) coordinates
    # Enable the franka arm
        # Communicate that task is complete
    # Return to home position

# Define the states for the Franka robot
class SpotState(Enum):
    IDLE_STATE = "idle"                 # Home position
    INSPECTION_STATE = "inspecting"     # Inspecting incident
    COMPLETION_STATE = "task completed" # Completion of task

# Position class: represents input data for actor
@actor.input
class Position:
    x: int
    y: int

# Target class: represents target position
@actor.type
class Target:
    x: int
    y: int

# Task Status class: represents the status of spot
@actor.type
class SpotTaskStatus:
    status: str

# Distance class: represents distance
@actor.type
class DistanceResult:
    distance: float

# Creates and registers actor
def create_spot_instance(id, robot, sim=None):
    # Actor class definition
    @actor.actor(name=id, subject="spot")
    class SpotPhy(BaseActor):
        id: str
        robot: object
        sim: object
        target: list[int] = None
        conversation: Conversation = None
        state: SpotState = SpotState.IDLE_STATE

        # Moves robot to target postion, called when Franka is disabled
        @actor.skill(id="spot@1.0.0", response=SpotTaskStatus)
        def goto(self, x: int, y: int, conversation: Conversation) -> None:
            asyncio.ensure_future(self.run_goto(x, y, conversation))

        # Actual function for the goto task
        async def run_goto(self, x: int, y: int, conversation: Conversation):
            if self.state == SpotState.IDLE_STATE:
                # Starts the inspection phase
                self.state = SpotState.INSPECTION_STATE
                self.target = [x, y]
                self.conversation = conversation
                # Function in spot_isaac, triggers call back for completion 
                self.robot.run_nav(self.target, self)
                conversation.send_response(SpotTaskStatus(status=self.state.value))
            else:
                conversation.send_response(SpotTaskStatus(status=self.state.value))

        # Returns current position of the robot
        @actor.skill(id="spot@1.0.0", response=Target)
        def get_position(self, conversation: Conversation) -> Target:
            pos = self.robot.get_loc()
            return Target(x=pos[0], y=pos[1])
        
        # Returns the current state
        @actor.skill(id="spot@1.0.0", response=SpotTaskStatus)
        def get_state(self) -> SpotTaskStatus:
            return SpotTaskStatus(status=self.state.value)
        
        # Returns current target coordinates
        @actor.skill(id="spot@1.0.0", response=Target)
        def get_target(self) -> Target:
            return Target(x=self.target[0], y=self.target[1])
        
        # Returns the distance away from target to decide which spot to send
        @actor.skill(id="spot@1.0.0", response=DistanceResult)
        def inspection_distance(self, x: float, y: float) -> DistanceResult:
            dist = self.robot.get_distance((x, y))
            return DistanceResult(distance=dist)

        # Callback from robot when action complete
        def __call__(self):
            if self.state == SpotState.INSPECTION_STATE:
                # Arrive to target position for inspection and enable franka
                actor.send("<franka_id>", "enable") # IDK, comms with franka??
                # Inspection completed
                if self.conversation:
                    self.conversation.send_response(SpotTaskStatus(status=SpotState.COMPLETION_STATE.value))
                # Return to home position
                self.state = SpotState.COMPLETION_STATE
                self.robot.run_nav(self.robot.drop_loc, self)
                return
            # If back at home state
            if self.state == SpotState.COMPLETION_STATE:
                # Back to home position, go back to idle state
                self.state = SpotState.IDLE_STATE
                if self.conversation:
                    self.conversation.send_response(SpotTaskStatus(status=self.state.value))
                    self.conversation = None
                
        def register(self):
            actor.register_actor(self)

    return SpotPhy(robot=robot, id=id, sim=sim)


async def delay(ms, callback):
    await asyncio.sleep(ms / 1000)
    callback()
            