#!/bin/zsh
# Preset launcher for real UR10 diffusion execution.
#
# Dry run with real cameras + robot connection but no motion:
#   CHECKPOINT=data/checkpoints/real_model_pick_orientation.ckpt ./ur10_real_robot/run_diffusion_real.sh
#
# Real execution:
#   CHECKPOINT=data/checkpoints/real_model_pick_orientation.ckpt ENABLE_MOTION=1 ./ur10_real_robot/run_diffusion_real.sh

export CHECKPOINT="${CHECKPOINT:-data/checkpoints/real_model_pick_orientation.ckpt}"
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
export GRIPPER_MOTION_ENABLE="${GRIPPER_MOTION_ENABLE:-1}"
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

echo "-------------------------------------------"
echo "UR10 REAL DIFFUSION LAUNCHER"
echo "-------------------------------------------"
echo "checkpoint       : $CHECKPOINT"
echo "backend          : $BACKEND"
echo "enable motion    : $ENABLE_MOTION"
echo "robot ip         : $ROBOT_IP"
echo "device           : $DEVICE"
echo "camera mode      : $CAMERA_MODE"
echo "top serial       : $TOP_SERIAL"
echo "wrist serial     : $WRIST_SERIAL"
echo "advanced config  : $(( 1 - ${NO_ADVANCED_CONFIG:-0} ))"
echo "top crop         : $TOP_CROP"
echo "wrist crop       : $WRIST_CROP"
echo "tcp offset       : $TCP_OFFSET"
echo "base rz deg      : $BASE_RZ_DEG"
echo "policy hz        : $POLICY_HZ"
echo "exec horizon     : $EXEC_HORIZON"
echo "infer steps      : $NUM_INFERENCE_STEPS"
echo "async hold       : $ASYNC_HOLD_CURRENT_POSE"
echo "kp pos/rot       : $KP_POS / $KP_ROT"
echo "max joint vel    : $MAX_JOINT_VEL"
echo "max target speed : $MAX_TARGET_SPEED"
echo "max pos err stop : $MAX_POS_ERROR_STOP"
echo "max rot err stop : $MAX_ROT_ERROR_STOP"
echo "loop watchdog    : warn=$LOOP_WATCHDOG_WARN_FACTOR stop=$LOOP_WATCHDOG_STOP_FACTOR"
echo "target dt cap    : ${TARGET_SMOOTHER_DT_CAP:-control_dt}"
echo "gripper          : $GRIPPER_ENABLE motion=$GRIPPER_MOTION_ENABLE"
echo "initial grip     : $INITIAL_GRIPPER_WIDTH_MM mm"
echo "gripper widths   : $GRIPPER_OPEN_WIDTH_MM / $GRIPPER_CLOSE_WIDTH_MM mm"
echo "gripper force    : $GRIPPER_FORCE_N N"
echo "gripper latch    : $GRIPPER_LATCH close>$GRIPPER_LATCH_CLOSE_THRESHOLD open<$GRIPPER_LATCH_OPEN_THRESHOLD"
echo "gripper quantize : $GRIPPER_QUANTIZE values=$GRIPPER_QUANTIZE_VALUES thresholds=${GRIPPER_QUANTIZE_THRESHOLDS:-nearest}"
echo "show cameras     : $SHOW_CAMERAS scale=$CAMERA_DISPLAY_SCALE"
echo "max run time     : $MAX_RUN_TIME"
echo "-------------------------------------------"

motion_arg=()
if [[ "$ENABLE_MOTION" == "1" ]]; then
  motion_arg+=(--enable-motion)
fi

async_arg=()
if [[ "$ASYNC_INFERENCE" == "1" ]]; then
  async_arg+=(--async-inference)
fi

async_hold_arg=()
if [[ "$ASYNC_HOLD_CURRENT_POSE" == "1" ]]; then
  async_hold_arg+=(--async-hold-current-pose)
fi

threads_arg=()
if [[ -n "$TORCH_NUM_THREADS" ]]; then
  threads_arg+=(--torch-num-threads "$TORCH_NUM_THREADS")
fi

target_dt_cap_arg=()
if [[ -n "$TARGET_SMOOTHER_DT_CAP" ]]; then
  target_dt_cap_arg+=(--target-smoother-dt-cap "$TARGET_SMOOTHER_DT_CAP")
fi

gripper_arg=()
if [[ "$GRIPPER_ENABLE" == "1" ]]; then
  gripper_arg+=(--gripper-enable)
fi

gripper_motion_arg=()
if [[ "$GRIPPER_MOTION_ENABLE" == "1" ]]; then
  gripper_motion_arg+=(--gripper-motion-enable)
fi

gripper_latch_arg=()
if [[ "$GRIPPER_LATCH" == "1" ]]; then
  gripper_latch_arg+=(
    --gripper-latch
    --gripper-latch-close-threshold "$GRIPPER_LATCH_CLOSE_THRESHOLD"
    --gripper-latch-open-threshold "$GRIPPER_LATCH_OPEN_THRESHOLD"
    --gripper-latch-close-command "$GRIPPER_LATCH_CLOSE_COMMAND"
    --gripper-latch-open-command "$GRIPPER_LATCH_OPEN_COMMAND"
  )
fi

