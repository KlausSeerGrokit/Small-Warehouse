
# CES DEMO Quickstart Guide

This README provides instructions for setting up the environment, running ROS 2 and MoveIt, and launching the CES demo in Isaac Sim. After completing these steps, you’ll be able to start the simulation, connect via Paranet, and interact with the H1 robot.

## Prerequisites

- NVIDIA Drivers installed (for GPU-accelerated Isaac Sim)
- ROS 2 Humble (or target ROS 2 distribution)
- MoveIt 2 (matching the same ROS 2 distribution)
- Isaac Sim installed on a machine with Ubuntu

# Initial Setup

### 1. Install ROS 2 and MoveIt
Follow the official ROS 2 and MoveIt installation instructions:

#### ROS 2 Installation:
For ROS 2 Humble: [ROS 2 Humble Installation Guide](https://docs.ros.org/en/humble/Installation/Alternatives/Ubuntu-Development-Setup.html)

    # Example for ROS 2 Humble on Ubuntu 22.04:
    sudo apt update && sudo apt install locales
    # Generate locale
    sudo locale-gen en_US en_US.UTF-8
    sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
    source /etc/os-release
    sudo apt update && sudo apt install curl gnupg2 lsb-release
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
    # Add ROS 2 repository
    sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $UBUNTU_CODENAME main" > /etc/apt/sources.list.d/ros2-latest.list'
    sudo apt update
    sudo apt install ros-humble-desktop

#### MoveIt 2 Installation:

Follow the official instructions for MoveIt 2 on Humble: [MoveIt 2 Installation Guide](https://moveit.ai/install-moveit2/binary/) 

    # Example for MoveIt 2:
    sudo apt install ros-humble-moveit

After installation, remember to source your ROS 2 and MoveIt setup:

    source /opt/ros/humble/setup.bash

## 2. Verify ROS 2 and MoveIt



    ros2 run demo_nodes_cpp talker
    ros2 run moveit_ros_move_group move_group --help

If these commands run without errors, your setup is correct.

# Running the CES DEMO in Isaac Sim

### 1. Launch Isaac Sim:
- Start Isaac Sim from your Ubuntu applications menu or by running the provided script from your Isaac Sim installation directory:

  

      ./isaac-sim.sh

- Ensure that you have a supported GPU driver and that the Isaac Sim UI loads correctly.

### 2. Setting up the project on Isaac Sim:

- Copy all the files in the `extension` folder here into the Isaac Sim installation folder `\omniverse\pkg\isaac-sim-4.2.0\exts\omni.isaac.examples\omni\isaac\examples\user_examples`.
- Go to File > Open...
- Select the CES.usd file from your project directory.
- The scene should load the environment and the initial configuration.
### 3. Start the Simulation and ROS/Paranet Connection:
- In the Isaac Sim toolbar, open Isaac Examples and click CES Demo.
- This will start the simulation and initiate the Paranet connection within the sim.

At this point, the environment will spawn an H1 robot that can be controlled via the keyboard (arrow keys and WASD) according to the demo’s defined controls.

### 4. Controlling the H1 Robot:

- Once the simulation is running, use arrow keys and WASD in the Isaac Sim viewport to move the H1 robot.
- You should see the robot responding to input commands.

### 5. Interfacing with ROS 2 and MoveIt: 
When interfacing with ROS2 and MoveIt, please ensure:
- ROS 2 nodes are active on your machine.
- Isaac Sim and ROS 2 are in the same network environment, and `ROS_LOCALHOST_ONLY=0 if required.`

Once MoveIt is publishing trajectories to the relevant ROS 2 topics, Isaac Sim will reflect that motion in the H1 robot within the simulation.

## Restarting the CES DEMO Example
If you need to reset the scenario:
- Instead of stopping Isaac Sim entirely, use the Restart option on the CES DEMO interface (e.g., in Isaac Sim’s Sample Browser or your custom UI).
- Pressing Restart resets the scene, the robot’s position, and reinitializes the Paranet connection, allowing you to start fresh without fully stopping and relaunching the simulation.

## Troubleshooting
- No Robot Movement:
Check if Isaac Sim’s play button is pressed and the simulation is actually running. Ensure you have focus on the Isaac Sim viewport before pressing the arrow keys and WASD.

- ROS 2 Connectivity Issues:
If MoveIt or ROS commands don’t affect Isaac Sim, verify that both are running on the same network and domain ID, and that ROS_LOCALHOST_ONLY is set to 0.

- Performance/Graphics Issues:
Ensure NVIDIA drivers are updated and that you meet the recommended hardware requirements for Isaac Sim.