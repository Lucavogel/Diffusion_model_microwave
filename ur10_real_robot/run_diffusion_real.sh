#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy one real-robot Diffusion Policy checkpoint. The shell layer validates
# paths and configuration; the Python runner retains the final YES confirmation
# before any physical UR10 motion.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd -- "$SCRIPT_DIR/.." && pwd)}"
export PROJECT_ROOT

show_help() {
  cat <<'EOF'
Usage:
  CHECKPOINT=data/checkpoints/<model>.ckpt \
    ./ur10_real_robot/run_diffusion_real.sh

The default connects to the configured real devices but does not move the arm
or gripper. Add ENABLE_MOTION=1 to authorize motion; the Python runner then asks
you to type YES.

Completely fake smoke test:
  CHECKPOINT=data/checkpoints/<model>.ckpt \
  BACKEND=fake CAMERA_MODE=fake GRIPPER_ENABLE=0 ENABLE_MOTION=0 \
  MAX_RUN_TIME=5 ./ur10_real_robot/run_diffusion_real.sh

Useful environment variables:
  CONDA_ENV_NAME=microwave_dp  Environment used when none is active
  PYTHON_BIN=/path/to/python   Explicit Python interpreter
  PREFLIGHT_ONLY=1             Check files/imports without opening hardware

See README_CODE.md for the complete pick-and-drop and microwave configurations.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi
(( $# == 0 )) || { show_help >&2; exit 2; }

# shellcheck source=scripts/lib/launch_common.sh
source "$PROJECT_ROOT/scripts/lib/launch_common.sh"

export CHECKPOINT="${CHECKPOINT:-}"
export ENABLE_MOTION="${ENABLE_MOTION:-0}"
export BACKEND="${BACKEND:-speedj}"
export ROBOT_IP="${ROBOT_IP:-192.168.2.100}"
export DEVICE="${DEVICE:-cpu}"

export CAMERA_MODE="${CAMERA_MODE:-realsense}"
export TOP_SERIAL="${TOP_SERIAL:-332322072359}"
export WRIST_SERIAL="${WRIST_SERIAL:-043422251624}"
export TOP_CAMERA_CONFIG="${TOP_CAMERA_CONFIG:-ur10_real_robot/camera/config/d435_config_dataset.json}"
export WRIST_CAMERA_CONFIG="${WRIST_CAMERA_CONFIG:-ur10_real_robot/camera/config/d455_config_dataset.json}"
export TOP_CROP="${TOP_CROP:-40 30 560 420}"
export WRIST_CROP="${WRIST_CROP:-0 0 640 480}"
export DATASET_WIDTH="${DATASET_WIDTH:-320}"
export DATASET_HEIGHT="${DATASET_HEIGHT:-240}"
export NO_ADVANCED_CONFIG="${NO_ADVANCED_CONFIG:-0}"

export URDF="${URDF:-dp_mujoco/models/universal_robots_ur10e/ur10_d455_support_rg2ft_fixed_gripper.urdf}"
export TCP_OFFSET="${TCP_OFFSET:-0 0 0.022}"
export BASE_RZ_DEG="${BASE_RZ_DEG:-180}"
export CONTROL_HZ="${CONTROL_HZ:-50}"
export POLICY_HZ="${POLICY_HZ:-10}"
export EXEC_HORIZON="${EXEC_HORIZON:-8}"
export NUM_INFERENCE_STEPS="${NUM_INFERENCE_STEPS:-8}"
export TORCH_NUM_THREADS="${TORCH_NUM_THREADS:-}"
export ASYNC_INFERENCE="${ASYNC_INFERENCE:-1}"
export ASYNC_HOLD_CURRENT_POSE="${ASYNC_HOLD_CURRENT_POSE:-0}"

export KP_POS="${KP_POS:-0.40}"
export KP_ROT="${KP_ROT:-0.30}"
export MAX_JOINT_VEL="${MAX_JOINT_VEL:-0.10}"
export MAX_TARGET_SPEED="${MAX_TARGET_SPEED:-0.08}"
export ALPHA_DQ="${ALPHA_DQ:-0.03}"
export SPEEDJ_A="${SPEEDJ_A:-0.04}"
export MAX_POS_ERROR_STOP="${MAX_POS_ERROR_STOP:-0.12}"
export MAX_ROT_ERROR_STOP="${MAX_ROT_ERROR_STOP:-0.50}"
export LOOP_WATCHDOG_WARN_FACTOR="${LOOP_WATCHDOG_WARN_FACTOR:-2.0}"
export LOOP_WATCHDOG_STOP_FACTOR="${LOOP_WATCHDOG_STOP_FACTOR:-5.0}"
export TARGET_SMOOTHER_DT_CAP="${TARGET_SMOOTHER_DT_CAP:-}"
export SMOOTH_ALPHA_POS="${SMOOTH_ALPHA_POS:-0.25}"
export SMOOTH_ALPHA_ROT="${SMOOTH_ALPHA_ROT:-0.08}"
export SMOOTH_ALPHA_GRIPPER="${SMOOTH_ALPHA_GRIPPER:-0.35}"

export GRIPPER_ENABLE="${GRIPPER_ENABLE:-1}"
export GRIPPER_MOTION_ENABLE="${GRIPPER_MOTION_ENABLE:-$ENABLE_MOTION}"
export GRIPPER_IP="${GRIPPER_IP:-192.168.1.1}"
export GRIPPER_PORT="${GRIPPER_PORT:-502}"
export GRIPPER_OPEN_WIDTH_MM="${GRIPPER_OPEN_WIDTH_MM:-85}"
export INITIAL_GRIPPER_WIDTH_MM="${INITIAL_GRIPPER_WIDTH_MM:-$GRIPPER_OPEN_WIDTH_MM}"
export GRIPPER_CLOSE_WIDTH_MM="${GRIPPER_CLOSE_WIDTH_MM:-30}"
export GRIPPER_FORCE_N="${GRIPPER_FORCE_N:-12}"
export GRIPPER_COMMAND_PERIOD="${GRIPPER_COMMAND_PERIOD:-0.10}"
export GRIPPER_DEADBAND_MM="${GRIPPER_DEADBAND_MM:-1.0}"
export GRIPPER_LATCH="${GRIPPER_LATCH:-0}"
export GRIPPER_LATCH_CLOSE_THRESHOLD="${GRIPPER_LATCH_CLOSE_THRESHOLD:-0.30}"
export GRIPPER_LATCH_OPEN_THRESHOLD="${GRIPPER_LATCH_OPEN_THRESHOLD:--0.05}"
export GRIPPER_LATCH_CLOSE_COMMAND="${GRIPPER_LATCH_CLOSE_COMMAND:-1.20}"
export GRIPPER_LATCH_OPEN_COMMAND="${GRIPPER_LATCH_OPEN_COMMAND:--0.20}"
export GRIPPER_QUANTIZE="${GRIPPER_QUANTIZE:-0}"
export GRIPPER_QUANTIZE_VALUES="${GRIPPER_QUANTIZE_VALUES:--0.2 0.30 0.70}"
export GRIPPER_QUANTIZE_THRESHOLDS="${GRIPPER_QUANTIZE_THRESHOLDS:-}"

export MAX_RUN_TIME="${MAX_RUN_TIME:-0}"
export PRINT_PERIOD="${PRINT_PERIOD:-0.5}"
export DEBUG_TIMING="${DEBUG_TIMING:-1}"
export VERBOSE_PLAN="${VERBOSE_PLAN:-0}"
export DEBUG_GRIPPER_PLAN="${DEBUG_GRIPPER_PLAN:-0}"
export SHOW_CAMERAS="${SHOW_CAMERAS:-0}"
export CAMERA_DISPLAY_PERIOD="${CAMERA_DISPLAY_PERIOD:-0.10}"
export CAMERA_DISPLAY_SCALE="${CAMERA_DISPLAY_SCALE:-2}"
export IGNORE_ACTION_ORIENTATION="${IGNORE_ACTION_ORIENTATION:-0}"
export PREFLIGHT_ONLY="${PREFLIGHT_ONLY:-0}"

[[ -n "$CHECKPOINT" ]] || launch_die "CHECKPOINT is required. Checkpoints are not stored in Git; copy one into data/checkpoints/."

case "$BACKEND" in
  fake|speedj) ;;
  *) launch_die "BACKEND must be 'fake' or 'speedj'." ;;
esac
case "$CAMERA_MODE" in
  fake|realsense) ;;
  *) launch_die "CAMERA_MODE must be 'fake' or 'realsense'." ;;
