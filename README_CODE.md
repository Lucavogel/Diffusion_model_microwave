# Using the Project Programs

This guide explains what the project programs do, where they are located, and
how to use them in the correct order. It is written for a new student who has
never used this repository, Diffusion Policy, MuJoCo, ROS 2, or the real robot.

Read the other setup guides first when necessary:

- [Local environment setup](README_ENV.md): install the local computer.
- [GPU server and training](README_SERVER.md): create the training container,
  transfer datasets, and train checkpoints.

Real-robot commands require an authorized operator, the local safety procedure,
and immediate access to the emergency stop. A trained policy can produce an
unexpected target even when the checkpoint loads successfully.

## 1. The Complete Workflow

The project has four main stages:

```text
Human teleoperation
        |
        v
Recorded Zarr demonstrations
        |
        v
Diffusion Policy training on the GPU server
        |
        v
Checkpoint execution in MuJoCo or on the real UR10
```

A **demonstration** is one complete example of the task performed by a human. A
**dataset** contains several demonstrations. A **checkpoint** is a saved neural
network produced during training. **Policy execution** means loading that
checkpoint and letting it predict robot actions from the latest observations.

There are two separate experimental pipelines:

| Pipeline | Demonstrations | Images | Execution |
|---|---|---|---|
| Simulation | Collected in MuJoCo | 84 x 84 pixels | MuJoCo robot |
| Real robot | Collected on the physical UR10 | 320 x 240 pixels | Physical UR10 |

The simulation and real-robot policies are trained separately. A simulation
checkpoint is not directly transferred to the real robot.

## 2. Start Every Local Session Correctly

Open a terminal and enter the repository:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
```

The exact parent directory may differ on a new computer. The important point is
that the terminal must be at the repository root. Confirm this with:

```bash
pwd
ls
```

The output of `ls` should include `README.md`, `dp_mujoco`,
`ur10_real_robot`, and `scripts`.

For programs that use the Touch device, also load ROS 2 and the compiled Touch
workspace:

```bash
source /opt/ros/humble/setup.bash
source ros2_WS/install/setup.bash
```

The launch scripts source the Bash setup files automatically. These manual
commands are useful only when running ROS 2 diagnostics directly.

## 3. Repository Map

These are the directories a new student will use most often:

| Path | Purpose |
|---|---|
| `configs/task/` | Dataset path, observation keys, shapes, and validation split |
| `configs/train/` | Policy architecture, horizons, optimizer, and training schedule |
| `data/datasets/` | Local `.zarr` demonstration datasets |
| `data/checkpoints/` | Checkpoints copied back from the GPU server |
| `data/outputs/` | Local logs and experiment outputs |
| `diffusion_policy/` | Training workspaces, datasets, policies, and neural networks |
| `dp_mujoco/` | MuJoCo scene, simulation teleoperation, and simulation execution |
| `ur10_real_robot/` | UR10, gripper, cameras, real teleoperation, and real execution |
| `ros2_WS/` | ROS 2 driver for the 3D Systems Touch interface |
| `scripts/` | Dataset replay, checks, plots, and benchmarks |

The main entry points are:

| Program | What it starts |
|---|---|
| `./launch_all.sh` | MuJoCo teleoperation and the Touch ROS 2 node |
| `./ur10_real_robot/run_teleop.sh` | Real-robot teleoperation and recording |
| `diffusion_policy/train.py` | Diffusion Policy training |
| `python -m dp_mujoco.policy_exec.run_diffusion_mujoco` | Simulation policy execution |
| `./ur10_real_robot/run_diffusion_real.sh` | Real-robot policy execution |

Start from these launchers before reading lower-level modules. Files named
`demo_*`, old experiment scripts, and `Readme2` contain development history and
are not part of the maintained workflow.

## 4. What Is Stored in a Dataset

Datasets use the [Zarr](https://zarr.readthedocs.io/) format. A `.zarr` path is a
directory containing compressed arrays, not one ordinary file. Never move only
some of its internal files.

Each real demonstration stores synchronized values at 10 Hz:

| Key | Meaning | Real shape per step |
|---|---|---|
| `agentview_image` | RGB top-view camera image | `240 x 320 x 3` |
| `robot0_eye_in_hand_image` | RGB wrist-camera image | `240 x 320 x 3` |
| `robot0_eef_pos` | Measured end-effector position in metres | `3` |
| `robot0_eef_quat` | Measured end-effector quaternion | `4` |
| `robot0_gripper_qpos` | Measured gripper state | `1` |
| `action` | Demonstrated Cartesian target and gripper command | `8` |

The real action is:

```text
[x, y, z, qw, qx, qy, qz, gripper]
```

The first seven values describe the desired end-effector pose. The eighth value
describes the gripper command.

### Important quaternion difference

- Real datasets and real execution use `wxyz` inside the 8D action.
- The current MuJoCo recorder and executor use `xyzw` inside the 8D action.

The `robot0_eef_quat` observation itself is stored as `wxyz` by both current
recorders. The difference above concerns the action representation.

Do not mix real and simulation datasets, task configurations, or checkpoints.
Quaternion-order errors may produce plausible positions with completely wrong
orientations.

The policy normally receives the two latest observation steps, predicts 16
future actions, and executes only the first 6 or 8 before replanning. Predicting
a longer future helps the model generate a coherent motion. Replanning before
all 16 actions are consumed limits the effect of increasingly old predictions.

## 5. Simulation Workflow

Simulation is the safest place to understand the complete pipeline.

### 5.1 Collect a MuJoCo demonstration

Check that the Touch driver was built as described in `README_ENV.md`, then run:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
./launch_all.sh
```

