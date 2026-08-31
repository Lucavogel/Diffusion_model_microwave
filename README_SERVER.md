# GPU Server and Training Setup

This guide explains how to transfer a dataset to the LIRMM GPU server, create a
persistent Docker container, install the training environment, launch a training
run, and retrieve the resulting checkpoints.

It is written for a new student with no previous Docker or GPU-server
experience. Follow the sections in order the first time.

For local installation and program usage, see
[README_ENV.md](README_ENV.md) and [README_CODE.md](README_CODE.md).

**Scope of this document:** GPU-server setup and neural-network training only.
The real robot must not be connected to the training server, and no robot motion
command is used here.

## 1. Understand the Four Layers

Training crosses four different environments:

~~~text
Local robot PC
    |
    | rsync over SSH
    v
LIRMM server host (mic-gpu1)
    |
    | Docker bind mount
    v
Docker container (/workspace)
    |
    | conda activate robodiff
    v
Python training environment
~~~

- **Local robot PC:** stores the original repository and recorded Zarr datasets.
- **Server host:** provides the GPUs, Docker, storage, SSH, and tmux.
- **Docker container:** isolates the system libraries used by Diffusion Policy.
- **Conda environment:** installs the exact Python and CUDA packages required by
  the original training code.

A Docker **image** is the template used to create a container. A Docker
**container** is the persistent instance in which commands are executed. The
Conda environment named <code>robodiff</code> lives inside that container.

## 2. Reference Configuration

The project was trained with the following setup:

| Item | Reference value |
|---|---|
| Server | <code>mic-gpu1</code> |
| Reference GPUs | 2 x NVIDIA A100 80 GB PCIe |
| Server project directory | <code>~/Diffusion-model-isaacsim</code> |
| Container project directory | <code>/workspace</code> |
| Docker base image | <code>continuumio/miniconda3</code> |
| Conda file | <code>/workspace/diffusion_policy/conda_environment.yaml</code> |
| Conda environment | <code>robodiff</code> |
| Python in the training environment | 3.9 |
| PyTorch / CUDA toolkit | 1.12.1 / 11.6 |
| Default real-policy architecture | small image-conditioned U-Net |

The local environment from <code>README_ENV.md</code> and this training
environment are intentionally different. Do not install
<code>environment_local.yml</code> in the server container. Training must use
<code>diffusion_policy/conda_environment.yaml</code>.

## 3. Commands and Prompts

Before every command block, check where the command must run:

| Prompt example | Meaning |
|---|---|
| <code>luca@local-pc:~$</code> | local robot computer |
| <code>username@mic-gpu1:~$</code> | server host |
| <code>root@container:/workspace#</code> | inside Docker |
| <code>(robodiff) root@container:/workspace#</code> | inside Docker with Conda active |

Do not run commands beginning with <code>/workspace</code> on the local PC or on
the server host. That path exists only inside the container.

## 4. One-Time Access Checks

The new student needs:

- a LIRMM server account;
- SSH access to <code>mic-gpu1</code>;
- permission to use Docker;
- permission to use at least one server GPU.

From the **local PC**, replace the username and test SSH:

~~~bash
SERVER_USER="replace_with_your_lirmm_username"
SERVER_HOST="mic-gpu1"

ssh "$SERVER_USER@$SERVER_HOST"
~~~

The historical account used during development was
<code>lvogelgesang@mic-gpu1</code>. A new student must use their own account.

Once connected to the **server host**, test Docker and the GPUs:

~~~bash
docker --version
nvidia-smi
~~~

If Docker returns a permission error, contact the server administrator. Do not
install Docker or use arbitrary <code>sudo</code> commands on a shared server.

## 5. Transfer the Code and One Dataset

Run this section on the **local PC**, not in SSH and not in Docker.

### 5.1 Select the dataset

Set the variables for the current experiment. Change only the username and
dataset name:

~~~bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"

LOCAL_REPO="$PWD"
SERVER_USER="replace_with_your_lirmm_username"
SERVER_HOST="mic-gpu1"
DATASET_NAME="real_demo_microwave_manual_light_v2_20260814.zarr"
~~~

Verify the dataset before sending several gigabytes:

~~~bash
test -d "$LOCAL_REPO/data/datasets/$DATASET_NAME" \
  && echo "Dataset found" \
  || echo "ERROR: dataset not found"

du -sh "$LOCAL_REPO/data/datasets/$DATASET_NAME"
ls -la "$LOCAL_REPO/data/datasets/$DATASET_NAME"
~~~

