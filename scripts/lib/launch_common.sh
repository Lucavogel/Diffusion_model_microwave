#!/usr/bin/env bash
# This file is sourced by the project launchers; it is not meant to be executed.
# Shared launcher helpers keep environment and Touch setup consistent and
# prevent the simulation and real-robot entry points from drifting apart.

launch_info() {
  printf '[INFO] %s\n' "$*"
}

launch_warn() {
  printf '[WARN] %s\n' "$*" >&2
}

launch_die() {
  printf '[ERROR] %s\n' "$*" >&2
  exit 1
}

launch_is_enabled() {
  case "${1:-0}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

launch_resolve_project_path() {
  local path="${1:?path is required}"
  if [[ "$path" = /* ]]; then
    printf '%s\n' "$path"
  else
    printf '%s/%s\n' "$PROJECT_ROOT" "$path"
  fi
}

launch_require_file() {
  local path="${1:?path is required}"
  local label="${2:-required file}"
  [[ -f "$path" ]] || launch_die "$label not found: $path"
}

launch_select_python() {
  local candidate="${PYTHON_BIN:-}"
  local conda_setup=""
  local env_name="${CONDA_ENV_NAME:-microwave_dp}"

  if [[ -z "$candidate" && ( -n "${CONDA_PREFIX:-}" || -n "${VIRTUAL_ENV:-}" ) ]]; then
    candidate="$(command -v python || true)"
  fi

  if [[ -z "$candidate" ]]; then
    if ! command -v conda >/dev/null 2>&1; then
      for conda_setup in \
        "$HOME/miniforge3/etc/profile.d/conda.sh" \
        "$HOME/mambaforge/etc/profile.d/conda.sh" \
        "$HOME/miniconda3/etc/profile.d/conda.sh" \
        "$HOME/anaconda3/etc/profile.d/conda.sh"; do
        if [[ -f "$conda_setup" ]]; then
          # shellcheck disable=SC1090
          source "$conda_setup"
          break
        fi
      done
    fi

    command -v conda >/dev/null 2>&1 || launch_die \
      "No Python environment is active and Conda was not found. Follow README_ENV.md."
    conda activate "$env_name" >/dev/null 2>&1 || launch_die \
      "Conda environment '$env_name' was not found. Follow README_ENV.md."
    candidate="$(command -v python || true)"
    launch_info "Activated Conda environment: $env_name"
  fi

  if [[ "$candidate" != */* ]]; then
    candidate="$(command -v "$candidate" || true)"
  fi
  [[ -n "$candidate" && -x "$candidate" ]] || launch_die \
    "No usable Python interpreter was found."

  PYTHON_BIN="$candidate"
  export PYTHON_BIN
  export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
  launch_info "Python: $PYTHON_BIN"
}

launch_require_python_modules() {
  local module output
  for module in "$@"; do
    if ! output=$("$PYTHON_BIN" -c \
      "import importlib; importlib.import_module('${module}')" 2>&1); then
      launch_die "Python module '$module' cannot be imported. ${output//$'\n'/ }"
    fi
  done
}

launch_source_ros2() {
  local distro="${ROS_DISTRO:-humble}"
  local setup="${ROS_SETUP:-/opt/ros/$distro/setup.bash}"
  [[ -f "$setup" ]] || launch_die \
    "ROS 2 setup was not found at $setup. Follow README_ENV.md."
  # shellcheck disable=SC1090
  source "$setup"
  command -v ros2 >/dev/null 2>&1 || launch_die \
    "ROS 2 did not become available after sourcing $setup."
}

launch_add_openhaptics_runtime() {
  local sdk_root="${OPENHAPTICS_ROOT:-}"
  local sdk_lib=""
  [[ -n "$sdk_root" ]] || return 0

  if [[ -d "$sdk_root/usr/lib" ]]; then
    sdk_lib="$sdk_root/usr/lib"
  elif [[ -d "$sdk_root/lib" ]]; then
    sdk_lib="$sdk_root/lib"
  fi
  if [[ -n "$sdk_lib" ]]; then
    export LD_LIBRARY_PATH="$sdk_lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  fi
}

launch_prepare_touch_workspace() {
  local workspace="${TOUCH_WS:-$PROJECT_ROOT/ros2_WS}"
  local setup="$workspace/install/setup.bash"
  local build_mode="${TOUCH_BUILD:-auto}"
  local must_build=0

  [[ -d "$workspace/src/touch_ros2_driver" ]] || launch_die \
    "Touch ROS 2 package not found under $workspace/src."

  case "$build_mode" in
    1|true|TRUE|yes|YES|on|ON) must_build=1 ;;
    auto|AUTO) [[ -f "$setup" ]] || must_build=1 ;;
    0|false|FALSE|no|NO|off|OFF) ;;
    *) launch_die "TOUCH_BUILD must be 0, 1, or auto (got '$build_mode')." ;;
  esac

  if (( must_build )); then
    command -v colcon >/dev/null 2>&1 || launch_die \
      "colcon is required to build the Touch workspace. Follow README_ENV.md."
    [[ -n "${OPENHAPTICS_ROOT:-}" ]] || launch_die \
      "OPENHAPTICS_ROOT must be set before the first Touch build. Follow README_ENV.md."
    launch_require_file \
      "$OPENHAPTICS_ROOT/usr/include/HD/hd.h" \
      "OpenHaptics header"
    launch_info "Building the Touch ROS 2 workspace..."
    (
      cd "$workspace"
      colcon build --symlink-install \
        --cmake-args "-DOPENHAPTICS_ROOT=$OPENHAPTICS_ROOT"
    )
  fi

  [[ -f "$setup" ]] || launch_die \
    "Touch workspace is not built. Set TOUCH_BUILD=auto or follow README_ENV.md."
  # shellcheck disable=SC1090
  source "$setup"
  launch_add_openhaptics_runtime
  ros2 pkg prefix touch_ros2_driver >/dev/null 2>&1 || launch_die \
    "ROS 2 cannot find touch_ros2_driver after sourcing $setup."
}

