 # Execution Environment (Simulation)

This file describes the minimal environment required to run simulations and teleoperation (execution only — no training).

## Available Files
- `environment_sim.yml`: Minimal conda environment for execution/simulation.
- `environment_repro.yml`: Full environment (training + execution).
- `requirements_sim.txt`: Minimal pip packages for simulation.
- `requirements.txt`: Extra pip packages for the full environment.

## Quick Installation (Conda, recommended)
1. Install Miniconda/Anaconda or micromamba.
2. Install the necessary system packages (Ubuntu example) for display, MuJoCo, and 3D mouse:

```bash
sudo apt update
sudo apt install -y libosmesa6-dev libgl1-mesa-glx libglfw3 patchelf libspnav-dev spacenavd
```

3. Create the minimal environment for simulation:

```bash
conda env create -f environment_sim.yml
conda activate robodiff_sim
```

## Alternative (pip only)

```bash
conda create -n robodiff_sim python=3.9 -y
conda activate robodiff_sim
pip install -r requirements_sim.txt
```

## Important System Notes
- **MuJoCo** (if used): `free-mujoco-py` requires MuJoCo binaries and additional system packages. See [mujoco.org](https://mujoco.org/) and the repository documentation.
- **`pyrealsense2`** (if using a RealSense camera): requires `librealsense`; see the [Linux distribution docs](https://github.com/IntelRealSense/librealsense/blob/master/doc/distribution_linux.md).
- **`spnav` / 3D mouse**: install `spacenavd` and start the service (`sudo systemctl start spacenavd`) if using a 3D SpaceMouse.
- **GPU & CUDA**: Install compatible NVIDIA drivers if using a GPU. The `environment_sim.yml` environment may include `cudatoolkit` for local installation, but keep your system drivers updated.

## Remarks
- `environment_sim.yml` is intentionally kept minimal to reduce installation time and potential conflicts. If you need training dependencies (datasets, diffusers, accelerate, wandb, etc.), use `environment_repro.yml`.
- If you prefer a Docker container or a `conda-lock` file for exact build reproducibility, I can generate one.

## Contact
- Let me know if you would like me to prepare a specific `environment_sim.yml` for Ubuntu 22.04 or a Dockerfile.