A valid Zarr v2 dataset normally contains <code>.zgroup</code>,
<code>data/</code>, and <code>meta/</code>.

Record the exact source-code revision used for the experiment:

~~~bash
git branch --show-current
git rev-parse HEAD
git status --short
~~~

### 5.2 Create the remote directories

~~~bash
ssh "$SERVER_USER@$SERVER_HOST" \
  'mkdir -p ~/Diffusion-model-isaacsim/data/datasets'
~~~

### 5.3 Transfer only the required source files

The project may contain local virtual environments, old outputs, and many large
datasets. Do not copy all of them. Send the source directories while excluding
generated files:

~~~bash
rsync -avzP \
  --exclude '.venv_dp/' \
  --exclude 'data/' \
  --exclude 'outputs/' \
  --exclude '*.egg-info/' \
  --exclude '__pycache__/' \
  "$LOCAL_REPO/configs" \
  "$LOCAL_REPO/diffusion_policy" \
  "$LOCAL_REPO/scripts" \
  "$SERVER_USER@$SERVER_HOST:~/Diffusion-model-isaacsim/"
~~~

Then transfer only the selected dataset:

~~~bash
rsync -avzP \
  "$LOCAL_REPO/data/datasets/$DATASET_NAME" \
  "$SERVER_USER@$SERVER_HOST:~/Diffusion-model-isaacsim/data/datasets/"
~~~

Running the same commands again updates changed files and resumes most
interrupted transfers. An <code>rsync</code> code 23 means that at least one file
or attribute was not transferred; read the first error instead of ignoring it.

## 6. Open a Persistent Server Session

Connect from the local PC:

~~~bash
ssh "$SERVER_USER@$SERVER_HOST"
~~~

All remaining commands in this section run on the **server host**.

Use tmux so training continues if the SSH connection or laptop closes:

~~~bash
tmux new -s dp-train
~~~

Useful tmux commands:

- detach without stopping training: press <code>Ctrl+B</code>, release, then
  press <code>D</code>;
- reconnect later: <code>tmux attach -t dp-train</code>;
- list sessions: <code>tmux ls</code>.

If the session already exists, attach to it instead of creating another one:

~~~bash
tmux attach -t dp-train
~~~

## 7. Select a GPU

On the **server host**, inspect GPU use:

~~~bash
nvidia-smi
~~~

Choose an available physical GPU index. The examples below use host GPU 0:

~~~bash
GPU_ID=0
~~~

Ask the server administrator or other users before occupying a GPU that is
already in use. The reference server contains two A100 GPUs, but availability is
not guaranteed.

When Docker exposes only one physical GPU, that GPU appears as
<code>cuda:0</code> **inside the container**, even if it was GPU 1 on the host.
Therefore the training command normally keeps
<code>training.device=cuda:0</code>.

## 8. Create the Docker Container

This section is performed once for each server account.

On the **server host**, define the project and container names:

~~~bash
PROJECT_DIR="$HOME/Diffusion-model-isaacsim"
CONTAINER_NAME="diffusion-model-$USER"
GPU_ID=0

test -d "$PROJECT_DIR/diffusion_policy" \
  && echo "Server project found" \
  || echo "ERROR: transfer the project first"
~~~

Check whether the container already exists:

~~~bash
docker ps -a --filter "name=^/$CONTAINER_NAME$"
~~~

If no matching container exists, create it:

~~~bash
docker run -it \
  --name "$CONTAINER_NAME" \
  --gpus "device=$GPU_ID" \
  --shm-size=20g \
  --mount type=bind,source="$PROJECT_DIR",target=/workspace \
  --workdir /workspace \
  continuumio/miniconda3 bash
~~~

What the options mean:

- <code>--name</code> gives the container a reusable name;
- <code>--gpus</code> exposes one selected GPU;
- <code>--shm-size=20g</code> gives PyTorch data-loader workers enough shared
  memory;
- <code>--mount</code> maps the server project to <code>/workspace</code>;
- <code>--workdir</code> opens the shell in that directory.

Do **not** add <code>--rm</code>. That option deletes the container and its Conda
environment when it stops. The bind mount makes datasets, configurations,
outputs, and checkpoints persist in the server project directory.