esac
if launch_is_enabled "$ENABLE_MOTION" && [[ "$BACKEND" != "speedj" ]]; then
  launch_die "ENABLE_MOTION=1 requires BACKEND=speedj."
fi
if launch_is_enabled "$GRIPPER_MOTION_ENABLE" && ! launch_is_enabled "$GRIPPER_ENABLE"; then
  launch_die "GRIPPER_MOTION_ENABLE=1 requires GRIPPER_ENABLE=1."
fi

CHECKPOINT="$(launch_resolve_project_path "$CHECKPOINT")"
TOP_CAMERA_CONFIG="$(launch_resolve_project_path "$TOP_CAMERA_CONFIG")"
WRIST_CAMERA_CONFIG="$(launch_resolve_project_path "$WRIST_CAMERA_CONFIG")"
URDF="$(launch_resolve_project_path "$URDF")"
export CHECKPOINT TOP_CAMERA_CONFIG WRIST_CAMERA_CONFIG URDF

read -r -a top_crop <<<"$TOP_CROP"
read -r -a wrist_crop <<<"$WRIST_CROP"
read -r -a tcp_offset <<<"$TCP_OFFSET"
read -r -a gripper_quantize_values <<<"$GRIPPER_QUANTIZE_VALUES"
(( ${#top_crop[@]} == 4 )) || launch_die "TOP_CROP must contain 4 integers."
(( ${#wrist_crop[@]} == 4 )) || launch_die "WRIST_CROP must contain 4 integers."
(( ${#tcp_offset[@]} == 3 )) || launch_die "TCP_OFFSET must contain 3 values."
(( ${#gripper_quantize_values[@]} >= 2 )) || launch_die "GRIPPER_QUANTIZE_VALUES must contain at least two values."

gripper_quantize_thresholds=()
if [[ -n "$GRIPPER_QUANTIZE_THRESHOLDS" ]]; then
  read -r -a gripper_quantize_thresholds <<<"$GRIPPER_QUANTIZE_THRESHOLDS"
  expected_thresholds=$(( ${#gripper_quantize_values[@]} - 1 ))
  (( ${#gripper_quantize_thresholds[@]} == expected_thresholds )) || launch_die "GRIPPER_QUANTIZE_THRESHOLDS must have one fewer value than GRIPPER_QUANTIZE_VALUES."
fi

launch_select_python
launch_require_file "$CHECKPOINT" "policy checkpoint"
launch_require_file "$URDF" "UR10 URDF"
if [[ "$CAMERA_MODE" == "realsense" ]] && ! launch_is_enabled "$NO_ADVANCED_CONFIG"; then
  launch_require_file "$TOP_CAMERA_CONFIG" "top-camera JSON configuration"
  launch_require_file "$WRIST_CAMERA_CONFIG" "wrist-camera JSON configuration"
fi
launch_require_python_modules torch numpy cv2 pinocchio zarr pyrealsense2 pymodbus urx

advanced_status="enabled"
launch_is_enabled "$NO_ADVANCED_CONFIG" && advanced_status="disabled"

cat <<EOF
-------------------------------------------
UR10 REAL DIFFUSION LAUNCHER
-------------------------------------------
checkpoint       : $CHECKPOINT
backend          : $BACKEND
enable motion    : $ENABLE_MOTION
robot ip         : $ROBOT_IP
device           : $DEVICE
camera mode      : $CAMERA_MODE
advanced config  : $advanced_status
top crop         : $TOP_CROP
wrist crop       : $WRIST_CROP
tcp offset       : $TCP_OFFSET
base rz deg      : $BASE_RZ_DEG
policy action hz : $POLICY_HZ
exec horizon     : $EXEC_HORIZON
denoising steps  : $NUM_INFERENCE_STEPS
async inference  : $ASYNC_INFERENCE
async hold       : $ASYNC_HOLD_CURRENT_POSE
kp pos/rot       : $KP_POS / $KP_ROT
max joint vel    : $MAX_JOINT_VEL
max target speed : $MAX_TARGET_SPEED
max pos err stop : $MAX_POS_ERROR_STOP
max rot err stop : $MAX_ROT_ERROR_STOP
gripper          : $GRIPPER_ENABLE motion=$GRIPPER_MOTION_ENABLE
initial grip     : $INITIAL_GRIPPER_WIDTH_MM mm
gripper widths   : $GRIPPER_OPEN_WIDTH_MM / $GRIPPER_CLOSE_WIDTH_MM mm
gripper force    : $GRIPPER_FORCE_N N
gripper latch    : $GRIPPER_LATCH
gripper quantize : $GRIPPER_QUANTIZE values=$GRIPPER_QUANTIZE_VALUES
show cameras     : $SHOW_CAMERAS scale=$CAMERA_DISPLAY_SCALE
max run time     : $MAX_RUN_TIME
-------------------------------------------
EOF

if launch_is_enabled "$PREFLIGHT_ONLY"; then
  launch_info "Preflight passed; no robot, camera, or gripper was opened."
  exit 0
fi

motion_args=()
async_args=()
async_hold_args=()
threads_args=()
target_dt_cap_args=()
gripper_args=()
gripper_motion_args=()
gripper_latch_args=()
gripper_quantize_args=()
debug_timing_args=()
verbose_plan_args=()
debug_gripper_plan_args=()
show_cameras_args=()
ignore_orientation_args=()
advanced_args=()

launch_is_enabled "$ENABLE_MOTION" && motion_args+=(--enable-motion)
launch_is_enabled "$ASYNC_INFERENCE" && async_args+=(--async-inference)
launch_is_enabled "$ASYNC_HOLD_CURRENT_POSE" &&
  async_hold_args+=(--async-hold-current-pose)
[[ -n "$TORCH_NUM_THREADS" ]] &&
  threads_args+=(--torch-num-threads "$TORCH_NUM_THREADS")
[[ -n "$TARGET_SMOOTHER_DT_CAP" ]] &&
  target_dt_cap_args+=(--target-smoother-dt-cap "$TARGET_SMOOTHER_DT_CAP")
launch_is_enabled "$GRIPPER_ENABLE" && gripper_args+=(--gripper-enable)
launch_is_enabled "$GRIPPER_MOTION_ENABLE" &&
  gripper_motion_args+=(--gripper-motion-enable)
if launch_is_enabled "$GRIPPER_LATCH"; then
  gripper_latch_args+=(
    --gripper-latch
    --gripper-latch-close-threshold "$GRIPPER_LATCH_CLOSE_THRESHOLD"
    --gripper-latch-open-threshold "$GRIPPER_LATCH_OPEN_THRESHOLD"
    --gripper-latch-close-command "$GRIPPER_LATCH_CLOSE_COMMAND"
    --gripper-latch-open-command "$GRIPPER_LATCH_OPEN_COMMAND"
  )
fi
if launch_is_enabled "$GRIPPER_QUANTIZE"; then
  gripper_quantize_args+=(
    --gripper-quantize
    --gripper-quantize-values "${gripper_quantize_values[@]}"
  )
  if (( ${#gripper_quantize_thresholds[@]} > 0 )); then
    gripper_quantize_args+=(
      --gripper-quantize-thresholds "${gripper_quantize_thresholds[@]}"
    )
  fi
fi
launch_is_enabled "$DEBUG_TIMING" && debug_timing_args+=(--debug-timing)
launch_is_enabled "$VERBOSE_PLAN" && verbose_plan_args+=(--verbose-plan)
launch_is_enabled "$DEBUG_GRIPPER_PLAN" &&
  debug_gripper_plan_args+=(--debug-gripper-plan)
if launch_is_enabled "$SHOW_CAMERAS"; then
  show_cameras_args+=(
    --show-cameras
    --camera-display-period "$CAMERA_DISPLAY_PERIOD"
    --camera-display-scale "$CAMERA_DISPLAY_SCALE"
  )
fi
launch_is_enabled "$IGNORE_ACTION_ORIENTATION" &&
  ignore_orientation_args+=(--ignore-action-orientation)
launch_is_enabled "$NO_ADVANCED_CONFIG" && advanced_args+=(--no-advanced-config)

cd "$PROJECT_ROOT"
policy_command=(
  "$PYTHON_BIN"
  -m
  ur10_real_robot.policy_exec.run_diffusion_real
  --checkpoint "$CHECKPOINT"
  --backend "$BACKEND"
  --robot-ip "$ROBOT_IP"
  "${motion_args[@]}"
  --device "$DEVICE"
  --camera-mode "$CAMERA_MODE"
  --top-serial "$TOP_SERIAL"
  --wrist-serial "$WRIST_SERIAL"
  --top-camera-config "$TOP_CAMERA_CONFIG"
  --wrist-camera-config "$WRIST_CAMERA_CONFIG"
  "${advanced_args[@]}"
  --top-crop "${top_crop[@]}"
  --wrist-crop "${wrist_crop[@]}"
  --dataset-width "$DATASET_WIDTH"
  --dataset-height "$DATASET_HEIGHT"
  --urdf "$URDF"
  --tcp-offset "${tcp_offset[@]}"
  --base-rz-deg "$BASE_RZ_DEG"
  --control-hz "$CONTROL_HZ"
  --policy-hz "$POLICY_HZ"
  --exec-horizon "$EXEC_HORIZON"
  --num-inference-steps "$NUM_INFERENCE_STEPS"
  "${threads_args[@]}"
  "${async_args[@]}"
  "${async_hold_args[@]}"
  --kp-pos "$KP_POS"
  --kp-rot "$KP_ROT"
  --max-joint-vel "$MAX_JOINT_VEL"
  --max-target-speed "$MAX_TARGET_SPEED"
  --max-pos-error-stop "$MAX_POS_ERROR_STOP"
  --max-rot-error-stop "$MAX_ROT_ERROR_STOP"
  --loop-watchdog-warn-factor "$LOOP_WATCHDOG_WARN_FACTOR"
  --loop-watchdog-stop-factor "$LOOP_WATCHDOG_STOP_FACTOR"
  "${target_dt_cap_args[@]}"
  --alpha-dq "$ALPHA_DQ"
  --speedj-a "$SPEEDJ_A"
  --smooth-alpha-pos "$SMOOTH_ALPHA_POS"
  --smooth-alpha-rot "$SMOOTH_ALPHA_ROT"
  --smooth-alpha-gripper "$SMOOTH_ALPHA_GRIPPER"
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
  "${gripper_latch_args[@]}"
  "${gripper_quantize_args[@]}"
  --max-run-time "$MAX_RUN_TIME"
  --print-period "$PRINT_PERIOD"
  "${debug_timing_args[@]}"
  "${verbose_plan_args[@]}"
  "${debug_gripper_plan_args[@]}"
  "${show_cameras_args[@]}"
  "${ignore_orientation_args[@]}"
)
"${policy_command[@]}"
