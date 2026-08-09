#!/bin/zsh
# Script pour lancer la teleop Touch + backend robot.
#
# Safe par defaut:
#   ./ur10_real_robot/run_teleop.sh
#
# Connexion robot sans mouvement:
#   REAL_BACKEND=speedj ./ur10_real_robot/run_teleop.sh
#
# Vraie teleop robot:
#   REAL_BACKEND=speedj ENABLE_MOTION=1 ./ur10_real_robot/run_teleop.sh
#
# Preset dataset reel pick-and-drop:
#   REAL_DATASET_PRESET=1 ./ur10_real_robot/run_teleop.sh

export REAL_DATASET_PRESET="${REAL_DATASET_PRESET:-0}"

if [[ "$REAL_DATASET_PRESET" == "1" ]]; then
  export REAL_BACKEND="${REAL_BACKEND:-speedj}"
  export ENABLE_MOTION="${ENABLE_MOTION:-1}"
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
  export TARGET_ALPHA_POS="${TARGET_ALPHA_POS:-0.45}"
  export TARGET_ALPHA_ROT="${TARGET_ALPHA_ROT:-0.25}"
  export TOUCH_AXIS_MAP="${TOUCH_AXIS_MAP:-swap_xy_neg_y}"
  export TOUCH_ROT_MAP="${TOUCH_ROT_MAP:-same_as_position}"
  export TOUCH_ROT_APPLY="${TOUCH_ROT_APPLY:-world}"
  export TOUCH_ROT_METHOD="${TOUCH_ROT_METHOD:-matrix}"
  export HOME_RESET_MAX_JOINT_VEL="${HOME_RESET_MAX_JOINT_VEL:-0.08}"
  export GRIPPER_ENABLE="${GRIPPER_ENABLE:-1}"
  export GRIPPER_MOTION_ENABLE="${GRIPPER_MOTION_ENABLE:-1}"
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
  export TOP_CAMERA_CONFIG="${TOP_CAMERA_CONFIG:-/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/camera/config/d435_config_dataset.json}"
  export WRIST_CAMERA_CONFIG="${WRIST_CAMERA_CONFIG:-/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/camera/config/d455_config_dataset.json}"
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
export GRIPPER_MOTION_ENABLE="${GRIPPER_MOTION_ENABLE:-0}"
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
export TOP_CAMERA_CONFIG="${TOP_CAMERA_CONFIG:-/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/camera/config/d435_config_dataset.json}"
export WRIST_CAMERA_CONFIG="${WRIST_CAMERA_CONFIG:-/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/camera/config/d455_config_dataset.json}"
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
export TOUCH_BUILD="${TOUCH_BUILD:-0}"
export TELEOP_START_DELAY="${TELEOP_START_DELAY:-3}"

echo "-------------------------------------------"
echo "UR10 REAL TELEOP LAUNCHER"
echo "-------------------------------------------"
echo "backend          : $REAL_BACKEND"
echo "enable motion    : $ENABLE_MOTION"
echo "robot ip         : $ROBOT_IP"
echo "control hz       : $CONTROL_HZ"
echo "tcp offset       : $TCP_OFFSET"
echo "base rz deg      : $BASE_RZ_DEG"
echo "kp pos           : $KP_POS"
echo "max joint vel    : $MAX_JOINT_VEL"
echo "position scale   : $POSITION_SCALE"
echo "max target speed : $MAX_TARGET_SPEED"
echo "target alpha pos : $TARGET_ALPHA_POS"
echo "target alpha rot : $TARGET_ALPHA_ROT"
echo "touch axis map   : $TOUCH_AXIS_MAP"
echo "touch rot map    : $TOUCH_ROT_MAP"
echo "touch rot apply  : $TOUCH_ROT_APPLY"
echo "touch rot method : $TOUCH_ROT_METHOD"
echo "home reset vel   : $HOME_RESET_MAX_JOINT_VEL"
echo "gripper enable   : $GRIPPER_ENABLE"
echo "gripper motion   : $GRIPPER_MOTION_ENABLE"
echo "gripper mode     : $GRIPPER_CONTROL_MODE"
echo "grip cmd mode    : $GRIPPER_COMMAND_MODE"
echo "grip steps       : $GRIPPER_STEP_VALUES"
echo "gripper ip       : $GRIPPER_IP:$GRIPPER_PORT"
echo "initial grip     : $INITIAL_GRIPPER_WIDTH_MM mm"
echo "record grip q    : $RECORD_GRIPPER_QPOS_SOURCE"
echo "record grip act  : $RECORD_GRIPPER_ACTION_SOURCE"
echo "camera enable    : $CAMERA_ENABLE"
echo "advanced config  : $(( 1 - ${NO_ADVANCED_CONFIG:-0} ))"
echo "top cam config   : $TOP_CAMERA_CONFIG"
echo "wrist cam config : $WRIST_CAMERA_CONFIG"
echo "record enable    : $RECORD_ENABLE"
echo "min ep steps     : $MIN_EPISODE_STEPS"
echo "show cameras     : $SHOW_CAMERAS"
echo "top crop         : ${TOP_CROP:-none}"
echo "wrist crop       : ${WRIST_CROP:-none}"
echo "dataset append   : $DATASET_APPEND_LATEST"
echo "dataset path     : ${DATASET_PATH:-auto}"
echo "touch build      : $TOUCH_BUILD"
echo "teleop delay     : $TELEOP_START_DELAY s"
echo "-------------------------------------------"