The launcher starts the Touch driver in the background, waits until
`/touch/pose` is available, and then opens MuJoCo. Both processes belong to the
same terminal; `Ctrl+C` stops them cleanly. Touch logs are written to
`/tmp/diffusion_policy_touch_driver.log` unless `TOUCH_LOG_FILE` is set.

Move the Touch stylus gently and verify that the simulated robot responds before
recording.

Controls in the MuJoCo window:

| Key | Action |
|---|---|
| `Space` | Start or stop an episode; stopping saves it |
| `Backspace` | Cancel the episode currently being recorded |
| `R` | Reset the robot and randomize the scene |
| `Esc` | Quit |

The dataset is created under `data/datasets/` with a name similar to:

```text
demo_data_YYYYMMDD_HHMMSS.zarr
```

### 5.2 Inspect the simulation dataset

Replace the example path with the one printed by the recorder:

```bash
python scripts/check_zarr.py \
  data/datasets/demo_data_YYYYMMDD_HHMMSS.zarr
```

Replay its images and states:

```bash
python scripts/replay_zarr.py \
  data/datasets/demo_data_YYYYMMDD_HHMMSS.zarr
```

The replay controls are listed in Section 7.

### 5.3 Train and execute a simulation policy

Training is performed on the GPU server. Follow `README_SERVER.md` and select a
simulation task configuration from `configs/task/` together with the matching
training configuration from `configs/train/`.

After copying the resulting checkpoint to `data/checkpoints/`, execute it with:

```bash
python -m dp_mujoco.policy_exec.run_diffusion_mujoco \
  --checkpoint data/checkpoints/<simulation_model>.ckpt \
  --device cpu \
  --policy_hz 10 \
  --exec_horizon 8 \
  --debug_timing
```

Use a simulation checkpoint only. The runner can save a trajectory as an `.npz`
file and timing measurements as a `.csv` file when the corresponding options are
enabled. Display all available options with:

```bash
python -m dp_mujoco.policy_exec.run_diffusion_mujoco --help
```

## 6. Real-Robot Demonstration Collection

### 6.1 Read this safety rule first

`REAL_DATASET_PRESET=1` selects the physical backend, cameras, gripper, and
recording configuration. It does **not** authorize motion by itself. Physical
arm motion requires the separate `ENABLE_MOTION=1` variable and an exact `YES`
confirmation. Before using it:

- obtain permission to operate the platform;
- clear the complete robot workspace;
- place the teach-pendant speed slider at a low value;
- keep the emergency stop reachable;
- verify the UR10, gripper, camera, and Touch network/USB connections;
- never stand inside the robot workspace.

If any target, camera image, or sound is unexpected, stop the run and understand
the cause before restarting.

### 6.2 Check the hardware connections

The current laboratory addresses are:

| Device | Address |
|---|---|
| UR10 controller | `192.168.2.100` |
| OnRobot gripper | `192.168.1.1:502` |

Check the UR10 and gripper networks:

