# eurodao_joystick_teleop

Joystick teleoperation interface for UR20 robot arm control via Logitech F710 gamepad.

## Overview

This C++ package converts raw joystick input (`/joy`) into velocity commands (`TwistStamped`). It acts as a **pure input source** in the euroDAO system architecture (Layer 4), focusing exclusively on translating human intentions into standard ROS2 messages.

**Core Philosophy:**
- **Decoupled Architecture:** This node does NOT listen to system state or arbitration decisions. It always expresses the operator's intent.
- **Single Responsibility:** Its only job is to process joystick signals and publish them. Safety blending and mode switching are handled by downstream nodes (`arbiter` and `execution`).

**Input processing pipeline:**
```
Raw Joy → Axis Mapping → Deadzone → Nonlinear Shaping → Low-pass Filter → TwistStamped
```

## Safety System

The node includes a local safety system to ensure the integrity of the input device:

| Priority | Check | Condition | Reason |
|----------|-------|-----------|--------|
| 1 | Startup delay | First 1.0s after launch | `startup_delay` |
| 2 | Joy timeout | No `/joy` message for 0.2s | `joy_timeout` |
| 3 | Deadman switch | LB button not held | `deadman_released` |

When any local safety check fails, zero twist is published and input processors are reset to prevent output jumps.

## Joystick Mapping (Logitech F710, X mode, Mode 燈不亮)

> **硬體設定提醒：**
>
> - Front switch 必須撥到 **"X" 位置** (XInput mode)
> - **Mode 燈必須是不亮的**（如果亮著，按一下 Mode 按鈕關閉）
> - 如果 joy 輸入輸出有問題（軸不動、按鈕無反應等），**請先排查硬體錯誤**：檢查 X/D 開關位置、Mode 燈狀態、電池電量、USB 無線接收器連接

### Axes → Twist Components

| Axis | Control | Twist Component | Notes |
|------|---------|----------------|-------|
| 0 (Left stick X) | Linear Y | `twist.linear.y` | |
| 1 (Left stick Y) | Linear X | `twist.linear.x` | |
| 2 (LT trigger) | Angular Y | `twist.angular.y` | Trigger mode |
| 3 (Right stick X) | Angular Z | `twist.angular.z` | Scale: -1.0 (inverted) |
| 4 (Right stick Y) | Linear Z | `twist.linear.z` | |
| 5 (RT trigger) | Angular X | `twist.angular.x` | Trigger mode |

Trigger mode converts the rest (1.0) / pressed (-1.0) range to 0.0 / 1.0 via `(1.0 - raw) / 2.0`.

### Buttons

| Button | Index | Function | Status |
|--------|-------|----------|--------|
| LB | 4 | Deadman switch | Implemented |
| Back | 6 | E-Stop (one-way latch) | Implemented |
| A | 0 | Gripper open (LB+A) | Implemented |
| B | 1 | Gripper close (LB+B) | Implemented |
| X | 2 | Speed up | TODO |
| Y | 3 | Speed down | TODO |
| Start | 7 | Go home | TODO |

E-Stop is a **one-way latch**: once triggered, it publishes `true` to `/e_stop` and cannot be cleared by this node. An external reset procedure is required.

## Input Processing

Each of the 6 twist components passes through an independent `InputProcessor`:

1. **Deadzone** (0.05): Values below threshold become 0
2. **Remapping**: Scale remaining range to [0, 1]
3. **Nonlinear shaping** (exponent 1.5): Power-law curve for fine control at low inputs
4. **Low-pass filter** (alpha 0.8): IIR smoothing — `output = 0.8 * shaped + 0.2 * previous`

## Gripper Control

One-shot position control via `JointTrajectory` messages:

- Joint: `onrobot_2fg14_finger_width`
- Open position: 0.105 (LB + A)
- Close position: 0.055 (LB + B)
- Topic: `/gripper_controller/joint_trajectory`
- Trajectory duration: 0.5s (configurable)
- **Requires deadman (LB) held** — prevents accidental gripper activation
- Each button press sends a single trajectory to the target position

