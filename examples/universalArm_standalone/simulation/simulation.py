import numpy as np
from actors.universalArm import universalArm
from simulation.block import Block
from simulation.universalArm_sim import universalArmSim

#### Create a main simulation class to create the scene and create instances of your robot classes

class Simulation:
  def __init__(self, world):
    self._world = world

  # Sets up the scene with USD objects
  def setup_scene(self):
    # Need to create a ground plane if not loading a USD scene
    self._world.scene.add_default_ground_plane()
    self.arm = universalArmSim()
    self.block = Block(position=[1, 1.5, 0.1], size=(0.05, 0.05, 0.05), name="pickup_block") #sets the block's position and size
    self.arm.assign_block(self.block)

  async def setup_post_load(self):
      # robot initialization needs to be done in post load
      self.arm.initialize()
      #self.block.initialize()

      # create and register actors
      self.franka_actor = universalArm(robot=self.arm)
      self.franka_actor.register() #connects to paranet
  
      self._world.add_physics_callback("sim_step", callback_fn=self.physics_step)

  # Called each time step, update each of your robots
  def physics_step(self, step_size):
    self.arm.physics_step(step_size)