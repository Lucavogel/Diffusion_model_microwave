# Diffusion Policy for Robotic Manipulation — MuJoCo & Real UR10

This repository implements a **Diffusion Policy pipeline for robotic manipulation**, developed during my internship at LIRMM.

The project includes **teleoperation and multimodal data collection, policy training, MuJoCo simulation, and deployment on a physical UR10 robot**, with a focus on robotic disassembly and e-waste sorting tasks.

## Demonstrations

### MuJoCo Simulation

https://github.com/user-attachments/assets/5065d1bc-a97e-4889-a67c-71cdfe236247

*Diffusion Policy executing a microwave disassembly task in MuJoCo: extracting two objects from the cavity and placing them into their respective sorting boxes. The objects are initialized with a random offset of ±0.2 m along the y-axis.*

**30/30 successful simulation trials.**

### Real Robot

REAL_ROBOT_VIDEO_LINK

*Diffusion Policy executing a microwave component extraction task on the physical UR10, with small variations in the initial object position. The policy was trained from demonstrations collected directly on the real setup through teleoperation.*

**Video shown at 3× playback speed.**

> The simulation and real-robot experiments use separate demonstration datasets. The real-robot policy is trained from demonstrations collected directly on the physical setup and is not a direct sim-to-real transfer of the MuJoCo policy.

## Project Architecture

- **`configs/`** — Hydra configuration files for training and environment setups.
- **`data/`** — Training datasets (`.zarr` files), model checkpoints, and experiment logs.
- **`diffusion_policy/`** — Main Diffusion Policy implementation, including neural network architectures and action generation.
- **`mujoco/`** — MuJoCo simulation environments, UR10 robot models, teleoperation scripts, kinematics, and safety utilities.
- **`ros2_WS/`** — ROS2 workspace for communication with and control of the physical robot.
- **`scripts/`** — Dataset inspection, trajectory visualization, metrics, and other utility scripts.

## Installation

A detailed guide for setting up the environment is available in `README_ENV.md`.

Quick Conda setup:

```bash
conda env create -f environment_sim.yml
conda activate <your_env_name>
pip install -r requirements_sim.txt
Usage
1. Teleoperation & Data Collection

Teleoperation tools are provided to collect human demonstration datasets used for Diffusion Policy training.

The collected demonstrations include robot states and visual observations used by the policy during training.

2. Dataset Validation

Collected .zarr datasets can be inspected by visualizing the recorded 3D robot trajectories:

python scripts/traj_zarr.py --pos-key "robot_pos"

This can be used to verify that recorded demonstrations are smooth and valid before starting training.

3. Training

Launch Diffusion Policy training using the corresponding Hydra configuration:

python diffusion_policy/train.py --config-name=train_e_waste.yaml
4. Pipeline Launch

The main pipeline operations can also be launched using:

bash launch_all.sh
Experiments

The project was evaluated both in simulation and on the physical robot.

Simulation

A custom MuJoCo environment reproduces the manipulation setup, including the robot, gripper, cameras, objects, and task environment.

The Diffusion Policy achieved:

30/30 successful trials

on the evaluated microwave disassembly task in simulation.

Physical Robot

For the physical UR10 experiments, demonstrations were collected directly on the real setup using teleoperation.

The resulting Diffusion Policy was deployed on the robot and evaluated with small variations in the initial object position.

The current task focuses on extracting a component from inside a microwave cavity, requiring the robot to approach the cavity, enter it, localize and grasp the component, and extract it from the cavity.

Acknowledgements

This project builds on the Diffusion Policy codebase from the Columbia Artificial Intelligence and Robotics Lab, distributed under the MIT License.

The original copyright notice and license terms are preserved in:

diffusion_policy/LICENSE

This repository extends the original codebase with UR10 integration, MuJoCo environments, teleoperation, ROS2 deployment, multimodal data collection, and robotic disassembly experiments.