launch_touch_topic_ready() {
  ros2 topic list 2>/dev/null | grep -Fxq '/touch/pose' || return 1
  # A listed topic is insufficient: wait for one sample to prove that the
  # plugged-in device and OpenHaptics scheduler are actually producing data.
  timeout 2 ros2 topic echo --once --qos-reliability best_effort \
    /touch/pose >/dev/null 2>&1
}

launch_start_touch_driver() {
  local timeout_s="${TOUCH_START_TIMEOUT:-15}"
  local deadline
  local log_file="${TOUCH_LOG_FILE:-/tmp/diffusion_policy_touch_driver.log}"

  TOUCH_DRIVER_PID=""
  export TOUCH_DRIVER_PID

  if launch_touch_topic_ready; then
    launch_info "Using the existing /touch/pose publisher."
    return 0
  fi

  if ! launch_is_enabled "${START_TOUCH_DRIVER:-1}"; then
    launch_die \
      "START_TOUCH_DRIVER=0 but /touch/pose is unavailable. Start the Touch node first."
  fi

  launch_info "Starting the Touch driver (log: $log_file)..."
  mkdir -p "$(dirname -- "$log_file")"
  ros2 launch touch_ros2_driver touch_rviz.launch.py >"$log_file" 2>&1 &
  TOUCH_DRIVER_PID=$!
  deadline=$(( SECONDS + timeout_s ))

  while (( SECONDS < deadline )); do
    if launch_touch_topic_ready; then
      launch_info "Touch input is ready on /touch/pose."
      return 0
    fi
    if ! kill -0 "$TOUCH_DRIVER_PID" 2>/dev/null; then
      wait "$TOUCH_DRIVER_PID" 2>/dev/null || true
      tail -n 30 "$log_file" >&2 || true
      launch_die \
        "The Touch driver stopped during startup. Check that the device is plugged in and its vendor driver is installed."
    fi
    sleep 0.25
  done

  launch_stop_touch_driver
  tail -n 30 "$log_file" >&2 || true
  launch_die \
    "No /touch/pose topic after ${timeout_s}s. Check the Touch connection and $log_file."
}

launch_stop_touch_driver() {
  if [[ -n "${TOUCH_DRIVER_PID:-}" ]] && kill -0 "$TOUCH_DRIVER_PID" 2>/dev/null; then
    kill -INT "$TOUCH_DRIVER_PID" 2>/dev/null || true
    wait "$TOUCH_DRIVER_PID" 2>/dev/null || true
  fi
  TOUCH_DRIVER_PID=""
}
