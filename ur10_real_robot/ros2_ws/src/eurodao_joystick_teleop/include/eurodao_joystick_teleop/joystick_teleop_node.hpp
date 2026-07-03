#pragma once

#include <atomic>
#include <chrono>
#include <cstdint>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <geometry_msgs/msg/twist.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_srvs/srv/trigger.hpp>

#include "eurodao_joystick_teleop/axis_mapper.hpp"
#include "eurodao_joystick_teleop/button_handler.hpp"
#include "eurodao_joystick_teleop/gripper_controller.hpp"
#include "eurodao_joystick_teleop/input_processor.hpp"
#include "eurodao_joystick_teleop/safety_guard.hpp"

namespace eurodao_joystick_teleop {

class JoystickTeleopNode : public rclcpp::Node {
public:
  JoystickTeleopNode();

private:
  struct ProcessorSet {
    InputProcessor lx;
    InputProcessor ly;
    InputProcessor lz;
    InputProcessor ax;
    InputProcessor ay;
    InputProcessor az;

    void reset();
  };

  void declare_parameters_();
  AxisMapper build_axis_mapper_();
  int detect_dpad_horizontal_(const std::vector<float> & axes) const;

  void on_timer_();
  TwistComponents process_components_(const TwistComponents & raw);
  void maybe_publish_status_(bool safe, const std::string & reason);

  double publish_rate_hz_{50.0};
  std::string frame_id_{"base_link"};
  int dpad_horizontal_axis_{6};
  double dpad_left_value_{1.0};
  double dpad_right_value_{-1.0};
  double dpad_activation_threshold_{0.5};
  int last_safe_dpad_horizontal_{0};

  std::mutex joy_mutex_;
  std::optional<std::vector<int32_t>> last_buttons_;
  std::optional<std::vector<float>> last_axes_;

  AxisMapper axis_mapper_{std::vector<AxisMapping>{}};
  ProcessorSet processors_;
  SafetyGuard safety_guard_{SafetyGuard::Config{}};
  std::unique_ptr<ButtonHandler> button_handler_;
  std::unique_ptr<GripperController> gripper_controller_;

  std::string safety_reason_{"startup_delay"};
  std::optional<std::chrono::steady_clock::time_point> next_status_time_;

  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr twist_stamped_pub_;
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr twist_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_pub_;
  rclcpp::Service<std_srvs::srv::Trigger>::SharedPtr status_srv_;
  rclcpp::TimerBase::SharedPtr timer_;
};

}  // namespace eurodao_joystick_teleop
