# Local Environment Setup

Follow the sections in order. Do not connect to or enable the real robot while
installing the software.

**Scope of this document:** only the local computer environment, software
versions, Python environment, and hardware drivers. Server-side training and the
use of the project programs are intentionally documented in two separate guides:

- [GPU server, Docker, and training](README_SERVER.md)
- [Project programs and complete workflows](README_CODE.md)

## 1. What This Environment Is For

The local environment is used for:

- running the MuJoCo simulation;
- inspecting and replaying recorded Zarr datasets;
- collecting demonstrations with the Touch device;
- reading the two Intel RealSense cameras;
- communicating with the UR10 and OnRobot gripper;
- loading and executing a trained Diffusion Policy on the local CPU.

Training the large neural network is **not** done in this environment. Training
uses the LIRMM GPU server and its Docker container. Keeping these two environments
separate avoids installing several gigabytes of CUDA libraries on the robot PC.

## 2. Important Vocabulary

- **Operating system:** the base software of the computer. This project was
  developed on Ubuntu Linux 22.04.
- **Repository:** the project directory downloaded from Git. It contains the
  source code, configuration files, and documentation.
- **Dependency:** an external library used by the project, such as PyTorch,
  MuJoCo, or OpenCV.
- **Virtual environment:** an isolated Python installation for one project. It
  prevents this project's libraries from changing another project's libraries.
- **Conda environment:** the type of virtual environment used here. Its content
  is described in `environment_local.yml`.
- **System package:** software installed for the whole computer with `apt`.
  Hardware drivers and ROS 2 belong to this layer and cannot be installed inside
  a Python environment.

There are therefore three different layers:

| Layer | Examples | Installed with |
|---|---|---|
| Ubuntu system | Git, compiler, RealSense driver | `apt` |
| Python environment | PyTorch, MuJoCo, Zarr, OpenCV | `environment_local.yml` |
| Robot middleware | ROS 2 Humble, Touch driver | `apt` and `colcon` |

## 3. Reference Versions

The following setup was used successfully on the final development computer.
Use Ubuntu 22.04 and Python 3.10 unless the complete stack has been tested again.

| Component | Reference version |
|---|---|
| Operating system | Ubuntu 22.04.5 LTS, 64 bit |
| Linux kernel on the reference PC | 6.8.0-138-generic |
| Python | 3.10.12 |
| ROS 2 | Humble |
| MuJoCo | 3.6.0 |
| PyTorch / TorchVision | 2.11.0 / 0.26.0 |
| Intel RealSense SDK | 2.58.x |
| OpenHaptics SDK | 3.4 |
| Git branch | `main` |
| Source revision | Record the current value with `git rev-parse HEAD` |

The Git commit identifies the exact version of the source code used for an
experiment. Display the version currently checked out with:

```bash
git branch --show-current
git rev-parse HEAD
```

Use the latest reviewed revision on `main`, and record its commit for each
experiment so that the result can be reproduced.

## 4. Install the Ubuntu Packages

Open a terminal with `Ctrl+Alt+T`, then run:

```bash
sudo apt update
sudo apt install -y \
  git curl wget ca-certificates gnupg lsb-release \
  build-essential cmake ninja-build pkg-config python3-dev \
  bash ffmpeg \
  libgl1 libglib2.0-0 libglfw3 libosmesa6-dev patchelf \
  libusb-1.0-0-dev
```

What this does:

- `git` downloads and updates the repository;
- `build-essential`, `cmake`, and `ninja-build` compile C/C++ code;
- the `libgl*` packages allow MuJoCo and OpenCV to display images;
- `ffmpeg` reads and writes experiment videos;
- `libusb` is required by USB devices such as the RealSense cameras.

## 5. Install Miniforge

Miniforge provides the `conda` and `mamba` commands. If `conda --version`
already works, skip this section.

```bash
cd "$HOME"
curl -L -O \
  "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash "Miniforge3-$(uname)-$(uname -m).sh"
```

Accept the licence, keep the proposed installation directory, and answer `yes`
when the installer asks whether it should initialize the shell. Close and reopen
the terminal after installation.

Verify the installation:

```bash
conda --version
mamba --version
```

