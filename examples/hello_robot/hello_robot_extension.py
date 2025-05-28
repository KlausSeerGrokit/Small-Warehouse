import os

from omni.isaac.examples.base_sample import BaseSampleExtension
from omni.isaac.examples.user_examples.hello_robot_paranet.hello_robot import HelloWorld

class HelloRobotExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="",
            submenu_name="",
            name="Hello Robot",
            title="Hello Robot Example",
            doc_link="https://docs.omniverse.nvidia.com/isaacsim/latest/core_api_tutorials/tutorial_core_hello_world.html",
            overview="This Example introduces the user on how to do cool stuff with Isaac Sim through scripting in asynchronous mode. The demo is extended via Paranet actorization with several basic skills.",
            file_path=os.path.abspath(__file__),
            sample=HelloWorld(),
        )
        return
