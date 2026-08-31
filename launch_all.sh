#!/usr/bin/env bash
set -Eeuo pipefail

# Start MuJoCo teleoperation and the 3D Systems Touch input in one terminal.
# The launcher is location-independent: it derives every path from this file.

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$SCRIPT_DIR}"
export PROJECT_ROOT

show_help() {
  cat <<'EOF'
Usage: ./launch_all.sh

Starts the Touch ROS 2 driver, waits for /touch/pose, then starts MuJoCo
teleoperation. Press Ctrl+C in this terminal to stop both processes.

Optional environment variables:
  CONDA_ENV_NAME=microwave_dp  Conda environment used when none is active
  PYTHON_BIN=/path/to/python   Explicit Python interpreter
  TOUCH_BUILD=auto             auto, 1 (always build), or 0 (never build)
  START_TOUCH_DRIVER=1         Set to 0 when a Touch node already runs
  TOUCH_START_TIMEOUT=15       Startup timeout in seconds
  TOUCH_LOG_FILE=/tmp/file.log Touch driver log file

The Touch must be plugged in, its vendor driver/OpenHaptics must be installed,
and OPENHAPTICS_ROOT must be set for the first ROS 2 workspace build. See
README_ENV.md.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  show_help
  exit 0
fi
(( $# == 0 )) || { show_help >&2; exit 2; }

# shellcheck source=scripts/lib/launch_common.sh
source "$PROJECT_ROOT/scripts/lib/launch_common.sh"

launch_select_python
launch_source_ros2
launch_prepare_touch_workspace
launch_require_file \
  "$PROJECT_ROOT/dp_mujoco/models/universal_robots_ur10e/scene_microwave_camera.xml" \
  "MuJoCo scene"
launch_require_file \
  "$PROJECT_ROOT/dp_mujoco/models/universal_robots_ur10e/ur10_d455_support_rg2ft_fixed_gripper.urdf" \
  "UR10 URDF"
launch_require_python_modules numpy cv2 mujoco rclpy pinocchio diffusion_policy

cleanup() {
  launch_stop_touch_driver
}
trap cleanup EXIT INT TERM

launch_start_touch_driver
launch_info "Starting MuJoCo teleoperation. Press Ctrl+C to stop."
cd "$PROJECT_ROOT"
"$PYTHON_BIN" -m dp_mujoco.teleop.test_UR10e_touch
