# Diffusion Policy for Robotic Manipulation

This repository contains a complete **Diffusion Policy pipeline for robotic
manipulation**, developed during an internship at LIRMM. The project started in
MuJoCo simulation and was then adapted to a physical **UR10 CB2 robot** equipped
with an **OnRobot RG2-FT gripper** and two Intel RealSense cameras.

The main application is robotic manipulation for e-waste disassembly, with a
focus on extracting electronic components from a microwave-like workspace.

## Highlights

- MuJoCo benchmark for microwave-inspired component extraction.
- Touch-based teleoperation for collecting demonstrations.
- Multimodal datasets with robot state, gripper state, and two RGB camera views.
- Diffusion Policy training with image-conditioned U-Net and Transformer variants.
- Real UR10 deployment using a speedj-based backend.
- Real-robot microwave component extraction benchmark.

## Demonstrations

### MuJoCo Simulation

https://github.com/user-attachments/assets/5065d1bc-a97e-4889-a67c-71cdfe236247

*Diffusion Policy executing a microwave disassembly task in MuJoCo: extracting
two objects from the cavity and placing them into their respective sorting boxes.
The objects are initialized with a random offset of +/- 0.2 m along the y-axis.*

**Result:** 30/30 successful simulation trials.

### Real Robot

REAL_ROBOT_VIDEO_LINK

*Diffusion Policy executing a microwave component extraction task on the physical
UR10, with small variations in the initial object position. The policy was
trained from demonstrations collected directly on the real setup through
teleoperation.*

**Result:** 18/20 successful real-robot trials.

**Video note:** the real-robot video is shown at 3x playback speed.

> The simulation and real-robot experiments use separate demonstration datasets.
> The real-robot policy is trained from demonstrations collected directly on the
> physical setup and is not a direct sim-to-real transfer of the MuJoCo policy.

## Repository Structure

```text
configs/           Hydra training and task configuration files
data/              Datasets, checkpoints, logs, and local experiment artifacts
diffusion_policy/  Diffusion Policy implementation and neural network modules
dp_mujoco/         MuJoCo environments, robot models, teleoperation, and utilities
ros2_WS/           ROS2 workspace used for the Touch interface and robot tooling
scripts/           Dataset inspection, replay, plotting, and benchmark utilities
ur10_real_robot/   Real UR10 teleoperation, cameras, gripper, and policy execution
```

## Installation

The full setup is described in [README_ENV.md](README_ENV.md).

Quick simulation environment setup:

```bash
conda env create -f environment_sim.yml
conda activate <your_env_name>
pip install -r requirements_sim.txt
```

Real-robot execution additionally requires the UR10 network setup, the OnRobot
gripper connection, RealSense camera drivers, and the local ROS2/Touch tooling.

## Typical Workflow

### 1. Teleoperation and Data Collection

Human demonstrations are collected through teleoperation. Each recorded episode
contains:

- two RGB camera views,
- end-effector position and orientation,
- gripper opening,
- the target action used for policy learning.

### 2. Dataset Inspection

Recorded `.zarr` datasets can be checked before training:

```bash
python3 scripts/check_zarr.py data/datasets/<dataset_name>.zarr
python3 scripts/replay_zarr.py data/datasets/<dataset_name>.zarr
```

For real cameras, a live-vs-dataset visual comparison tool is also available:

```bash
PYTHONPATH=. python3 scripts/compare_live_camera_to_zarr.py \
  data/datasets/<dataset_name>.zarr
```

### 3. Training

Training uses Hydra configuration files. Example:

```bash
python train.py \
  --config-name=train_e_waste_unet_real \
  task=e_waste_image_unet_real \
  training.device=cuda:0
```

### 4. Real-Robot Execution

The real robot launcher keeps the execution parameters in one place:

```bash
CHECKPOINT=data/checkpoints/<checkpoint>.ckpt \
ENABLE_MOTION=1 \
./ur10_real_robot/run_diffusion_real.sh
```

Start real-robot experiments with a low speed slider and keep the emergency stop
reachable.

## Experiments

### Simulation

The MuJoCo environment includes the robot, gripper, cameras, target components,
a simplified microwave cavity, and sorting containers. It was used to validate
the full pipeline and compare U-Net and Transformer diffusion backbones.

**Evaluated result:** 30/30 successful rollouts.

### Physical UR10

The real setup uses:

- UR10 CB2 manipulator,
- OnRobot RG2-FT gripper,
- Intel RealSense D435 top-view camera,
- Intel RealSense D455 wrist camera,
- teleoperated real demonstrations for policy training.

The current real benchmark is microwave component extraction. The robot starts
outside the cavity, enters with a narrowed gripper, grasps a small component,
extracts it, and releases it into a target box.

**Evaluated result:** 18/20 successful trials.

## Acknowledgements

This project builds on the Diffusion Policy codebase from the Columbia
Artificial Intelligence and Robotics Lab, distributed under the MIT License.

The original license is preserved in:

```text
diffusion_policy/LICENSE
```

This repository extends the original codebase with UR10 integration, MuJoCo
environments, teleoperation, real-robot deployment, multimodal data collection,
and robotic disassembly experiments.
