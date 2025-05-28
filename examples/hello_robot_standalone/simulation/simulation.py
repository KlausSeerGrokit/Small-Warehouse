import numpy as np

from actors.jetbot import Jetbot
from simulation.jetbot_sim import JetbotSim

#### Create a main simulation class to create the scene and create instances of your robot classes

class Simulation:
  def __init__(self, world):
    self._world = world

  # Sets up the scene with USD objects
  def setup_scene(self):
    # Need to create a ground plane if not loading a USD scene
    self._world.scene.add_default_ground_plane()

    self._jetbot = JetbotSim()

  async def setup_post_load(self):
      # robot initialization needs to be done in post load
      self._jetbot.initialize()

      # create and register actors
      self._jetbot_actor = Jetbot(robot=self._jetbot) # Entry point here
      self._jetbot_actor.register()
  
      self._world.add_physics_callback("sim_step", callback_fn=self.physics_step)

  # Called each time step, update each of your robots
  def physics_step(self, step_size):
    self._jetbot.physics_step(step_size)