# Terminal 1 : teleop Python

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim

echo "[real teleop] waiting ${TELEOP_START_DELAY:-3}s for Touch ROS2 node..."
sleep "${TELEOP_START_DELAY:-3}"

motion_arg=()
if [[ "${ENABLE_MOTION:-0}" == "1" ]]; then
  motion_arg+=(--enable-motion)
fi

gripper_arg=()
if [[ "${GRIPPER_ENABLE:-0}" == "1" ]]; then
  gripper_arg+=(--gripper-enable)
fi

gripper_motion_arg=()
if [[ "${GRIPPER_MOTION_ENABLE:-0}" == "1" ]]; then
  gripper_motion_arg+=(--gripper-motion-enable)
fi

camera_arg=()
if [[ "${CAMERA_ENABLE:-0}" == "1" ]]; then
  camera_arg+=(--camera-enable)
fi

record_arg=()
if [[ "${RECORD_ENABLE:-0}" == "1" ]]; then
  record_arg+=(--record-enable)
fi

show_camera_arg=()
if [[ "${SHOW_CAMERAS:-0}" == "1" ]]; then
  show_camera_arg+=(--show-cameras)
fi

advanced_arg=()
if [[ "${NO_ADVANCED_CONFIG:-0}" == "1" ]]; then
  advanced_arg+=(--no-advanced-config)
fi

dataset_path_arg=()
if [[ -n "${DATASET_PATH:-}" ]]; then
  dataset_path_arg+=(--dataset-path "${DATASET_PATH}")
fi

append_latest_arg=()
if [[ "${DATASET_APPEND_LATEST:-0}" == "1" ]]; then
  append_latest_arg+=(--append-latest-dataset)
fi

top_crop_arg=()
if [[ -n "${TOP_CROP:-}" ]]; then
  top_crop=(${=TOP_CROP})
  top_crop_arg+=(--top-crop "${top_crop[@]}")
fi

wrist_crop_arg=()
if [[ -n "${WRIST_CROP:-}" ]]; then
  wrist_crop=(${=WRIST_CROP})
  wrist_crop_arg+=(--wrist-crop "${wrist_crop[@]}")
fi

tcp_offset=(${=TCP_OFFSET})
gripper_step_values=(${=GRIPPER_STEP_VALUES})