The official syntax is documented in the
[Docker GPU guide](https://docs.docker.com/engine/containers/gpu/) and
[Docker run reference](https://docs.docker.com/engine/containers/run/).

After the command starts, the prompt should look similar to:

~~~text
root@a1b2c3d4:/workspace#
~~~

You are now **inside Docker**.

## 9. Install the Training Environment Inside Docker

Run every command in this section **inside the container**. This setup is needed
only once because the container is persistent.

### 9.1 Install system libraries

~~~bash
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  build-essential git wget ffmpeg patchelf \
  libosmesa6-dev libgl1 libglfw3
~~~

### 9.2 Create the Conda environment

First verify that the environment file transferred correctly:

~~~bash
ls -la /workspace/diffusion_policy/conda_environment.yaml
~~~

Install the faster Conda solver, then create <code>robodiff</code> from that
file:

~~~bash
conda install -y -n base conda-libmamba-solver
conda config --set solver libmamba

conda env create \
  -f /workspace/diffusion_policy/conda_environment.yaml
~~~

This command installs Python 3.9, PyTorch 1.12.1, CUDA Toolkit 11.6,
Diffusers, Hydra, Zarr, and the other versions expected by the original
Diffusion Policy code. The official command is described in the
[Conda environment documentation](https://docs.conda.io/projects/conda/en/latest/commands/env/create.html).

Activate the environment:

~~~bash
source /opt/conda/etc/profile.d/conda.sh
conda activate robodiff
~~~

### 9.3 Register the local project and compatibility fixes

Install the source tree in editable mode:

~~~bash
python -m pip install --no-deps -e /workspace/diffusion_policy
~~~

Install the compatibility versions that were required by the final training
container:

~~~bash
python -m pip install --no-cache-dir \
  'mujoco==2.3.7' \
  'huggingface_hub==0.23.0' \
  'protobuf<5' \
  'wandb>=0.22.3'
~~~

Some server configurations mark old PyTorch shared libraries with an executable
stack. Clear that flag once:

~~~bash
for file in /opt/conda/envs/robodiff/lib/python3.9/site-packages/torch/lib/*.so; do
  patchelf --clear-execstack "$file" || true
done
~~~

## 10. Verify the Container

Still inside Docker with <code>robodiff</code> active, run:

~~~bash
python --version

python -c "import torch; print('torch:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('visible GPUs:', torch.cuda.device_count()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"

python -c "import hydra, zarr, diffusers, diffusion_policy; print('Core imports: OK')"
~~~

Expected results include:

- Python 3.9;
- PyTorch 1.12.1;
- <code>CUDA available: True</code>;
- one visible NVIDIA GPU;
- <code>Core imports: OK</code>.

Also run:

~~~bash
nvidia-smi
~~~

If CUDA is false, do not start a CPU training run accidentally. Exit Docker and
check the <code>--gpus</code> option used when the container was created.

## 11. Re-enter the Container Later

After the one-time installation, use these commands from the **server host**:

~~~bash
CONTAINER_NAME="diffusion-model-$USER"

docker start "$CONTAINER_NAME"
docker exec -it "$CONTAINER_NAME" bash
~~~

Then, **inside Docker**, activate Conda:

~~~bash
source /opt/conda/etc/profile.d/conda.sh
conda activate robodiff
cd /workspace
~~~

If Docker says that the container name already exists, this is not an error in
the project. Use <code>docker start</code> and <code>docker exec</code>; do not run
<code>docker run</code> again.

## 12. Prepare the Dataset and Hydra Configurations

Run this section inside Docker.

Select and verify the dataset:

~~~bash
cd /workspace
DATASET_NAME="real_demo_microwave_manual_light_v2_20260814.zarr"

test -d "/workspace/data/datasets/$DATASET_NAME" \
  && echo "Dataset found" \
  || echo "ERROR: dataset not found"

ls -la "/workspace/data/datasets/$DATASET_NAME"
du -sh "/workspace/data/datasets/$DATASET_NAME"
~~~

The custom Hydra configurations live in the repository-level
<code>configs/</code> directory. Copy them into the configuration package read by
<code>train.py</code>:

~~~bash
cp /workspace/configs/train/*.yaml \
  /workspace/diffusion_policy/diffusion_policy/config/

cp /workspace/configs/task/*.yaml \
  /workspace/diffusion_policy/diffusion_policy/config/task/
~~~

Verify the two final configurations:

~~~bash
ls -la \
  /workspace/diffusion_policy/diffusion_policy/config/train_e_waste_unet_real_small.yaml

ls -la \
  /workspace/diffusion_policy/diffusion_policy/config/task/e_waste_image_unet_real.yaml

grep -n "dataset_path" \
  /workspace/diffusion_policy/diffusion_policy/config/task/e_waste_image_unet_real.yaml
~~~

The dataset path written in the YAML is only a default. The explicit
<code>task.dataset_path</code> argument in the next section is authoritative and
prevents training the wrong dataset.

## 13. Launch the Training Run

The recommended first command uses the final smaller U-Net configuration. It is
substantially lighter than the original 307-million-parameter U-Net while
preserving the same observation and action interface.

Inside Docker:

~~~bash
cd /workspace
source /opt/conda/etc/profile.d/conda.sh
conda activate robodiff

DATASET_NAME="real_demo_microwave_manual_light_v2_20260814.zarr"

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
export HYDRA_FULL_ERROR=1

python /workspace/diffusion_policy/train.py \
  --config-name=train_e_waste_unet_real_small \
  task=e_waste_image_unet_real \
  task.dataset_path="/workspace/data/datasets/$DATASET_NAME" \
  training.resume=False \
  training.device=cuda:0 \
  logging.mode=disabled \
  logging.resume=False
~~~

Important details:

- omit the <code>.yaml</code> extension after <code>--config-name</code>;
- <code>training.device=cuda:0</code> refers to the GPU visible inside Docker;
- <code>logging.mode=disabled</code> trains without Weights & Biases;
- the configuration trains for 200 epochs and saves a checkpoint every 20
  epochs;
- the validation split is 10 percent of the recorded episodes;
- the explicit absolute dataset path avoids Hydra path-resolution mistakes.

The first dataset load can take several minutes because Zarr chunks are read,
decompressed, and cached. Seeing the model parameter count followed by a pause
does not by itself mean that the program has frozen.

## 14. Monitor Training Without Stopping It

Detach from tmux with <code>Ctrl+B</code>, then <code>D</code>. Training continues
on the server.

From a second SSH terminal, inspect the GPU:

~~~bash
watch -n 5 nvidia-smi
~~~

Reconnect to the training terminal later:

~~~bash
ssh "$SERVER_USER@$SERVER_HOST"
tmux attach -t dp-train
~~~

Do not run <code>docker stop</code> while training is active.

## 15. Find and Select Checkpoints

Because <code>/workspace</code> is a bind mount, outputs are available both:

- inside Docker at <code>/workspace/data/outputs/</code>;
- on the server host at
  <code>~/Diffusion-model-isaacsim/data/outputs/</code>.

Inside Docker, list the newest run:

~~~bash
LATEST_RUN=$(find /workspace/data/outputs \
  -mindepth 2 -maxdepth 2 -type d | sort | tail -n 1)

echo "$LATEST_RUN"
ls -lh "$LATEST_RUN/checkpoints"
~~~

Typical files are:

~~~text
epoch=0020-val_loss=....ckpt
epoch=0040-val_loss=....ckpt
epoch=0060-val_loss=....ckpt
epoch=0080-val_loss=....ckpt
epoch=0100-val_loss=....ckpt
latest.ckpt
~~~

Validation loss is useful for detecting severe overfitting, but it is not a
complete measure of closed-loop robot performance. In the real experiments,
checkpoints around epochs 40, 60, and 80 were often tested before selecting the
final policy. Do not automatically assume that the checkpoint with the lowest
validation loss is the best physical policy.

## 16. Retrieve a Checkpoint on the Local PC

Run this section on the **local PC**. Set the exact remote checkpoint path shown
by the previous command:

~~~bash
cd "$HOME/Stage_Lirmm/Diffusion-model-isaacsim"
mkdir -p data/checkpoints

SERVER_USER="replace_with_your_lirmm_username"
SERVER_HOST="mic-gpu1"
REMOTE_CHECKPOINT="~/Diffusion-model-isaacsim/data/outputs/YYYY.MM.DD/RUN_NAME/checkpoints/epoch=0060-val_loss=0.000.ckpt"
LOCAL_MODEL_NAME="new_real_policy.ckpt"

rsync -avzP \
  "$SERVER_USER@$SERVER_HOST:$REMOTE_CHECKPOINT" \
  "data/checkpoints/$LOCAL_MODEL_NAME"
~~~

Verify that the large file arrived completely:

~~~bash
ls -lh "data/checkpoints/$LOCAL_MODEL_NAME"
~~~

With the persistent bind-mounted container described here, <code>docker cp</code>
is unnecessary. It was used by older experiments whose container did not expose
the output directory correctly.

## 17. Optional Weights & Biases Logging

First complete one training run with <code>logging.mode=disabled</code>. To enable
online plots later, run inside Docker:

~~~bash
conda activate robodiff
wandb login
~~~

Then replace this argument in the training command:

~~~text
logging.mode=online
~~~

Never place a Weights & Biases API key in a README, shell script, Git commit, or
shared terminal log.

## 18. Troubleshooting

### Hydra cannot find the training configuration

Example symptom:

~~~text
Cannot find primary config 'train_e_waste_unet_real_small'
~~~

Copy the custom configurations again:

~~~bash
cp /workspace/configs/train/*.yaml \
  /workspace/diffusion_policy/diffusion_policy/config/
cp /workspace/configs/task/*.yaml \
  /workspace/diffusion_policy/diffusion_policy/config/task/
~~~

Use the name without <code>.yaml</code> in <code>--config-name</code>.

### Zarr PathNotFoundError

Example symptom:

~~~text
PathNotFoundError("nothing found at path ''")
~~~

Verify the exact path inside Docker:

~~~bash
find /workspace -maxdepth 3 -type d -name '*.zarr'
ls -la "/workspace/data/datasets/$DATASET_NAME"
~~~

Then pass the absolute path explicitly with
<code>task.dataset_path=/workspace/data/datasets/NAME.zarr</code>. Do not edit a
config in one directory and assume Hydra is reading that copy.

### Protobuf descriptor error

If the traceback says that descriptors cannot be created directly, run:

~~~bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
python -c "import google.protobuf; print(google.protobuf.__version__)"
~~~

The training command in this guide already exports that compatibility setting.

### CUDA out of memory

Run <code>nvidia-smi</code> on the host and inside Docker. An A100 can still have
almost no free memory when another process occupies it. Prefer another free GPU
or wait for the current job to finish. Reducing the batch size is a fallback,
but it changes the training configuration and must be recorded.

### Training appears blocked after the parameter count

Wait several minutes and inspect CPU, disk, and GPU activity. The first Zarr
cache construction can spend a long time decompressing images before the first
epoch. A <code>KeyboardInterrupt</code> inside Zarr decompression usually means
the load was interrupted, not that all demonstrations are corrupted.

### Docker container name already exists

Use:

~~~bash
docker start "diffusion-model-$USER"
docker exec -it "diffusion-model-$USER" bash
~~~

Do not create a second container unless a separate experiment genuinely needs
one.

### The Conda environment already exists

Activate it instead of recreating it:

~~~bash
source /opt/conda/etc/profile.d/conda.sh
conda activate robodiff
~~~

To update it after the YAML changes:

~~~bash
conda env update \
  -n robodiff \
  -f /workspace/diffusion_policy/conda_environment.yaml \
  --prune
~~~

### The /workspace directory is empty

The container was probably created with the wrong host directory. Exit Docker
and verify on the server host:

~~~bash
ls -la "$HOME/Diffusion-model-isaacsim"
docker inspect "diffusion-model-$USER"
~~~

Do not delete either directory while investigating the mount.

## 19. Critical Data-Safety Rules

- Never run <code>rm -rf /workspace</code>. Because it is a bind mount, this can
  delete the project, datasets, and outputs on the server host.
- Never remove the original local dataset immediately after transfer.
- Never overwrite a checkpoint without recording its run, epoch, validation
  loss, dataset name, and Git commit.
- Never start a training job on a GPU already occupied by another user.
- Never run real-robot execution from the training server.
- Keep failed and preliminary checkpoints separate from the final named model.

## 20. Short Checklist for Later Runs

After the one-time Docker and Conda installation, a normal training day is:

1. Verify the local dataset and Git commit.
2. Transfer updated source files and one dataset with <code>rsync</code>.
3. SSH to <code>mic-gpu1</code> and attach or create the tmux session.
4. Check GPU availability with <code>nvidia-smi</code>.
5. Start and enter the existing Docker container.
6. Activate <code>robodiff</code>.
7. Copy the custom Hydra configurations into the package.
8. Verify the absolute dataset path.
9. Launch training with <code>training.device=cuda:0</code>.
10. Detach from tmux and monitor the GPU.
11. Inspect candidate checkpoints around epochs 40, 60, and 80.
12. Retrieve selected checkpoints with <code>rsync</code>.
