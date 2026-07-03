#pragma once

#include <algorithm>
#include <chrono>
#include <cmath>
#include <string>

#include <onrobot_rg_msgs/msg/on_robot_rg_input.hpp>
#include <onrobot_rg_msgs/msg/on_robot_rg_output.hpp>
#include <rclcpp/rclcpp.hpp>
#include <trajectory_msgs/msg/joint_trajectory.hpp>
#include <trajectory_msgs/msg/joint_trajectory_point.hpp>

namespace eurodao_joystick_teleop {

class GripperController {
public:
  GripperController(
    rclcpp::Node * node,
    std::string joint_name,
    double limit_open,
    double limit_close,
    double trajectory_duration,
    std::string direct_command_topic,
    std::string direct_status_topic,
    double direct_open_width_mm,
    double direct_close_width_mm,
    double direct_open_force_n,
    double direct_close_force_n,
    double direct_step_mm,
    double direct_repeat_period_sec)
  : node_(node),
    joint_name_(std::move(joint_name)),
    limit_open_(limit_open),
    limit_close_(limit_close),
    trajectory_duration_(trajectory_duration),
    current_position_(limit_open_),
    direct_command_topic_(std::move(direct_command_topic)),
    direct_status_topic_(std::move(direct_status_topic)),
    direct_open_width_mm_(direct_open_width_mm),
    direct_close_width_mm_(direct_close_width_mm),
    direct_open_force_n_(direct_open_force_n),
    direct_close_force_n_(direct_close_force_n),
    current_direct_width_mm_(direct_open_width_mm_),
    direct_step_mm_(std::max(0.1, direct_step_mm)),
    direct_repeat_period_(
      std::chrono::duration_cast<std::chrono::steady_clock::duration>(
        std::chrono::duration<double>(std::max(0.02, direct_repeat_period_sec))))
  {
    pub_ = node_->create_publisher<trajectory_msgs::msg::JointTrajectory>(
      "/gripper_controller/joint_trajectory",
      10);
    direct_pub_ = node_->create_publisher<onrobot_rg_msgs::msg::OnRobotRGOutput>(
      direct_command_topic_,
      10);
    direct_status_sub_ = node_->create_subscription<onrobot_rg_msgs::msg::OnRobotRGInput>(
      direct_status_topic_,
      10,
      [this](const onrobot_rg_msgs::msg::OnRobotRGInput::SharedPtr msg) {
        latest_direct_width_mm_ = clamp_width_mm(static_cast<double>(msg->grip_width) / 10.0);
        current_direct_width_mm_ = latest_direct_width_mm_;
        direct_busy_ = (msg->busy != 0);
        has_direct_status_ = true;
      });
  }

  void update(bool gripper_open, bool gripper_close)
  {
    if (!gripper_open && !gripper_close) {
      return;
    }

    if (gripper_open) {
      current_position_ = limit_open_;
    } else if (gripper_close) {
      current_position_ = limit_close_;
    }

    trajectory_msgs::msg::JointTrajectory msg;
    msg.joint_names = {joint_name_};

    trajectory_msgs::msg::JointTrajectoryPoint point;
    point.positions = {current_position_};
    const auto duration_ns = static_cast<int64_t>(trajectory_duration_ * 1e9);
    point.time_from_start.sec = static_cast<int32_t>(duration_ns / 1000000000LL);
    point.time_from_start.nanosec = static_cast<uint32_t>(duration_ns % 1000000000LL);
    msg.points = {point};

    pub_->publish(msg);
    RCLCPP_INFO(
      node_->get_logger(), "Gripper %s → position=%.3f (duration=%.1fs)",
      gripper_open ? "OPEN" : "CLOSE", current_position_, trajectory_duration_);
  }

