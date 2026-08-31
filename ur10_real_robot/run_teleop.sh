#!/usr/bin/env bash
set -Eeuo pipefail

# Launch Touch-based teleoperation for either the fake backend or the UR10.
# Configuration is supplied through environment variables so one recorded
# dataset can be reproduced without editing Python source files.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
export PROJECT_ROOT

show_help() {
  cat <<'EOF'
Usage: ./ur10_real_robot/run_teleop.sh

Safe default:
  Fake robot, no cameras, no gripper, no recording, no physical motion.

Final real-data preset (still motion-disabled unless explicitly enabled):
  REAL_DATASET_PRESET=1 DATASET_PATH=data/datasets/<name>.zarr \
    ./ur10_real_robot/run_teleop.sh

To permit physical arm motion, add REAL_BACKEND=speedj ENABLE_MOTION=1. The
launcher asks for an explicit YES before it starts the control process.

Useful environment variables:
  CONDA_ENV_NAME=microwave_dp  Environment used when none is active
  PYTHON_BIN=/path/to/python   Explicit Python interpreter
  TOUCH_BUILD=auto             auto, 1 (always build), or 0 (never build)
  START_TOUCH_DRIVER=1         Set to 0 if /touch/pose already exists
  PREFLIGHT_ONLY=1             Validate configuration without opening hardware

All available defaults are defined near the top of this script. See
README_CODE.md for the full data-collection command and safety procedure.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi
(( $# == 0 )) || { show_help >&2; exit 2; }

# shellcheck source=scripts/lib/launch_common.sh
source "$PROJECT_ROOT/scripts/lib/launch_common.sh"

export REAL_DATASET_PRESET="${REAL_DATASET_PRESET:-0}"

# This preset configures the final sensor/recording interface. It deliberately
# does not authorize physical motion; ENABLE_MOTION=1 remains explicit.
if launch_is_enabled "$REAL_DATASET_PRESET"; then
  export REAL_BACKEND="${REAL_BACKEND:-speedj}"
  export ROBOT_IP="${ROBOT_IP:-192.168.2.100}"
  export CONTROL_HZ="${CONTROL_HZ:-50}"
  export TCP_OFFSET="${TCP_OFFSET:-0 0 0.022}"
  export BASE_RZ_DEG="${BASE_RZ_DEG:-180}"
  export KP_POS="${KP_POS:-0.40}"
  export KP_ROT="${KP_ROT:-0.30}"
  export MAX_JOINT_VEL="${MAX_JOINT_VEL:-0.10}"
  export ALPHA_DQ="${ALPHA_DQ:-0.03}"
  export SPEEDJ_A="${SPEEDJ_A:-0.04}"
  export POSITION_SCALE="${POSITION_SCALE:-0.50}"
  export MAX_TARGET_SPEED="${MAX_TARGET_SPEED:-0.08}"
  export MAX_POS_ERROR_STOP="${MAX_POS_ERROR_STOP:-0.20}"
  export MAX_ROT_ERROR_STOP="${MAX_ROT_ERROR_STOP:-0.60}"
  export TARGET_ALPHA_POS="${TARGET_ALPHA_POS:-0.45}"
  export TARGET_ALPHA_ROT="${TARGET_ALPHA_ROT:-0.25}"
  export TOUCH_AXIS_MAP="${TOUCH_AXIS_MAP:-swap_xy_neg_y}"
  export TOUCH_ROT_MAP="${TOUCH_ROT_MAP:-same_as_position}"
  export TOUCH_ROT_APPLY="${TOUCH_ROT_APPLY:-world}"
  export TOUCH_ROT_METHOD="${TOUCH_ROT_METHOD:-matrix}"
  export HOME_RESET_MAX_JOINT_VEL="${HOME_RESET_MAX_JOINT_VEL:-0.08}"
  export GRIPPER_ENABLE="${GRIPPER_ENABLE:-1}"
  export GRIPPER_CONTROL_MODE="${GRIPPER_CONTROL_MODE:-button}"
  export GRIPPER_OPEN_WIDTH_MM="${GRIPPER_OPEN_WIDTH_MM:-85}"
  export INITIAL_GRIPPER_WIDTH_MM="${INITIAL_GRIPPER_WIDTH_MM:-85}"
  export GRIPPER_CLOSE_WIDTH_MM="${GRIPPER_CLOSE_WIDTH_MM:-30}"
  export GRIPPER_FORCE_N="${GRIPPER_FORCE_N:-12}"
  export GRIPPER_COMMAND_MODE="${GRIPPER_COMMAND_MODE:-continuous}"
  export GRIPPER_STEP_VALUES="${GRIPPER_STEP_VALUES:--0.2 0.30 0.70}"
  export RECORD_GRIPPER_QPOS_SOURCE="${RECORD_GRIPPER_QPOS_SOURCE:-actual_width}"
  export RECORD_GRIPPER_ACTION_SOURCE="${RECORD_GRIPPER_ACTION_SOURCE:-actual_width}"
  export CAMERA_ENABLE="${CAMERA_ENABLE:-1}"
  export SHOW_CAMERAS="${SHOW_CAMERAS:-1}"
  export RECORD_ENABLE="${RECORD_ENABLE:-1}"
  export NO_ADVANCED_CONFIG="${NO_ADVANCED_CONFIG:-0}"
  export TOP_SERIAL="${TOP_SERIAL:-332322072359}"
  export WRIST_SERIAL="${WRIST_SERIAL:-043422251624}"
  export TOP_CAMERA_CONFIG="${TOP_CAMERA_CONFIG:-ur10_real_robot/camera/config/d435_config_dataset.json}"
  export WRIST_CAMERA_CONFIG="${WRIST_CAMERA_CONFIG:-ur10_real_robot/camera/config/d455_config_dataset.json}"
  export TOP_CROP="${TOP_CROP:-40 30 560 420}"
  export WRIST_CROP="${WRIST_CROP:-0 0 640 480}"
  export DATASET_WIDTH="${DATASET_WIDTH:-320}"
  export DATASET_HEIGHT="${DATASET_HEIGHT:-240}"
  export RECORD_FREQ="${RECORD_FREQ:-10}"
  export MIN_EPISODE_STEPS="${MIN_EPISODE_STEPS:-5}"
fi

export REAL_BACKEND="${REAL_BACKEND:-fake}"
export ENABLE_MOTION="${ENABLE_MOTION:-0}"
export ROBOT_IP="${ROBOT_IP:-192.168.2.100}"
export CONTROL_HZ="${CONTROL_HZ:-50}"
export TCP_OFFSET="${TCP_OFFSET:-0 0 0}"
export BASE_RZ_DEG="${BASE_RZ_DEG:-180}"
export KP_POS="${KP_POS:-0.35}"
export KP_ROT="${KP_ROT:-0.0}"
export MAX_JOINT_VEL="${MAX_JOINT_VEL:-0.08}"
export ALPHA_DQ="${ALPHA_DQ:-0.04}"
export SPEEDJ_A="${SPEEDJ_A:-0.06}"
export POSITION_SCALE="${POSITION_SCALE:-0.15}"
export MAX_TARGET_SPEED="${MAX_TARGET_SPEED:-0.05}"
export MAX_POS_ERROR_STOP="${MAX_POS_ERROR_STOP:-0.20}"
export MAX_ROT_ERROR_STOP="${MAX_ROT_ERROR_STOP:-0.60}"
export TARGET_ALPHA_POS="${TARGET_ALPHA_POS:-0.25}"
export TARGET_ALPHA_ROT="${TARGET_ALPHA_ROT:-0.15}"
export TOUCH_AXIS_MAP="${TOUCH_AXIS_MAP:-swap_xy_neg_y}"
export TOUCH_ROT_MAP="${TOUCH_ROT_MAP:-same_as_position}"
export TOUCH_ROT_APPLY="${TOUCH_ROT_APPLY:-world}"
export TOUCH_ROT_METHOD="${TOUCH_ROT_METHOD:-matrix}"
export WATCHDOG_TIMEOUT="${WATCHDOG_TIMEOUT:-0.30}"
export HOME_RESET_KP="${HOME_RESET_KP:-1.0}"
export HOME_RESET_MAX_JOINT_VEL="${HOME_RESET_MAX_JOINT_VEL:-0.08}"
export HOME_RESET_THRESHOLD_DEG="${HOME_RESET_THRESHOLD_DEG:-0.5}"
export GRIPPER_ENABLE="${GRIPPER_ENABLE:-0}"
export GRIPPER_MOTION_ENABLE="${GRIPPER_MOTION_ENABLE:-$ENABLE_MOTION}"
export GRIPPER_IP="${GRIPPER_IP:-192.168.1.1}"
export GRIPPER_PORT="${GRIPPER_PORT:-502}"
export GRIPPER_OPEN_WIDTH_MM="${GRIPPER_OPEN_WIDTH_MM:-85}"
export INITIAL_GRIPPER_WIDTH_MM="${INITIAL_GRIPPER_WIDTH_MM:-$GRIPPER_OPEN_WIDTH_MM}"
export GRIPPER_CLOSE_WIDTH_MM="${GRIPPER_CLOSE_WIDTH_MM:-35}"
export GRIPPER_FORCE_N="${GRIPPER_FORCE_N:-8}"
export GRIPPER_COMMAND_PERIOD="${GRIPPER_COMMAND_PERIOD:-0.10}"
export GRIPPER_DEADBAND_MM="${GRIPPER_DEADBAND_MM:-1.0}"
export GRIPPER_CONTROL_MODE="${GRIPPER_CONTROL_MODE:-button}"
export GRIPPER_COMMAND_MODE="${GRIPPER_COMMAND_MODE:-continuous}"
export GRIPPER_STEP_VALUES="${GRIPPER_STEP_VALUES:--0.2 0.30 0.70}"
export RECORD_GRIPPER_QPOS_SOURCE="${RECORD_GRIPPER_QPOS_SOURCE:-actual_width}"
export RECORD_GRIPPER_ACTION_SOURCE="${RECORD_GRIPPER_ACTION_SOURCE:-actual_width}"
export CAMERA_ENABLE="${CAMERA_ENABLE:-0}"
export CAMERA_MODE="${CAMERA_MODE:-realsense}"
export TOP_SERIAL="${TOP_SERIAL:-332322072359}"
export WRIST_SERIAL="${WRIST_SERIAL:-043422251624}"
export TOP_CAMERA_CONFIG="${TOP_CAMERA_CONFIG:-ur10_real_robot/camera/config/d435_config_dataset.json}"
export WRIST_CAMERA_CONFIG="${WRIST_CAMERA_CONFIG:-ur10_real_robot/camera/config/d455_config_dataset.json}"
export NO_ADVANCED_CONFIG="${NO_ADVANCED_CONFIG:-0}"
export DATASET_WIDTH="${DATASET_WIDTH:-320}"
export DATASET_HEIGHT="${DATASET_HEIGHT:-240}"
export TOP_CROP="${TOP_CROP:-}"
export WRIST_CROP="${WRIST_CROP:-}"
export RECORD_ENABLE="${RECORD_ENABLE:-0}"
export SHOW_CAMERAS="${SHOW_CAMERAS:-0}"
export RECORD_FREQ="${RECORD_FREQ:-10}"
export MIN_EPISODE_STEPS="${MIN_EPISODE_STEPS:-3}"
export DATASET_APPEND_LATEST="${DATASET_APPEND_LATEST:-0}"
export DATASET_ROOT="${DATASET_ROOT:-data/datasets}"
export DATASET_PATH="${DATASET_PATH:-}"
export TOUCH_BUILD="${TOUCH_BUILD:-auto}"
export START_TOUCH_DRIVER="${START_TOUCH_DRIVER:-1}"
export TOUCH_START_TIMEOUT="${TOUCH_START_TIMEOUT:-15}"
export PREFLIGHT_ONLY="${PREFLIGHT_ONLY:-0}"

case "$REAL_BACKEND" in
  fake|speedj) ;;
  *) launch_die "REAL_BACKEND must be 'fake' or 'speedj'." ;;
esac
if launch_is_enabled "$ENABLE_MOTION" && [[ "$REAL_BACKEND" != "speedj" ]]; then
  launch_die "ENABLE_MOTION=1 requires REAL_BACKEND=speedj."
fi
if launch_is_enabled "$GRIPPER_MOTION_ENABLE" && ! launch_is_enabled "$GRIPPER_ENABLE"; then
  launch_die "GRIPPER_MOTION_ENABLE=1 requires GRIPPER_ENABLE=1."
fi
if launch_is_enabled "$RECORD_ENABLE" && [[ -z "$DATASET_PATH" ]] &&
   ! launch_is_enabled "$DATASET_APPEND_LATEST"; then
  launch_warn "No DATASET_PATH was supplied; a timestamped dataset will be created."
fi

TOP_CAMERA_CONFIG="$(launch_resolve_project_path "$TOP_CAMERA_CONFIG")"
WRIST_CAMERA_CONFIG="$(launch_resolve_project_path "$WRIST_CAMERA_CONFIG")"
DATASET_ROOT="$(launch_resolve_project_path "$DATASET_ROOT")"
if [[ -n "$DATASET_PATH" ]]; then
  DATASET_PATH="$(launch_resolve_project_path "$DATASET_PATH")"
fi
export TOP_CAMERA_CONFIG WRIST_CAMERA_CONFIG DATASET_ROOT DATASET_PATH

read -r -a tcp_offset <<<"$TCP_OFFSET"
read -r -a gripper_step_values <<<"$GRIPPER_STEP_VALUES"
(( ${#tcp_offset[@]} == 3 )) || launch_die "TCP_OFFSET must contain exactly 3 values."
(( ${#gripper_step_values[@]} == 3 )) || launch_die "GRIPPER_STEP_VALUES must contain OPEN, NARROW, and GRASP."

top_crop=()
wrist_crop=()
if [[ -n "$TOP_CROP" ]]; then
  read -r -a top_crop <<<"$TOP_CROP"
  (( ${#top_crop[@]} == 4 )) || launch_die "TOP_CROP must contain 4 integers."
fi
if [[ -n "$WRIST_CROP" ]]; then
  read -r -a wrist_crop <<<"$WRIST_CROP"
  (( ${#wrist_crop[@]} == 4 )) || launch_die "WRIST_CROP must contain 4 integers."
fi

launch_select_python
launch_source_ros2
launch_prepare_touch_workspace
launch_require_file "$PROJECT_ROOT/dp_mujoco/models/universal_robots_ur10e/ur10_d455_support_rg2ft_fixed_gripper.urdf" "UR10 URDF"
if [[ "$CAMERA_MODE" == "realsense" ]] && ! launch_is_enabled "$NO_ADVANCED_CONFIG" &&
   { launch_is_enabled "$CAMERA_ENABLE" || launch_is_enabled "$RECORD_ENABLE"; }; then
  launch_require_file "$TOP_CAMERA_CONFIG" "top-camera JSON configuration"
  launch_require_file "$WRIST_CAMERA_CONFIG" "wrist-camera JSON configuration"
fi
launch_require_python_modules numpy cv2 rclpy pinocchio zarr pyrealsense2 pymodbus urx

advanced_status="enabled"
launch_is_enabled "$NO_ADVANCED_CONFIG" && advanced_status="disabled"

cat <<EOF
-------------------------------------------
UR10 REAL TELEOP LAUNCHER
-------------------------------------------
backend          : $REAL_BACKEND
enable motion    : $ENABLE_MOTION
robot ip         : $ROBOT_IP
control hz       : $CONTROL_HZ
tcp offset       : $TCP_OFFSET
base rz deg      : $BASE_RZ_DEG
kp pos/rot       : $KP_POS / $KP_ROT
max joint vel    : $MAX_JOINT_VEL
position scale   : $POSITION_SCALE
max target speed : $MAX_TARGET_SPEED
max pos err stop : $MAX_POS_ERROR_STOP
max rot err stop : $MAX_ROT_ERROR_STOP
target alphas    : $TARGET_ALPHA_POS / $TARGET_ALPHA_ROT
touch axis map   : $TOUCH_AXIS_MAP
touch rot map    : $TOUCH_ROT_MAP
gripper          : $GRIPPER_ENABLE motion=$GRIPPER_MOTION_ENABLE
gripper mode     : $GRIPPER_CONTROL_MODE / $GRIPPER_COMMAND_MODE
gripper steps    : $GRIPPER_STEP_VALUES
initial grip     : $INITIAL_GRIPPER_WIDTH_MM mm
record grip q    : $RECORD_GRIPPER_QPOS_SOURCE
record grip act  : $RECORD_GRIPPER_ACTION_SOURCE
camera           : $CAMERA_ENABLE mode=$CAMERA_MODE
advanced config  : $advanced_status
record           : $RECORD_ENABLE at $RECORD_FREQ Hz
dataset path     : ${DATASET_PATH:-auto}
show cameras     : $SHOW_CAMERAS
-------------------------------------------
EOF

if launch_is_enabled "$PREFLIGHT_ONLY"; then
  launch_info "Preflight passed; no hardware process was started."
  exit 0
fi

motion_args=()
gripper_args=()
gripper_motion_args=()
camera_args=()
record_args=()
show_camera_args=()
advanced_args=()
dataset_path_args=()
append_latest_args=()
top_crop_args=()
wrist_crop_args=()

launch_is_enabled "$ENABLE_MOTION" && motion_args+=(--enable-motion)
launch_is_enabled "$GRIPPER_ENABLE" && gripper_args+=(--gripper-enable)
launch_is_enabled "$GRIPPER_MOTION_ENABLE" &&
  gripper_motion_args+=(--gripper-motion-enable)
launch_is_enabled "$CAMERA_ENABLE" && camera_args+=(--camera-enable)
launch_is_enabled "$RECORD_ENABLE" && record_args+=(--record-enable)
launch_is_enabled "$SHOW_CAMERAS" && show_camera_args+=(--show-cameras)
launch_is_enabled "$NO_ADVANCED_CONFIG" && advanced_args+=(--no-advanced-config)
launch_is_enabled "$DATASET_APPEND_LATEST" &&
  append_latest_args+=(--append-latest-dataset)
[[ -n "$DATASET_PATH" ]] && dataset_path_args+=(--dataset-path "$DATASET_PATH")
(( ${#top_crop[@]} > 0 )) && top_crop_args+=(--top-crop "${top_crop[@]}")
(( ${#wrist_crop[@]} > 0 )) && wrist_crop_args+=(--wrist-crop "${wrist_crop[@]}")

cleanup() {
  launch_stop_touch_driver
}
trap cleanup EXIT INT TERM

launch_start_touch_driver
launch_info "Starting teleoperation. Press Ctrl+C to stop."
cd "$PROJECT_ROOT"
teleop_command=(
  "$PYTHON_BIN"
  -m
  ur10_real_robot.run_real_teleop
  --backend "$REAL_BACKEND"
  "${motion_args[@]}"
  --robot-ip "$ROBOT_IP"
  --control-hz "$CONTROL_HZ"
  --tcp-offset "${tcp_offset[@]}"
  --base-rz-deg "$BASE_RZ_DEG"
  --kp-pos "$KP_POS"
  --kp-rot "$KP_ROT"
  --max-joint-vel "$MAX_JOINT_VEL"
  --alpha-dq "$ALPHA_DQ"
  --speedj-a "$SPEEDJ_A"
  --position-scale "$POSITION_SCALE"
  --max-target-speed "$MAX_TARGET_SPEED"
  --max-pos-error-stop "$MAX_POS_ERROR_STOP"
  --max-rot-error-stop "$MAX_ROT_ERROR_STOP"
  --target-alpha-pos "$TARGET_ALPHA_POS"
  --target-alpha-rot "$TARGET_ALPHA_ROT"
  --touch-axis-map "$TOUCH_AXIS_MAP"
  --touch-rot-map "$TOUCH_ROT_MAP"
  --touch-rot-apply "$TOUCH_ROT_APPLY"
  --touch-rot-method "$TOUCH_ROT_METHOD"
  --watchdog-timeout "$WATCHDOG_TIMEOUT"
  --home-reset-kp "$HOME_RESET_KP"
  --home-reset-max-joint-vel "$HOME_RESET_MAX_JOINT_VEL"
  --home-reset-threshold-deg "$HOME_RESET_THRESHOLD_DEG"
  "${gripper_args[@]}"
  "${gripper_motion_args[@]}"
  --gripper-ip "$GRIPPER_IP"
  --gripper-port "$GRIPPER_PORT"
  --gripper-open-width-mm "$GRIPPER_OPEN_WIDTH_MM"
  --initial-gripper-width-mm "$INITIAL_GRIPPER_WIDTH_MM"
  --gripper-close-width-mm "$GRIPPER_CLOSE_WIDTH_MM"
  --gripper-force-n "$GRIPPER_FORCE_N"
  --gripper-command-period "$GRIPPER_COMMAND_PERIOD"
  --gripper-deadband-mm "$GRIPPER_DEADBAND_MM"
  --gripper-control-mode "$GRIPPER_CONTROL_MODE"
  --gripper-command-mode "$GRIPPER_COMMAND_MODE"
  --gripper-step-values "${gripper_step_values[@]}"
  --record-gripper-qpos-source "$RECORD_GRIPPER_QPOS_SOURCE"
  --record-gripper-action-source "$RECORD_GRIPPER_ACTION_SOURCE"
  "${camera_args[@]}"
  "${record_args[@]}"
  "${show_camera_args[@]}"
  "${advanced_args[@]}"
  "${dataset_path_args[@]}"
  "${append_latest_args[@]}"
  --camera-mode "$CAMERA_MODE"
  --top-serial "$TOP_SERIAL"
  --wrist-serial "$WRIST_SERIAL"
  --top-camera-config "$TOP_CAMERA_CONFIG"
  --wrist-camera-config "$WRIST_CAMERA_CONFIG"
  --dataset-width "$DATASET_WIDTH"
  --dataset-height "$DATASET_HEIGHT"
  --dataset-root "$DATASET_ROOT"
  --min-episode-steps "$MIN_EPISODE_STEPS"
  "${top_crop_args[@]}"
  "${wrist_crop_args[@]}"
  --record-freq "$RECORD_FREQ"
)
"${teleop_command[@]}"
