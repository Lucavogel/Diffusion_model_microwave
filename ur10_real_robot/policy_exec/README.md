# Real Diffusion Policy Execution

This folder contains the real-robot equivalent of `dp_mujoco/policy_exec`.

The safe test order is:

1. Fake robot + fake cameras, no real hardware:

```bash
/home/luca/venvs/mujoco_ros/bin/python \
  -m ur10_real_robot.policy_exec.run_diffusion_real \
  --checkpoint data/checkpoints/u_net_small_moredata.ckpt \
  --backend fake \
  --camera-mode fake \
  --max-run-time 10 \
  --debug-timing
```

2. Real robot connection, no motion, fake cameras:

```bash
/home/luca/venvs/mujoco_ros/bin/python \
  -m ur10_real_robot.policy_exec.run_diffusion_real \
  --checkpoint data/checkpoints/u_net_small_moredata.ckpt \
  --backend speedj \
  --robot-ip 192.168.2.100 \
  --camera-mode fake \
  --max-run-time 10
```

3. Real cameras, real robot connection, no motion:

```bash
/home/luca/venvs/mujoco_ros/bin/python \
  -m ur10_real_robot.policy_exec.run_diffusion_real \
  --checkpoint data/checkpoints/u_net_small_moredata.ckpt \
  --backend speedj \
  --robot-ip 192.168.2.100 \
  --camera-mode realsense \
  --top-serial SERIAL_TOP \
  --wrist-serial SERIAL_WRIST \
  --no-advanced-config \
  --max-run-time 10
```

4. Real motion only after offline/fake tests are clean:

```bash
/home/luca/venvs/mujoco_ros/bin/python \
  -m ur10_real_robot.policy_exec.run_diffusion_real \
  --checkpoint data/checkpoints/REAL_MODEL.ckpt \
  --backend speedj \
  --robot-ip 192.168.2.100 \
  --enable-motion \
  --camera-mode realsense \
  --top-serial SERIAL_TOP \
  --wrist-serial SERIAL_WRIST \
  --tcp-offset 0 0 0.022 \
  --gripper-enable \
  --gripper-motion-enable \
  --gripper-force-n 8 \
  --max-run-time 20
```

Defaults are intentionally conservative. The script prompts `YES` before real
motion is enabled.
