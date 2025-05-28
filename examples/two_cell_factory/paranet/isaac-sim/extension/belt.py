import omni
import numpy as np

class BeltCamera:
    def __init__(self, position):
        self.position = position

    def detect(self, obj):
        pos, _ = obj.get_world_pose()
        if pos[0] > self.position[0]:
            return 'good'

class BeltSim:
    def __init__(self, root_path, name, sim):
        self.root_path = root_path
        self.name = name
        self.sim = sim
        self.camera = BeltCamera(np.array([4.2, 0, 1]))
        self.belt_on = False
        self.checked = False

    def set_belt_velocity(self, vel):
        stage = omni.usd.get_context().get_stage()
        for name in ['ConveyorTrack','ConveyorTrack_01']:
            belt = stage.GetPrimAtPath(f"{self.root_path}/Robots/{name}/ConveyorBeltGraph")
            velocity_attr = belt.GetAttribute("graph:variable:Velocity")
            velocity_attr.Set(vel)
        print(f"[{self.name}] Velocity {vel}")

    def initialize(self):
        self.set_belt_velocity(0.0)

    def check_tote(self, callback):
        self.callback = callback
        self.set_belt_velocity(1.0)
        self.belt_on = True

    def physics_step(self):
        if self.belt_on:
            if self.camera.detect(self.sim.get_cube()):
                self.set_belt_velocity(0.0)
                self.belt_on = False
                self.checked = True
                if self.callback:
                    self.callback(self.sim._trial_outcome)
                    self.callback = None

    def is_done(self):
        return self.checked