python3 -m ur10_real_robot.run_real_teleop \
  --backend "${REAL_BACKEND:-fake}" \
  ${motion_arg[@]} \
  --robot-ip "${ROBOT_IP:-192.168.2.100}" \
  --control-hz "${CONTROL_HZ:-50}" \
  --tcp-offset "${tcp_offset[@]}" \
  --base-rz-deg "${BASE_RZ_DEG:-180}" \
  --kp-pos "${KP_POS:-0.35}" \
  --kp-rot "${KP_ROT:-0.0}" \
  --max-joint-vel "${MAX_JOINT_VEL:-0.08}" \
  --alpha-dq "${ALPHA_DQ:-0.04}" \
  --speedj-a "${SPEEDJ_A:-0.06}" \
  --position-scale "${POSITION_SCALE:-0.15}" \
  --max-target-speed "${MAX_TARGET_SPEED:-0.05}" \
  --target-alpha-pos "${TARGET_ALPHA_POS:-0.25}" \
  --target-alpha-rot "${TARGET_ALPHA_ROT:-0.15}" \
  --touch-axis-map "${TOUCH_AXIS_MAP:-swap_xy_neg_y}" \
  --touch-rot-map "${TOUCH_ROT_MAP:-same_as_position}" \
  --touch-rot-apply "${TOUCH_ROT_APPLY:-world}" \
  --touch-rot-method "${TOUCH_ROT_METHOD:-matrix}" \
  --watchdog-timeout "${WATCHDOG_TIMEOUT:-0.30}" \
  --home-reset-kp "${HOME_RESET_KP:-1.0}" \
  --home-reset-max-joint-vel "${HOME_RESET_MAX_JOINT_VEL:-0.08}" \
  --home-reset-threshold-deg "${HOME_RESET_THRESHOLD_DEG:-0.5}" \
  ${gripper_arg[@]} \
  ${gripper_motion_arg[@]} \
  --gripper-ip "${GRIPPER_IP:-192.168.1.1}" \
  --gripper-port "${GRIPPER_PORT:-502}" \
  --gripper-open-width-mm "${GRIPPER_OPEN_WIDTH_MM:-85}" \
  --initial-gripper-width-mm "${INITIAL_GRIPPER_WIDTH_MM:-85}" \
  --gripper-close-width-mm "${GRIPPER_CLOSE_WIDTH_MM:-35}" \
  --gripper-force-n "${GRIPPER_FORCE_N:-8}" \
  --gripper-command-period "${GRIPPER_COMMAND_PERIOD:-0.10}" \
  --gripper-deadband-mm "${GRIPPER_DEADBAND_MM:-1.0}" \
  --gripper-control-mode "${GRIPPER_CONTROL_MODE:-button}" \
  --gripper-command-mode "${GRIPPER_COMMAND_MODE:-continuous}" \
  --gripper-step-values "${gripper_step_values[@]}" \
  --record-gripper-qpos-source "${RECORD_GRIPPER_QPOS_SOURCE:-actual_width}" \
  --record-gripper-action-source "${RECORD_GRIPPER_ACTION_SOURCE:-actual_width}" \
  ${camera_arg[@]} \
  ${record_arg[@]} \
  ${show_camera_arg[@]} \
  ${advanced_arg[@]} \
  ${dataset_path_arg[@]} \
  ${append_latest_arg[@]} \
  --camera-mode "${CAMERA_MODE:-realsense}" \
  --top-serial "${TOP_SERIAL:-332322072359}" \
  --wrist-serial "${WRIST_SERIAL:-043422251624}" \
  --top-camera-config "${TOP_CAMERA_CONFIG}" \
  --wrist-camera-config "${WRIST_CAMERA_CONFIG}" \
  --dataset-width "${DATASET_WIDTH:-320}" \
  --dataset-height "${DATASET_HEIGHT:-240}" \
  --dataset-root "${DATASET_ROOT:-data/datasets}" \
  --min-episode-steps "${MIN_EPISODE_STEPS:-3}" \
  ${top_crop_arg[@]} \
  ${wrist_crop_arg[@]} \
  --record-freq "${RECORD_FREQ:-10}"

status=$?
echo ""
echo "[real teleop] process exited with status $status"
echo "Press Enter to close this terminal..."
read
exec zsh -i
') &

# Terminal 2 : ROS2 + Touch driver + RViz

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ros2_WS
if [[ "${TOUCH_BUILD:-0}" == "1" ]]; then
  colcon build
fi
source install/setup.zsh
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
ros2 launch touch_ros2_driver touch_rviz.launch.py
status=$?
echo ""
echo "[touch ros2] process exited with status $status"
echo "Press Enter to close this terminal..."
read
exec zsh -i
') &



wait