gripper_quantize_arg=()
if [[ "$GRIPPER_QUANTIZE" == "1" ]]; then
  gripper_quantize_values=(${=GRIPPER_QUANTIZE_VALUES})
  gripper_quantize_arg+=(
    --gripper-quantize
    --gripper-quantize-values "${gripper_quantize_values[@]}"
  )
  if [[ -n "$GRIPPER_QUANTIZE_THRESHOLDS" ]]; then
    gripper_quantize_thresholds=(${=GRIPPER_QUANTIZE_THRESHOLDS})
    gripper_quantize_arg+=(
      --gripper-quantize-thresholds "${gripper_quantize_thresholds[@]}"
    )
  fi
fi

debug_timing_arg=()
if [[ "$DEBUG_TIMING" == "1" ]]; then
  debug_timing_arg+=(--debug-timing)
fi

verbose_plan_arg=()
if [[ "$VERBOSE_PLAN" == "1" ]]; then
  verbose_plan_arg+=(--verbose-plan)
fi

debug_gripper_plan_arg=()
if [[ "$DEBUG_GRIPPER_PLAN" == "1" ]]; then
  debug_gripper_plan_arg+=(--debug-gripper-plan)
fi

show_cameras_arg=()
if [[ "$SHOW_CAMERAS" == "1" ]]; then
  show_cameras_arg+=(
    --show-cameras
    --camera-display-period "$CAMERA_DISPLAY_PERIOD"
    --camera-display-scale "$CAMERA_DISPLAY_SCALE"
  )
fi

ignore_orientation_arg=()
if [[ "$IGNORE_ACTION_ORIENTATION" == "1" ]]; then
  ignore_orientation_arg+=(--ignore-action-orientation)
fi

advanced_arg=()
if [[ "$NO_ADVANCED_CONFIG" == "1" ]]; then
  advanced_arg+=(--no-advanced-config)
fi

top_crop=(${=TOP_CROP})
wrist_crop=(${=WRIST_CROP})
tcp_offset=(${=TCP_OFFSET})

/home/luca/venvs/mujoco_ros/bin/python \
  -m ur10_real_robot.policy_exec.run_diffusion_real \
  --checkpoint "$CHECKPOINT" \
  --backend "$BACKEND" \
  --robot-ip "$ROBOT_IP" \
  ${motion_arg[@]} \
  --device "$DEVICE" \
  --camera-mode "$CAMERA_MODE" \
  --top-serial "$TOP_SERIAL" \
  --wrist-serial "$WRIST_SERIAL" \
  --top-camera-config "$TOP_CAMERA_CONFIG" \
  --wrist-camera-config "$WRIST_CAMERA_CONFIG" \
  ${advanced_arg[@]} \
  --top-crop "${top_crop[@]}" \
  --wrist-crop "${wrist_crop[@]}" \
  --dataset-width "$DATASET_WIDTH" \
  --dataset-height "$DATASET_HEIGHT" \
  --tcp-offset "${tcp_offset[@]}" \
  --base-rz-deg "$BASE_RZ_DEG" \
  --control-hz "$CONTROL_HZ" \
  --policy-hz "$POLICY_HZ" \
  --exec-horizon "$EXEC_HORIZON" \
  --num-inference-steps "$NUM_INFERENCE_STEPS" \
  ${threads_arg[@]} \
  ${async_arg[@]} \
  ${async_hold_arg[@]} \
  --kp-pos "$KP_POS" \
  --kp-rot "$KP_ROT" \
  --max-joint-vel "$MAX_JOINT_VEL" \
  --max-target-speed "$MAX_TARGET_SPEED" \
  --max-pos-error-stop "$MAX_POS_ERROR_STOP" \
  --max-rot-error-stop "$MAX_ROT_ERROR_STOP" \
  --loop-watchdog-warn-factor "$LOOP_WATCHDOG_WARN_FACTOR" \
  --loop-watchdog-stop-factor "$LOOP_WATCHDOG_STOP_FACTOR" \
  ${target_dt_cap_arg[@]} \
  --alpha-dq "$ALPHA_DQ" \
  --speedj-a "$SPEEDJ_A" \
  --smooth-alpha-pos "$SMOOTH_ALPHA_POS" \
  --smooth-alpha-rot "$SMOOTH_ALPHA_ROT" \
  --smooth-alpha-gripper "$SMOOTH_ALPHA_GRIPPER" \
  ${gripper_arg[@]} \
  ${gripper_motion_arg[@]} \
  --gripper-ip "$GRIPPER_IP" \
  --gripper-port "$GRIPPER_PORT" \
  --gripper-open-width-mm "$GRIPPER_OPEN_WIDTH_MM" \
  --initial-gripper-width-mm "$INITIAL_GRIPPER_WIDTH_MM" \
  --gripper-close-width-mm "$GRIPPER_CLOSE_WIDTH_MM" \
  --gripper-force-n "$GRIPPER_FORCE_N" \
  --gripper-command-period "$GRIPPER_COMMAND_PERIOD" \
  --gripper-deadband-mm "$GRIPPER_DEADBAND_MM" \
  ${gripper_latch_arg[@]} \
  ${gripper_quantize_arg[@]} \
  --max-run-time "$MAX_RUN_TIME" \
  --print-period "$PRINT_PERIOD" \
  ${debug_timing_arg[@]} \
  ${verbose_plan_arg[@]} \
  ${debug_gripper_plan_arg[@]} \
  ${show_cameras_arg[@]} \
  ${ignore_orientation_arg[@]}
