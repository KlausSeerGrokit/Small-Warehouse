https://docs.omniverse.nvidia.com/isaacsim/latest/core_api_tutorials/tutorial_core_hello_robot.html

This demo is a combination of Nvidia's core hello_robot tutorial, and Otonoma's paranet actorization. It lightly manipulates the existing scope of the demo to expose 3 actorized skills:
  1. start demo (Begins the demo.)
  2. get position (Reports the coordinate location of the jet bot.)
  3. ping (Check connectivity to the jet bot.)

Prerequisites:

- Isaac-sim:
    - Complete and understand Nvidia's hello world and hello robot tutorials.
    - Confirm access to the isaac sim user_examples directory. For example, a common/default path on linux is: 
    `~/.local/share/ov/pkg/isaac-sim-4.2.0/exts/omni.isaac.examples/omni/isaac/examples/user_examples/`
        
        
- Otonoma
    - Complete the getting started tasks:
        - https://paranet.otonoma.com/docs/getting-started
        - ensure you can run `para -V` and get a version displayed.
    - Install the python paranet sdk for Isaac-sim. 
        - Download the sdk release <@mike galvin>: `~/Downloads/<SDK.WHL>`

        ```
        cd ~/.local/share/ov/pkg/isaac-sim-4.2.0/ 

        unix: ./python.sh -m pip install ~/Downloads/<SDK.WHL>
        windows: ./python.bat -m pip install ~/Downloads/<SDK.WHL>
        ```
    - Clone the paranet repo. 
    https://github.com/otonoma/paranet

    Version Requirements:
    - Python SDK: v1.4.0 or higher
    - Para: v0.13.0 or higher

- Optional:
    - The VSCode Docker extension is very useful for quickly monitoring and resetting the state of existing containers as you navigate the code of your project.
    https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker


Setup:
1. Navigate to the `paranet/examples/hello_robot` directory. 
2. Copy all working files and directories WITHIN the `hello_robot` directory to the isaac-sim `user_examples` directory. The readme is not required.
    - Result should look like:
        ```
        .
        ├── user_examples
        │   ├── hello_robot_extension.py
        │   ├── hello_robot_paranet
        │   │   ├── hello_robot_actors.py
        │   │   ├── hello_robot.py
        │   │   └── __init__.py
        │   ├── __init__.py
        │   └── paranet.yaml
        ```
    - Note: It is important that an `..._extension.py` file is at the top level within `user_examples`, or else the demo will not be recognized by isaac-sim.
    - Note: If you have other demos in `user_examples`, you may have an existing `user_examples/__init__.py` already. If so, simply ensure the lines from the `hello_robot/__init__.py` are added to the existing init file.

Running the demo:
1. Open a terminal at `paranet/examples/hello_robot`
2. run `para docker build`
3. Observe the output to ensure the core paranet services are online. This can also easily be seen in the docker extension.
4. Open the provided paracord link from the terminal. 
    - http://localhost:3023
    - This is where we will later trigger skills.
4. Open a terminal at `~/.local/share/ov/pkg/isaac-sim-4.2.0/` and run `./isaac-sim.sh`, or start isaac-sim from the omniverse launcher.
5. Once loaded, on the top bar open "Isaac Examples" and click "Hello Robot" in the list. If it is not present, ensure you completed setup properly, and your `user_examples/__init__.py` includes your hello robot lines.
6. Load the demo. You will see a seperate compose task in the Docker extension.
    - Don't press Play or anything else, following actions will happen in paracord.
7. Go to the "Advanced" tab in paracord, and find the "Hello Robot" actor.
8. Test the 3 mentioned skills.
9. Note that currently reset demo is not currently built into the skills. Use the Isaac sim UI to stop and reload the demo.