  void update_direct(bool dpad_open, bool dpad_close)
  {
    const int direction = dpad_open == dpad_close ? 0 : (dpad_open ? 1 : -1);
    const auto now = std::chrono::steady_clock::now();

    if (direction == 0) {
      if (last_direct_direction_ != 0) {
        publish_direct_stop_command();
        active_direct_direction_ = 0;
        next_direct_command_time_ = now + direct_repeat_period_;
      }
      last_direct_direction_ = 0;
      return;
    }

    if (direction != last_direct_direction_ && last_direct_direction_ != 0) {
      publish_direct_stop_command();
      active_direct_direction_ = 0;
      last_direct_direction_ = direction;
      next_direct_command_time_ = now + direct_repeat_period_;
      return;
    }

    last_direct_direction_ = direction;

    if (direction == active_direct_direction_) {
      return;
    }

    if (has_direct_status_ && direct_busy_) {
      return;
    }

    if (now < next_direct_command_time_) {
      return;
    }

    const bool open_command = direction > 0;
    current_direct_width_mm_ = open_command ? direct_open_width_mm_ : direct_close_width_mm_;
    const double force_n = open_command ? direct_open_force_n_ : direct_close_force_n_;
    publish_direct_command(current_direct_width_mm_, force_n, 1);
    active_direct_direction_ = direction;
    next_direct_command_time_ = now + direct_repeat_period_;

    RCLCPP_INFO(
      node_->get_logger(), "Direct gripper %s via %s: target=%.1f mm force=%.1f N",
      open_command ? "OPEN" : "CLOSE",
      direct_command_topic_.c_str(),
      clamp_width_mm(current_direct_width_mm_),
      clamp_force_n(force_n));
  }

  double position() const { return has_direct_status_ ? latest_direct_width_mm_ : current_direct_width_mm_; }

private:
  static double clamp_width_mm(double width_mm)
  {
    return std::clamp(width_mm, 0.0, 110.0);
  }

  static double clamp_force_n(double force_n)
  {
    return std::clamp(force_n, 0.0, 40.0);
  }

  double current_width_mm() const
  {
    return has_direct_status_ ? latest_direct_width_mm_ : current_direct_width_mm_;
  }

  void publish_direct_command(double width_mm, double force_n, uint8_t control)
  {
    onrobot_rg_msgs::msg::OnRobotRGOutput msg;
    msg.r_gwd = static_cast<uint16_t>(std::lround(clamp_width_mm(width_mm) * 10.0));
    msg.r_gfr = static_cast<uint16_t>(std::lround(clamp_force_n(force_n) * 10.0));
    msg.r_ctr = control;
    msg.out_zero = 0;
    msg.out_prox_off_r = 0;
    msg.out_prox_off_l = 0;
    direct_pub_->publish(msg);
  }

  void publish_direct_stop_command()
  {
    publish_direct_command(current_width_mm(), 0.0, 0);
    RCLCPP_INFO(
      node_->get_logger(), "Direct gripper STOP via %s at %.1f mm",
      direct_command_topic_.c_str(),
      clamp_width_mm(current_width_mm()));
  }

  rclcpp::Node * node_{nullptr};
  std::string joint_name_;
  double limit_open_{0.105};
  double limit_close_{0.055};
  double trajectory_duration_{0.5};
  double current_position_{0.105};
  std::string direct_command_topic_{"OnRobotRGOutput"};
  std::string direct_status_topic_{"OnRobotRGInput"};
  double direct_open_width_mm_{100.0};
  double direct_close_width_mm_{0.0};
  double direct_open_force_n_{10.0};
  double direct_close_force_n_{40.0};
  double latest_direct_width_mm_{100.0};
  double current_direct_width_mm_{100.0};
  double direct_step_mm_{1.0};
  std::chrono::steady_clock::duration direct_repeat_period_{
    std::chrono::duration_cast<std::chrono::steady_clock::duration>(
      std::chrono::duration<double>(0.05))};
  std::chrono::steady_clock::time_point next_direct_command_time_{
    std::chrono::steady_clock::now()};
  int last_direct_direction_{0};
  int active_direct_direction_{0};
  bool has_direct_status_{false};
  bool direct_busy_{false};

  rclcpp::Publisher<trajectory_msgs::msg::JointTrajectory>::SharedPtr pub_;
  rclcpp::Publisher<onrobot_rg_msgs::msg::OnRobotRGOutput>::SharedPtr direct_pub_;
  rclcpp::Subscription<onrobot_rg_msgs::msg::OnRobotRGInput>::SharedPtr direct_status_sub_;
};

}  // namespace eurodao_joystick_teleop