## ROS2 Interfaces

### Subscriptions

| Topic | Type | Description |
|-------|------|-------------|
| `/joy` | sensor_msgs/Joy | Raw joystick input |

### Publications

| Topic | Type | Rate | Description |
|-------|------|------|-------------|
| `/teleop/twist_cmd` | geometry_msgs/TwistStamped | 50 Hz | Primary twist output (for `execution`) |
| `/teleop/cmd` | geometry_msgs/Twist | 50 Hz | Secondary twist (for `arbiter` override detection) |
| `/e_stop` | std_msgs/Bool | On event | E-Stop signal |
| `/gripper_controller/joint_trajectory` | trajectory_msgs/JointTrajectory | On event | Gripper command |
| `~/status` | std_msgs/String | 1 Hz | JSON status |

### Services

| Service | Type | Description |
|---------|------|-------------|
| `~/get_status` | std_srvs/Trigger | On-demand status query (JSON) |

## Configuration

### `config/joystick_teleop.yaml`

```yaml
joystick_teleop:
  ros__parameters:
    publish_rate_hz: 50.0
    joy_timeout_sec: 0.2
    twist_frame_id: base_link

    input_processing:
      deadzone: 0.05
      nonlinear_exponent: 1.5
      lowpass_alpha: 0.8

    axis_mapping:
      left_stick_x:  { axis: 0, component: lx, scale: 1.0, trigger_mode: false }
      left_stick_y:  { axis: 1, component: ly, scale: 1.0, trigger_mode: false }
      lt_trigger:    { axis: 2, component: ay, scale: 1.0, trigger_mode: true  }
      right_stick_x: { axis: 3, component: az, scale: -1.0, trigger_mode: false }
      right_stick_y: { axis: 4, component: lz, scale: 1.0, trigger_mode: false }
      rt_trigger:    { axis: 5, component: ax, scale: 1.0, trigger_mode: true  }

    button_mapping:
      deadman_switch: 4    # LB
      estop: 6             # Back
      gripper_open: 0      # A       (requires LB held)
      gripper_close: 1     # B       (requires LB held)
      speed_up: 2          # X       (TODO)
      speed_down: 3        # Y       (TODO)
      go_home: 7           # Start   (TODO)

    deadman_switch:
      enabled: true

    gripper:
      joint_name: onrobot_2fg14_finger_width
      limit_open: 0.105
      limit_close: 0.055
      trajectory_duration: 0.5

    safety:
      startup_delay_sec: 1.0
```

## Package Structure

```
eurodao_joystick_teleop/
├── config/
│   └── joystick_teleop.yaml
├── include/eurodao_joystick_teleop/
│   ├── joystick_teleop_node.hpp
│   ├── input_processor.hpp
│   ├── axis_mapper.hpp
│   ├── button_handler.hpp
│   ├── gripper_controller.hpp
│   └── safety_guard.hpp
├── src/
│   ├── joystick_teleop_node.cpp
│   └── joystick_teleop_node_main.cpp
└── launch/
    └── joystick_teleop.launch.py
```

## Launch

```bash
ros2 launch eurodao_joystick_teleop joystick_teleop.launch.py
```

No launch arguments — all configuration is loaded from `joystick_teleop.yaml`.

**Prerequisites:**
- **F710 硬體設定正確**：Front switch 在 X 位置、Mode 燈不亮（詳見上方 Joystick Mapping 章節）
- `earth_sensor_bringup` joystick launch must be running (provides `/joy` topic)

## Dependencies

- `rclcpp`, `sensor_msgs`, `geometry_msgs`, `std_msgs`, `std_srvs`, `trajectory_msgs`
- `joy` (exec_depend) — Joystick driver

## License

Proprietary
