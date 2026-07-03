#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/bool.hpp>

namespace eurodao_joystick_teleop {

struct ButtonState {
  bool estop_triggered{false};
  bool gripper_open{false};
  bool gripper_close{false};
  bool speed_down{false};
  bool speed_up{false};
  bool go_home{false};
};

class ButtonHandler {
public:
  ButtonHandler(
    rclcpp::Node * node,
    int estop_button = 6,
    int gripper_open_button = 0,
    int gripper_close_button = 1,
    int speed_down_button = 3,
    int speed_up_button = 2,
    int go_home_button = 7)
  : node_(node),
    estop_button_(estop_button),
    gripper_open_button_(gripper_open_button),
    gripper_close_button_(gripper_close_button),
    speed_down_button_(speed_down_button),
    speed_up_button_(speed_up_button),
    go_home_button_(go_home_button)
  {
    estop_pub_ = node_->create_publisher<std_msgs::msg::Bool>("/e_stop", 10);
  }

  ButtonState update(const std::vector<int32_t> & buttons)
  {
    ButtonState result;

    if (buttons.empty()) {
      prev_buttons_.clear();
      return result;
    }

    // E-Stop is intentionally one-way (latch): once triggered, it cannot be
    // cleared by this node.  An external reset procedure (e.g. operator
    // confirming safe state) must publish false on /e_stop to resume.
    if (is_rising_edge(buttons, estop_button_)) {
      result.estop_triggered = true;
      std_msgs::msg::Bool msg;
      msg.data = true;
      estop_pub_->publish(msg);
      RCLCPP_WARN(node_->get_logger(), "E-Stop triggered!");
    }

    if (is_rising_edge(buttons, gripper_open_button_)) {
      result.gripper_open = true;
    }
    if (is_rising_edge(buttons, gripper_close_button_)) {
      result.gripper_close = true;
    }

    if (speed_down_button_ >= 0 && static_cast<std::size_t>(speed_down_button_) < buttons.size()) {
      result.speed_down = (buttons[static_cast<std::size_t>(speed_down_button_)] == 1);
    }

    if (speed_up_button_ >= 0 && static_cast<std::size_t>(speed_up_button_) < buttons.size()) {
      result.speed_up = (buttons[static_cast<std::size_t>(speed_up_button_)] == 1);
    }

    if (is_rising_edge(buttons, go_home_button_)) {
      result.go_home = true;
      RCLCPP_INFO(node_->get_logger(), "TODO: go home");
    }

    prev_buttons_ = buttons;
    return result;
  }

private:
  bool is_rising_edge(const std::vector<int32_t> & buttons, int index) const
  {
    if (index < 0) {
      return false;
    }
    const std::size_t idx = static_cast<std::size_t>(index);
    if (idx >= buttons.size()) {
      return false;
    }
    const int32_t current = buttons[idx];
    const int32_t prev = (idx < prev_buttons_.size()) ? prev_buttons_[idx] : 0;
    return (current == 1) && (prev == 0);
  }

  rclcpp::Node * node_{nullptr};

  int estop_button_{6};
  int gripper_open_button_{0};
  int gripper_close_button_{1};
  int speed_down_button_{3};
  int speed_up_button_{2};
  int go_home_button_{7};

  std::vector<int32_t> prev_buttons_;
  rclcpp::Publisher<std_msgs::msg::Bool>::SharedPtr estop_pub_;
};

}  // namespace eurodao_joystick_teleop

