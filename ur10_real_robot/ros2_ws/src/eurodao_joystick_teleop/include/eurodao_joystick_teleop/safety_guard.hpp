#pragma once

#include <chrono>
#include <cstddef>
#include <cstdint>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

namespace eurodao_joystick_teleop {

class SafetyGuard {
public:
  struct Config {
    bool deadman_enabled{true};
    int deadman_button{4};
    double joy_timeout_sec{0.2};
    double startup_delay_sec{1.0};
  };

  explicit SafetyGuard(Config config) : config_(config) {}

  void reconfigure(Config config)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    config_ = config;
  }

  void mark_started(std::chrono::steady_clock::time_point now)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    start_time_ = now;
  }

  void update_joy_time(std::chrono::steady_clock::time_point now)
  {
    std::lock_guard<std::mutex> lock(mutex_);
    last_joy_time_ = now;
  }

  std::pair<bool, std::string> is_safe(
    const std::vector<int32_t> & buttons,
    std::chrono::steady_clock::time_point now) const
  {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!start_time_) {
      return {false, "startup_delay"};
    }

    const double since_start =
      std::chrono::duration_cast<std::chrono::duration<double>>(now - *start_time_).count();
    if (since_start < config_.startup_delay_sec) {
      return {false, "startup_delay"};
    }

    if (!last_joy_time_) {
      return {false, "joy_timeout"};
    }
    const double since_joy =
      std::chrono::duration_cast<std::chrono::duration<double>>(now - *last_joy_time_).count();
    if (since_joy > config_.joy_timeout_sec) {
      return {false, "joy_timeout"};
    }

    if (config_.deadman_enabled) {
      if (config_.deadman_button < 0) {
        return {false, "deadman_released"};
      }
      const std::size_t idx = static_cast<std::size_t>(config_.deadman_button);
      if (idx >= buttons.size() || buttons[idx] == 0) {
        return {false, "deadman_released"};
      }
    }

    return {true, "ok"};
  }

private:
  Config config_;
  mutable std::mutex mutex_;
  std::optional<std::chrono::steady_clock::time_point> start_time_;
  std::optional<std::chrono::steady_clock::time_point> last_joy_time_;
};

}  // namespace eurodao_joystick_teleop
