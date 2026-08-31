# Real Diffusion Policy Execution

This package contains checkpoint loading, observation construction,
asynchronous inference, Cartesian control, gripper commands, and safety checks
for the physical UR10. Use the repository launcher instead of calling the Python
module with a machine-specific interpreter path:

```bash
CHECKPOINT=data/checkpoints/<real_model>.ckpt \
./ur10_real_robot/run_diffusion_real.sh
```

The launcher resolves paths from the Git clone, uses the active Python
environment (or activates `microwave_dp`), validates required files and imports,
and forwards experiment variables to
`ur10_real_robot.policy_exec.run_diffusion_real`.

Follow this order for every new checkpoint:

1. Fake robot and fake cameras:

   ```bash
   CHECKPOINT=data/checkpoints/<real_model>.ckpt \
   BACKEND=fake CAMERA_MODE=fake GRIPPER_ENABLE=0 \
   MAX_RUN_TIME=10 ./ur10_real_robot/run_diffusion_real.sh
   ```

2. Real observations without actuator motion:

   ```bash
   CHECKPOINT=data/checkpoints/<real_model>.ckpt \
   BACKEND=speedj CAMERA_MODE=realsense ENABLE_MOTION=0 \
   GRIPPER_ENABLE=1 GRIPPER_MOTION_ENABLE=0 SHOW_CAMERAS=1 \
   MAX_RUN_TIME=10 ./ur10_real_robot/run_diffusion_real.sh
   ```

3. Physical motion only after both tests pass. Set `ENABLE_MOTION=1`, begin with
   the teach-pendant speed slider low, and type the exact word `YES` when asked.

The launcher defaults to no physical motion. The Python module also performs the
confirmation, so direct module execution cannot bypass this final check. Full
validated experiment parameters and troubleshooting are in
[`README_CODE.md`](../../README_CODE.md).