The official installation instructions are in the
[Miniforge documentation](https://github.com/conda-forge/miniforge#install).

## 6. Download the Repository

The commands below create the same directory layout used during development.
The username does not need to be `luca`.

```bash
mkdir -p "$HOME/Stage_Lirmm"
cd "$HOME/Stage_Lirmm"
git clone https://github.com/Lucavogel/Diffusion_model_microwave.git \
  Diffusion-model-isaacsim
cd Diffusion-model-isaacsim
git switch main
```

If the repository has already been cloned, do not clone it again. Enter it and
check its state instead:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
git status
```

## 7. Create the Python Environment

Always run the next command from the repository root, where
`environment_local.yml` is located:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
mamba env create -f environment_local.yml
conda activate microwave_dp
python -m pip install --no-deps -e ./diffusion_policy
```

If `mamba` is unavailable, replace the first command with:

```bash
conda env create -f environment_local.yml
```

The installation may take several minutes. The YAML file fixes the important
library versions and requests the CPU build of PyTorch. `pip install -e` then
registers the local Diffusion Policy source code without copying it. Changes made
inside `diffusion_policy/` are therefore immediately visible to Python.

Check that the correct interpreter is active:

```bash
which python
python --version
```

The prompt should start with `(microwave_dp)`, and Python should report version
3.10. Deactivate the environment with `conda deactivate`.

### Updating an existing environment

When `environment_local.yml` changes, update the existing environment with:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
mamba env update -f environment_local.yml --prune
python -m pip install --no-deps -e ./diffusion_policy
```

Do not solve a missing import by installing random package versions. Add the
required package to `environment_local.yml`, recreate or update the environment,
and document the change.

## 8. Install ROS 2 Humble

ROS 2 transports the Touch pose from its C++ driver to the Python teleoperation
program. It is a system dependency, not a normal Python library.

First check whether it is already installed:

```bash
test -f /opt/ros/humble/setup.bash && echo "ROS 2 Humble is installed"
```

If it is missing, install ROS 2 Humble using the official Ubuntu instructions:

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe

export ROS_APT_SOURCE_VERSION=$(curl -s \
  https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest \
  | grep -F 'tag_name' | awk -F\" '{print $4}')

curl -L -o /tmp/ros2-apt-source.deb \
  "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo $VERSION_CODENAME)_all.deb"

sudo dpkg -i /tmp/ros2-apt-source.deb
sudo apt update
sudo apt install -y \
  ros-humble-desktop ros-dev-tools \
  python3-colcon-common-extensions ros-humble-moveit
```

Then initialize `rosdep`. The first command is required only once per computer:

```bash
sudo rosdep init
rosdep update
```

If `rosdep init` says that the sources list already exists, that is normal: skip
that command and run only `rosdep update`.

Activate ROS 2 in the current terminal:

```bash
source /opt/ros/humble/setup.bash
ros2 --help
```

Refer to the [official ROS 2 Humble Ubuntu guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html)
if the package repository setup changes.

## 9. Install the RealSense Driver (Real Cameras Only)

Skip this section for simulation-only work. The YAML installs the Python wrapper,
but Ubuntu also needs the camera driver and USB permissions.

```bash
sudo mkdir -p /etc/apt/keyrings
curl -sSf https://librealsense.realsenseai.com/Debian/librealsenseai.asc \
  | gpg --dearmor \
  | sudo tee /etc/apt/keyrings/librealsenseai.gpg > /dev/null

sudo apt install -y apt-transport-https
echo "deb [signed-by=/etc/apt/keyrings/librealsenseai.gpg] https://librealsense.realsenseai.com/Debian/apt-repo $(lsb_release -cs) main" \
  | sudo tee /etc/apt/sources.list.d/librealsense.list

sudo apt update
sudo apt install -y librealsense2-dkms librealsense2-utils librealsense2-dev
```

Unplug and reconnect the cameras, then verify them **one at a time**:

```bash
realsense-viewer
```

The official and current commands are maintained in the
[librealsense Linux guide](https://github.com/realsenseai/librealsense/blob/master/doc/distribution_linux.md).

## 10. Install OpenHaptics (Touch Device Only)

OpenHaptics is the vendor SDK used to communicate with the 3D Systems Touch.
It is not distributed through Conda or the Ubuntu repository.

1. Open the official [3D Systems OpenHaptics support page](https://support.3dsystems.com/s/article/OpenHaptics-for-Linux-Developer-Edition-v34?language=en_US).
2. Download **OpenHaptics Installer -- OpenHaptics for Linux v3.4** and
   **Haptic Device Driver Installer -- Touch Device Driver v2025.12.10**.
3. Create a permanent working directory, for example `~/touch_driver`, and
   extract both archives there. Do not put them inside the Git repository.
4. Define `OPENHAPTICS_ROOT` as the directory containing the extracted `usr/`
   directory.

Example:

```bash
export OPENHAPTICS_ROOT="$HOME/touch_driver/openhaptics_3.4-0-developer-edition-amd64"
test -f "$OPENHAPTICS_ROOT/usr/include/HD/hd.h" \
  && echo "OpenHaptics headers found"
```

If the `test` command prints nothing, the path is wrong. Find the directory that
contains `usr/include/HD/hd.h` and correct `OPENHAPTICS_ROOT`.

## 11. Build the Touch ROS 2 Workspace

Activate all required layers in this order:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
source /opt/ros/humble/setup.bash
export OPENHAPTICS_ROOT="$HOME/touch_driver/openhaptics_3.4-0-developer-edition-amd64"
```

Install ROS dependencies and build:

```bash
cd ros2_WS
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install \
  --cmake-args -DOPENHAPTICS_ROOT="$OPENHAPTICS_ROOT"
source install/setup.bash
```

The `build/`, `install/`, and `log/` directories are generated for one
computer. If this repository was copied from another computer and the build
contains old absolute paths, remove only these three generated directories and
build again:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim/ros2_WS"
rm -rf build install log
colcon build --symlink-install \
  --cmake-args -DOPENHAPTICS_ROOT="$OPENHAPTICS_ROOT"
```

## 12. Verify the Complete Installation

Return to the repository root and run the automatic check:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
source /opt/ros/humble/setup.bash
source ros2_WS/install/setup.bash
python scripts/check_environment.py
```

The script uses three result levels:

- `[OK]`: this part is correctly installed;
- `[WARN]`: an optional hardware component is unavailable;
- `[FAIL]`: a core dependency is missing and must be fixed.

A student working only in simulation may ignore warnings for RealSense,
OpenHaptics, and real-robot communication. Do not ignore a failure.

## 13. Daily Terminal Setup

Run these commands once in every new terminal before working:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
source /opt/ros/humble/setup.bash
source ros2_WS/install/setup.bash
```

The order matters: first the Python environment, then ROS 2, then this project's
compiled ROS workspace.

The three canonical shell launchers perform these activation/source steps
themselves. Manual activation is still required for standalone Python, ROS 2,
dataset, and diagnostic commands. A launcher uses the active Conda/virtual
environment when one exists; otherwise it tries to activate `microwave_dp`.

For commands that do not use the Touch device, the final `source` command is not
required. For pure dataset inspection, only the Conda environment is required.

## 14. First Safe Test

Start with software-only checks. Do not enable physical motion.

```bash
python scripts/check_environment.py
python -c "import torch; print('PyTorch:', torch.__version__, 'CUDA:', torch.cuda.is_available())"
python -c "import mujoco; print('MuJoCo:', mujoco.__version__)"
```

`CUDA: False` is expected on the local robot computer. It is not an installation
error. The large policy can run on the CPU, but inference is slower than on the
LIRMM GPU server.

## 15. Common Problems

### `conda: command not found`

Close and reopen the terminal. If it still fails:

```bash
"$HOME/miniforge3/bin/conda" init
```

### `ModuleNotFoundError: dp_mujoco` or `ur10_real_robot`

Run the command from the repository root and verify the active environment:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
which python
```

### `ModuleNotFoundError: diffusion_policy`

Register the local package again:

```bash
python -m pip install --no-deps -e ./diffusion_policy
```

### `ros2: command not found`

```bash
source /opt/ros/humble/setup.bash
```

### OpenHaptics headers or libraries are not found

Verify that the path contains `usr/include/HD/hd.h` and `usr/lib/libHD.so`,
then rebuild with the correct `OPENHAPTICS_ROOT`.

### A RealSense camera is not found

Check the USB connection and list devices:

```bash
rs-enumerate-devices
lsusb -t
```

Connect each RealSense to a separate USB 3 controller when possible. A camera
listed at `480M` is using USB 2 and is more likely to time out.

### OpenCV opens a black window or reports Qt errors

Ensure the command is run from a graphical Ubuntu session, not a headless SSH
session. Close other applications that already use the cameras.

## 16. Files to Use and Files to Avoid

- Use `environment_local.yml` for a new local installation.
- `environment_sim.yml` is a legacy simulation file kept for old experiments.
  It does not reproduce the final robot environment.
- The original `diffusion_policy/conda_environment*.yaml` files describe the
  upstream training stack. They are not the local robot-PC environment.
- Never commit passwords, private SSH keys, large datasets, or checkpoints.

Once this guide passes on a clean computer, record the computer name, Git commit,
and environment check output in the experiment notes.
