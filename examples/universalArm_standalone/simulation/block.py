# import numpy as np
# from omni.isaac.core.utils.prims import create_prim
# from omni.isaac.core.prims import RigidPrim

# class Block:
#     def __init__(self, position, size=(0.05, 0.05, 0.05), name="block"):
#         # Set the initial properties of the block
#         self.position = np.array(position)
#         self.size = size
#         self.name = name

#         prim_path = f"/World/{name}"
#         create_prim(prim_path, "Cube")
        
#         # Create the block in the scene using RigidPrim
#         self.prim = RigidPrim(
#             prim_path=f"/World/{self.name}",
#             name=self.name,
#             position=self.position,
#             scale=self.size
#         )
#     def initialize(self):
#         self.prim.initialize()

#     def get_position(self):
#         return self.position

#     def get_size(self):
#         return self.size

import omni.usd
from omni.isaac.core.utils.prims import create_prim
from omni.isaac.core.prims import RigidPrim
from pxr import UsdPhysics, UsdGeom, Gf

class Block:
    def __init__(self, position, size=(0.05, 0.05, 0.05), name="pickup_block"):
        prim_path = f"/World/{name}"

        # Create the cube
        create_prim(prim_path, "Cube")

        # Add rigid body and collision via USD API
        stage = omni.usd.get_context().get_stage()
        prim = stage.GetPrimAtPath(prim_path)

        # Enable physics
        UsdPhysics.RigidBodyAPI.Apply(prim)
        UsdPhysics.CollisionAPI.Apply(prim)

        # Optional: Add mass (can be omitted if not needed)
        rigid_body = UsdPhysics.RigidBodyAPI(prim)
        # Omit mass if not needed or set with the proper method if necessary
        # rigid_body.SetMass(1.0)

        # Scale the block to the desired size
        xform_api = UsdGeom.XformCommonAPI(prim)
        xform_api.SetScale(Gf.Vec3f(size[0], size[1], size[2]))

        # Now wrap with RigidPrim
        self.prim = RigidPrim(
            prim_path=prim_path,
            name=name,
            position=position,
            scale=size
        )
