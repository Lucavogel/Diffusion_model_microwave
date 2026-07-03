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
export TOUCH_AXIS_MAP="${TOUCH_AXIS_MAP:-swap_xy_neg_y}"
export TOUCH_ROT_MAP="${TOUCH_ROT_MAP:-same_as_position}"
export TOUCH_ROT_APPLY="${TOUCH_ROT_APPLY:-world}"
export TOUCH_ROT_METHOD="${TOUCH_ROT_METHOD:-matrix}"
export WATCHDOG_TIMEOUT="${WATCHDOG_TIMEOUT:-0.30}"
export GRIPPER_ENABLE="${GRIPPER_ENABLE:-0}"
export GRIPPER_MOTION_ENABLE="${GRIPPER_MOTION_ENABLE:-0}"
export GRIPPER_IP="${GRIPPER_IP:-192.168.1.1}"
export GRIPPER_PORT="${GRIPPER_PORT:-502}"
export GRIPPER_OPEN_WIDTH_MM="${GRIPPER_OPEN_WIDTH_MM:-85}"
export GRIPPER_CLOSE_WIDTH_MM="${GRIPPER_CLOSE_WIDTH_MM:-35}"
export GRIPPER_FORCE_N="${GRIPPER_FORCE_N:-8}"
export GRIPPER_COMMAND_PERIOD="${GRIPPER_COMMAND_PERIOD:-0.10}"
export GRIPPER_DEADBAND_MM="${GRIPPER_DEADBAND_MM:-1.0}"
export GRIPPER_CONTROL_MODE="${GRIPPER_CONTROL_MODE:-button}"

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
echo "touch axis map   : $TOUCH_AXIS_MAP"
echo "touch rot map    : $TOUCH_ROT_MAP"
echo "touch rot apply  : $TOUCH_ROT_APPLY"
echo "touch rot method : $TOUCH_ROT_METHOD"
echo "gripper enable   : $GRIPPER_ENABLE"
echo "gripper motion   : $GRIPPER_MOTION_ENABLE"
echo "gripper mode     : $GRIPPER_CONTROL_MODE"
echo "gripper ip       : $GRIPPER_IP:$GRIPPER_PORT"
echo "-------------------------------------------"

# Terminal 1 : teleop Python

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim

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

tcp_offset=(${=TCP_OFFSET})

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
  --touch-axis-map "${TOUCH_AXIS_MAP:-swap_xy_neg_y}" \
  --touch-rot-map "${TOUCH_ROT_MAP:-same_as_position}" \
  --touch-rot-apply "${TOUCH_ROT_APPLY:-world}" \
  --touch-rot-method "${TOUCH_ROT_METHOD:-matrix}" \
  --watchdog-timeout "${WATCHDOG_TIMEOUT:-0.30}" \
  ${gripper_arg[@]} \
  ${gripper_motion_arg[@]} \
  --gripper-ip "${GRIPPER_IP:-192.168.1.1}" \
  --gripper-port "${GRIPPER_PORT:-502}" \
  --gripper-open-width-mm "${GRIPPER_OPEN_WIDTH_MM:-85}" \
  --gripper-close-width-mm "${GRIPPER_CLOSE_WIDTH_MM:-35}" \
  --gripper-force-n "${GRIPPER_FORCE_N:-8}" \
  --gripper-command-period "${GRIPPER_COMMAND_PERIOD:-0.10}" \
  --gripper-deadband-mm "${GRIPPER_DEADBAND_MM:-1.0}" \
  --gripper-control-mode "${GRIPPER_CONTROL_MODE:-button}"

status=$?
echo ""
echo "[real teleop] process exited with status $status"
echo "Press Enter to close this terminal..."
read
') &

# Terminal 2 : ROS2 + Touch driver + RViz

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ros2_WS
colcon build 
source install/setup.zsh
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
ros2 launch touch_ros2_driver touch_rviz.launch.py
status=$?
echo ""
echo "[touch ros2] process exited with status $status"
echo "Press Enter to close this terminal..."
read
') &



wait
