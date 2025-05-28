import os

from omni.isaac.examples.base_sample import BaseSampleExtension
from omni.isaac.examples.user_examples import HumanoidExample


class UserExampleExtension(BaseSampleExtension):
    def on_startup(self, ext_id: str):
        super().on_startup(ext_id)
        super().start_extension(
            menu_name="CES Demo",
            submenu_name="",
            name="CES Demo",
            title="CES Demo",
            doc_link="",
            overview="CES",
            file_path=os.path.abspath(__file__),
            sample=HumanoidExample(),
        )
        print("USER EXAMPLE STARTUP")
        return

    def shutdown_cleanup(self):
        print("USER EXAMPLE CLEANUP")
