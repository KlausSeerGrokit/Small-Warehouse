# Isaac Sim Integration

## Install

Isaac Sim installs it's own Python environment, so the `paranet_agent` package needs to be installed in the environment, as follows:
1. Download the last wheel file from the [release page](https://github.com/grokit-data/py-paranet-sdk/releases/latest)
2. Local Isaac Python binary (`D:\omniverse\pkg\isaac-sim-4.2.0\python` on Windows, `/home/devops/.local/share/ov/pkg/isaac-sim-4.2.0/python.sh` on CES laptops)
3. Install package with `<isaac-python> -m pip install <downloaded wheel file>`

## Isaac Sim Configuration

The demo requires the ISAAC SIM CONVEYOR BELT UTILITY extension to be enabled.  This is a one-time step:
1. Launch Isaac Sim
2. Select Windows -> Extensions from menu
3. Enter `conveyor` in the search bar
4. Click on the ISAAC SIM CONVEYOR BELT UTILITY extension
5. Click the "ENABLED" switch
6. Click the "AUTOLOAD" checkbox

## Install Isaac Sim extension

Copy all the files in the `extension` folder here into the Isaac Sim installation folder at `<isaac-sim-folder>\exts\omni.isaac.examples\omni\isaac\examples\user_examples`.  The installation folder should be `D:\omniverse\pkg\isaac-sim-4.2.0` on Windows and `/home/devops/.local/share/ov/pkg/isaac-sim-4.2.0` on CES laptops.

When you launch Isaac Sim, it will appear in the Isaac Examples menu as "CES Demo".

## Running

1. Start the Paranet via `para docker build --config paranet-isaac.yaml
2. Start Isaac Sim
3. Select the Isaac Examples -> CES Demo -> CES Demo menu item
4. Click load and wait a while for the scene to appear
5. Click play if it does not auto play
6. Open Paracord, select Advanced tab and clock on the fleet mgmt actor
7. Use the Start Cell request to start the work cells.  The cell input is 1 or 2.