```bash
ping -c 3 192.168.2.100
ping -c 3 192.168.1.1
```

List the RealSense cameras:

```bash
rs-enumerate-devices | grep -E "Name|Serial Number"
```

The current camera serials are configured in the launchers. If a camera is
replaced, set `TOP_SERIAL` or `WRIST_SERIAL` to the new serial rather than
editing unrelated code.

The camera pipeline captures `640 x 480` images, applies the configured crop,
then resizes them to the real-policy size of `320 x 240`.

### 6.3 Choose a new dataset name

Use a descriptive path and never accidentally append a different task to an old
dataset. For example:

```text
data/datasets/real_demo_microwave_new_task.zarr
```

If this path already exists, the recorder appends new episodes to it. Use
`scripts/check_zarr.py` before recording to confirm that this is intentional.

### 6.4 Launch the final three-state teleoperation setup

The command below reflects the final microwave data-collection interface. Keep
the values fixed across one dataset unless a deliberate new experiment is being
created.

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp

REAL_DATASET_PRESET=1 \
ENABLE_MOTION=1 \
ROBOT_IP=192.168.2.100 \
GRIPPER_IP=192.168.1.1 \
GRIPPER_PORT=502 \
WRIST_CAMERA_CONFIG=ur10_real_robot/camera/config/d455_config_microwave_auto.json \
POSITION_SCALE=0.70 \
MAX_TARGET_SPEED=0.12 \
MAX_POS_ERROR_STOP=0.25 \
TARGET_ALPHA_POS=0.65 \
TARGET_ALPHA_ROT=0.35 \
GRIPPER_CONTROL_MODE=width \
GRIPPER_COMMAND_MODE=three_state \
GRIPPER_STEP_VALUES="-0.2 0.30 0.70" \
RECORD_GRIPPER_QPOS_SOURCE=actual_width \
RECORD_GRIPPER_ACTION_SOURCE=command \
DATASET_PATH=data/datasets/<new_dataset_name>.zarr \
./ur10_real_robot/run_teleop.sh
```

The launcher starts and verifies the Touch node first, then runs real-robot
control, cameras, gripper, and recording in the foreground. `Ctrl+C` stops the
teleoperation process and its Touch node. The Python control module asks for
`YES` before opening any enabled physical actuator path.

### 6.5 Understand the gripper fields

The three-state command values represent:

```text
-0.2 -> open
 0.30 -> narrowed for entering the cavity
 0.70 -> grasp
```

`RECORD_GRIPPER_QPOS_SOURCE=actual_width` records the measured opening as part
of the observation. The observation therefore tells the policy what the gripper
actually did.

`RECORD_GRIPPER_ACTION_SOURCE=command` records the operator's intended
three-state command as the action target. It avoids teaching the policy the
delayed and fluctuating intermediate values measured while the physical gripper
is still moving.

These settings do not remove intermediate physical motion. They make the
learning target unambiguous while retaining the measured physical state in the
observation.

### 6.6 Camera-window controls

Click the camera window before pressing a key.

| Key | Action |
|---|---|
| `Space` | Start recording, or stop and save the current episode |
| `Backspace` | Cancel the current unsaved episode |
| `P` | Pause/resume robot command streaming when not recording |
| `H` | Return to the startup joint pose and initial gripper opening |
| `Q` or `Esc` | Stop the program |

The `H` command is disabled during recording. Press it again to cancel a home
motion. Always observe the robot during home reset; it is a real motion, not a
teleportation.

An episode is saved only when `Space` is pressed a second time and the minimum
step count is reached. `Backspace` cannot delete an episode that has already
been saved.

## 7. Inspect Every Dataset Before Training

Never start an expensive training run immediately after data collection. First
verify the structure, images, trajectories, and episode count.

### 7.1 Structure and episode count

```bash
python scripts/check_zarr.py \
  data/datasets/<dataset_name>.zarr
```

Confirm:

- the expected number of episodes;
- both image arrays are present;
- `action` has dimension 8;
- all arrays have the same number of time steps;
- the image resolution matches the selected task configuration.

### 7.2 Replay the episodes

```bash
python scripts/replay_zarr.py \
  data/datasets/<dataset_name>.zarr \
  --scale 2
```

Controls:

| Key | Action |
|---|---|
| `P` | Pause or resume |
| `N` or Right arrow | Next frame while paused |
| `B` or Left arrow | Previous frame while paused |
| `S` | Next episode |
| `Q` or `Esc` | Quit |

Reduce the displayed size on a small screen with `--scale 1` or
`--max-width <pixels>`.

### 7.3 Plot the end-effector trajectory

```bash
python scripts/traj_zarr.py \
  data/datasets/<dataset_name>.zarr
```

This helps identify sudden jumps, unusually long episodes, or a demonstration
that follows a very different path.

### 7.4 Compare live camera images with the dataset

Use this after a camera, table, microwave, crop, or light source has moved:

```bash
PYTHONPATH=. python scripts/compare_live_camera_to_zarr.py \
  data/datasets/<dataset_name>.zarr \
  --wrist-camera-config \
  ur10_real_robot/camera/config/d455_config_microwave_auto.json
```

Controls are `N`/`B` for frames, `]`/`[` for episodes, `S` to save a comparison
image, and `Q` to quit.

The live images do not need to be pixel-identical, but the workspace geometry,
camera crop, viewpoint, and illumination should be close to the demonstrations.

### 7.5 Dataset-quality checklist

Reject or recollect an episode when it contains:

- a frozen, black, or corrupted camera stream;
- an object that is hidden during the critical approach;
- an accidental collision or emergency stop;
- a task failure recorded as if it were a demonstration;
- a long inactive section unrelated to the task;
- a gripper command sequence inconsistent with the other demonstrations;
- a microwave, camera, light, or target box configuration from another setup.

Cancel a bad episode with `Backspace` before saving it. If a bad episode was
already saved, make a complete backup of the `.zarr` directory before using a
reviewed dataset-editing procedure. Never delete Zarr chunk files manually.

## 8. Select the Training Configuration

Training details and server commands are in `README_SERVER.md`. This section
only explains how the code selects the dataset and model.

### 8.1 Task configuration

`configs/task/e_waste_image_unet_real.yaml` defines:

- the default dataset path;
- observation keys and array shapes;
- image resolution;
- action dimension;
- training/validation split.

The dataset path can be changed in the file or overridden in the training
command. An explicit command-line override is easier to audit:

```text
task.dataset_path=/workspace/data/datasets/<dataset_name>.zarr
```

The path must exist **inside the Docker container**, normally under
`/workspace/data/datasets/`.

### 8.2 Training configuration

The final smaller real U-Net configuration is:

```text
configs/train/train_e_waste_unet_real_small.yaml
```

Its main sequence settings are:

| Parameter | Value | Meaning |
|---|---:|---|
| Observation horizon | 2 | Two consecutive observation steps condition the policy |
| Prediction horizon | 16 | The model predicts 16 future actions |
| Training action horizon | 8 | The action chunk used by the policy configuration |
| Training diffusion steps | 100 | Noise levels used by the diffusion process during training |

Do not change a shape, key, horizon, or quaternion convention only at execution
time. The dataset, task config, training config, and deployment code form one
interface contract.

### 8.3 Training output

Hydra creates a timestamped output directory such as:

```text
data/outputs/2026.08.14/14.56.32_train_.../checkpoints/
```

It normally contains periodic checkpoints and `latest.ckpt`. A lower validation
loss is useful, but it is not enough to choose the real-robot model. Inspect the
training curves, then compare a small set of candidate checkpoints under the
same controlled deployment conditions.

## 9. Check a Checkpoint Without the Robot

After copying a checkpoint to `data/checkpoints/`, verify that it exists:

```bash
ls -lh data/checkpoints/<model>.ckpt
```

Measure offline inference time without cameras or robot hardware:

```bash
PYTHONPATH=. python scripts/benchmark_policy_inference.py \
  data/checkpoints/<model>.ckpt \
  --device cpu \
  --num-inference-steps 8 \
  --warmup 2 \
  --repeats 5 \
  --output-csv data/benchmark_policy_cpu.csv
```

This test confirms that the model loads and measures policy computation only. It
does not prove that the checkpoint understands the task or is safe to execute.

The checkpoint stores its model architecture and normalization statistics. The
loader reconstructs the matching policy automatically and uses the EMA weights
when the training configuration enables EMA.

## 10. Test a Real Checkpoint in Three Stages

Never go directly from a downloaded checkpoint to enabled robot motion.

### 10.1 Stage 1: fake robot and fake cameras

This checks checkpoint loading, observation shapes, and inference with no
hardware connection and no physical movement:

```bash
CHECKPOINT=data/checkpoints/<real_model>.ckpt \
BACKEND=fake \
CAMERA_MODE=fake \
ENABLE_MOTION=0 \
GRIPPER_ENABLE=0 \
GRIPPER_MOTION_ENABLE=0 \
MAX_RUN_TIME=10 \
./ur10_real_robot/run_diffusion_real.sh
```

Expected result: the checkpoint loads, inference timings appear, fake targets
are printed, and the program exits after 10 seconds.

### 10.2 Stage 2: real observations, no motion

This connects to the UR10 and cameras but does not command the arm or gripper:

```bash
CHECKPOINT=data/checkpoints/<real_model>.ckpt \
BACKEND=speedj \
ROBOT_IP=192.168.2.100 \
CAMERA_MODE=realsense \
ENABLE_MOTION=0 \
GRIPPER_ENABLE=1 \
GRIPPER_MOTION_ENABLE=0 \
WRIST_CAMERA_CONFIG=ur10_real_robot/camera/config/d455_config_microwave_auto.json \
SHOW_CAMERAS=1 \
MAX_RUN_TIME=10 \
./ur10_real_robot/run_diffusion_real.sh
```

Expected result: both cameras start, the model predicts plans, and the measured
robot pose remains stationary. The gripper connection is read-only because
`GRIPPER_MOTION_ENABLE=0`.

`SHOW_CAMERAS=1` displays the exact `320 x 240` images given to the policy,
enlarged with nearest-neighbour scaling. It is useful for diagnosis but adds CPU
and display load, so it is normally disabled during final timing/evaluation.

### 10.3 Stage 3: controlled real motion

The following command documents one final microwave experiment. It is an
experiment-specific reference, not a universal safe configuration:

```bash
CHECKPOINT=data/checkpoints/<real_model>.ckpt \
ROBOT_IP=192.168.2.100 \
ENABLE_MOTION=1 \
ASYNC_INFERENCE=1 \
POLICY_HZ=10 \
EXEC_HORIZON=6 \
NUM_INFERENCE_STEPS=12 \
KP_POS=0.40 \
KP_ROT=0.30 \
MAX_JOINT_VEL=0.08 \
MAX_TARGET_SPEED=0.12 \
MAX_POS_ERROR_STOP=0.12 \
MAX_ROT_ERROR_STOP=0.80 \
WRIST_CAMERA_CONFIG=ur10_real_robot/camera/config/d455_config_microwave_auto.json \
GRIPPER_QUANTIZE=1 \
GRIPPER_QUANTIZE_VALUES="-0.2 0.30 0.70" \
GRIPPER_QUANTIZE_THRESHOLDS="0.15 0.35" \
DEBUG_GRIPPER_PLAN=1 \
./ur10_real_robot/run_diffusion_real.sh
```

The program asks for the exact word `YES` before enabling any physical actuator
path. This confirmation is the last software check, not a guarantee of safety.
Begin with the teach-pendant speed slider low and increase it only after
controlled tests.

`MAX_RUN_TIME=0`, which is the launcher default, means no automatic time limit.
Stop with `Ctrl+C` when required.

## 11. Understand Real-Time Execution

### 11.1 Horizons and action frequency

- `EXEC_HORIZON=6` means at most six predicted actions are placed in the active
  execution buffer.
- `POLICY_HZ=10` is the frequency at which buffered actions are consumed. It
  does **not** mean that ten complete diffusion inferences finish each second.
- `NUM_INFERENCE_STEPS=12` is the number of denoising iterations used to sample
  one plan. More steps generally cost more CPU time.

### 11.2 Asynchronous inference

With `ASYNC_INFERENCE=1`, two activities overlap:

```text
Robot/control thread:  execute actions from current plan A -------- switch to B
Policy thread:             capture observation -> compute plan B --- ready
```

The robot continues executing buffered actions from plan A while the CPU
computes plan B. When B is ready, it replaces the active buffer. This avoids a
complete stop during every slow CPU inference.

The observation used for B was captured at the start of its computation. It is
therefore older when B becomes ready. Faster robot motion increases the distance
travelled during this latency and can reduce precision near contacts.

With asynchronous inference disabled, plan generation blocks the replanning
path. It is easier to interpret but can cause long pauses and abrupt stop/start
motion on a CPU-only computer.

### 11.3 Safety stops

The runner checks, among other conditions:

- target position error;
- target orientation error;
- joint velocity limits;
- Cartesian target speed;
- control-loop timing.

A safety stop is latched for the current run. Stop the program, identify the
cause, and restart from a known state. Do not simply raise a threshold because a
run stopped; that can hide a wrong frame, stale plan, moved setup, or bad policy
prediction.

`IGNORE_ACTION_ORIENTATION=1` is only a diagnostic option. It changes the
control problem and should not be used as the final evaluation of a policy
trained with orientation actions.

### 11.4 Gripper post-processing

Use `GRIPPER_QUANTIZE=1` only when the demonstrations were recorded with the
same discrete command states. Quantization maps uncertain predictions back to
the known open, narrow, and grasp commands.

Gripper latch and close-boost options are experimental workarounds. Keep them
disabled unless they are explicitly part of a documented experiment. They can
make one benchmark look better while hiding inconsistent training targets.

## 12. Where the Important Code Lives

### 12.1 Teleoperation path

```text
Touch ROS 2 driver
  -> target pose topic
  -> run_real_teleop.py or test_UR10e_touch.py
  -> Cartesian servo / Pinocchio kinematics
  -> fake, MuJoCo, or speedj robot backend
  -> episode recorder
  -> Zarr dataset
```

| File or directory | Responsibility |
|---|---|
| `ros2_WS/src/touch_ros2_driver/` | Reads the Touch device and publishes its pose/buttons |
| `ur10_real_robot/run_real_teleop.py` | Main real teleoperation, UI, safety, and recording loop |
| `ur10_real_robot/teleop/` | Real Touch target handling and dataset recorder |
| `ur10_real_robot/robot/` | Fake and speedj UR10 backends |
| `ur10_real_robot/gripper/` | OnRobot Modbus/TCP communication and width mapping |
| `ur10_real_robot/camera/` | RealSense capture, crop, resize, and dual-camera rig |
| `dp_mujoco/teleop/test_UR10e_touch.py` | Main MuJoCo teleoperation and recording loop |

### 12.2 Training path

```text
Hydra train config
  -> training workspace
  -> GenericImageDataset reads Zarr
  -> image encoder + diffusion backbone
  -> optimizer and validation
  -> checkpoint
```

| File or directory | Responsibility |
|---|---|
| `diffusion_policy/train.py` | Hydra training entry point |
| `diffusion_policy/diffusion_policy/dataset/` | Loads and samples Zarr episodes |
| `diffusion_policy/diffusion_policy/policy/` | Complete image-conditioned policies |
| `diffusion_policy/diffusion_policy/model/` | U-Net, Transformer, vision, and diffusion modules |
| `diffusion_policy/diffusion_policy/workspace/` | Training loops, validation, logging, and checkpoints |

The ResNet visual encoder and diffusion backbone are trained end to end. The
camera images are not converted to hand-written object coordinates first.

### 12.3 Real execution path

```text
Checkpoint + latest observations
  -> policy loader
  -> predicted 8D action sequence
  -> plan buffer
  -> Cartesian target filtering and safety checks
  -> Pinocchio Jacobian controller
  -> UR10 speedj commands + gripper Modbus commands
```

| File or directory | Responsibility |
|---|---|
| `ur10_real_robot/policy_exec/policy_loader.py` | Restores policy, EMA weights, and normalizer |
| `ur10_real_robot/policy_exec/real_observation_builder.py` | Builds policy observations from cameras and robot state |
| `ur10_real_robot/policy_exec/run_diffusion_real.py` | Inference, buffering, control, gripper, safety, and logs |
| `ur10_real_robot/control/` | Cartesian control and safety helpers |

## 13. Starting a New Task

Use this order rather than changing many parameters at once:

1. Define the initial scene, allowed object variation, success condition, and
   failure conditions.
2. Fix the camera positions, crops, lighting, robot home pose, gripper states,
   and target box.
3. Create a new dataset name.
4. Record a few demonstrations and inspect every one.
5. Correct the collection method before recording the full dataset.
6. Create or update the matching task and training configurations.
7. Train on the server and compare candidate checkpoints.
8. Run fake, observation-only, and low-speed physical tests in that order.
9. Freeze the checkpoint and execution parameters before reporting evaluation
   trials.

Create a new dataset and checkpoint when the task interface changes. Do not mix
episodes with different image crops, lighting protocols, quaternion orders,
gripper semantics, or object objectives into one dataset without a deliberate
experimental reason.

## 14. Common Problems

### `ModuleNotFoundError: No module named ...`

Return to the repository root and activate the environment:

```bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
conda activate microwave_dp
export PYTHONPATH="$PWD${PYTHONPATH:+:$PYTHONPATH}"
```

### `No route to host` for the UR10 or gripper

The computer is on the wrong network, the IP changed, the cable is disconnected,
or the device is off. Verify with `ip address` and `ping`. Do not change the code
until the network route works.

### RealSense camera not found

Close other programs using the cameras, reconnect the USB cable, then run:

```bash
rs-enumerate-devices
lsusb -t
```

Each RealSense should ideally use a USB 3 connection. A camera shown at `480M`
is connected as USB 2 and is more likely to time out.

### Advanced JSON configuration fails once

The camera code retries configuration loading. A first failed attempt followed
by `Advanced JSON config loaded` is acceptable. If all attempts fail, the run
stops rather than silently collecting images with the wrong settings.

### Camera image is black, frozen, or different from training

Stop recording. Check USB bandwidth, serial numbers, crop, JSON configuration,
light source, and physical camera pose. Use the live-vs-dataset comparison tool
before collecting or evaluating more episodes.

### Robot is connected but does not move

Check the startup summary. `ENABLE_MOTION=0` deliberately blocks arm commands.
The gripper motion flag now follows `ENABLE_MOTION` by default, so a dry run also
keeps the gripper still unless it is explicitly enabled.

### The robot stops on position or orientation error

Treat the stop as evidence, not an inconvenience. Check the printed raw target,
limited target, measured pose, quaternion convention, camera/setup alignment,
and checkpoint. Restart only after the cause is understood.

### CPU inference is slow

Measure it with `scripts/benchmark_policy_inference.py`. A smaller U-Net, fewer
sampling steps, lower robot speed, or asynchronous inference may improve the
timing/precision trade-off. Changing sampling steps can also change policy
quality, so evaluate the complete task again after any change.

### Validation loss rises while training loss falls

This is a sign of overfitting. Compare earlier checkpoints under the same test
protocol. Real-robot success, trajectory quality, safety stops, and grasp quality
remain important because validation loss alone does not measure closed-loop task
performance.

## 15. Non-Negotiable Safety Rules

- Never run an unknown checkpoint first with real motion enabled.
- Never bypass the exact `YES` confirmation in the real runner.
- Never stand inside the UR10 workspace.
- Keep the emergency stop reachable and the initial speed slider low.
- Never increase safety thresholds merely to make an error disappear.
- Never collect data with a frozen or incorrect camera stream.
- Never change the physical setup halfway through a dataset without documenting
  and validating that change.
- Stop after a collision, camera failure, stale plan, or unusual gripper motion.
- Keep raw datasets and evaluation records backed up before editing them.

## 16. Minimal Command Index

```bash
# Simulation teleoperation
./launch_all.sh

# Real teleoperation (full parameters are in Section 6)
REAL_DATASET_PRESET=1 \
ENABLE_MOTION=1 \
DATASET_PATH=data/datasets/<new_dataset>.zarr \
./ur10_real_robot/run_teleop.sh

# Dataset structure
python scripts/check_zarr.py data/datasets/<dataset>.zarr

# Dataset replay
python scripts/replay_zarr.py data/datasets/<dataset>.zarr

# Offline checkpoint timing
PYTHONPATH=. python scripts/benchmark_policy_inference.py \
  data/checkpoints/<model>.ckpt --device cpu

# Real checkpoint, completely fake test
CHECKPOINT=data/checkpoints/<model>.ckpt \
BACKEND=fake CAMERA_MODE=fake ENABLE_MOTION=0 \
GRIPPER_ENABLE=0 GRIPPER_MOTION_ENABLE=0 \
MAX_RUN_TIME=10 ./ur10_real_robot/run_diffusion_real.sh
```

When a command behaves differently from this guide, first record the Git commit,
the complete command, and the terminal output. That information is usually more
useful than changing several parameters at random.
