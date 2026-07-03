#include <cmath>
#include <optional>
#include <sstream>
#include <string>
#include <utility>

#include "eurodao_joystick_teleop/joystick_teleop_node.hpp"

namespace eurodao_joystick_teleop {
namespace {

constexpr const char * kJoyTopic = "/joy";
constexpr const char * kTeleopTwistStampedTopic = "/teleop/twist_cmd";
constexpr const char * kTeleopTwistTopic = "/teleop/cmd";

std::string escape_json_string(const std::string & s)
{
  std::string result;
  result.reserve(s.size());
  for (const char c : s) {
    switch (c) {
      case '"':  result += "\\\""; break;
      case '\\': result += "\\\\"; break;
      case '\n': result += "\\n";  break;
      case '\r': result += "\\r";  break;
      case '\t': result += "\\t";  break;
      default:   result.push_back(c); break;
    }
  }
  return result;
}

std::string status_json(
  bool safe,
  const std::string & reason,
  double gripper_position)
{
  std::ostringstream oss;
  oss << "{";
  oss << "\"node\":\"joystick_teleop\",";
  oss << "\"safe\":" << (safe ? "true" : "false") << ",";
  oss << "\"reason\":\"" << escape_json_string(reason) << "\",";
  oss << "\"gripper_position\":" << gripper_position;
  oss << "}";
  return oss.str();
}

}  // namespace

void JoystickTeleopNode::ProcessorSet::reset()
{
  lx.reset();
  ly.reset();
  lz.reset();
  ax.reset();
  ay.reset();
  az.reset();
}

JoystickTeleopNode::JoystickTeleopNode()
: rclcpp::Node("joystick_teleop")
{
  declare_parameters_();

  publish_rate_hz_ = get_parameter("publish_rate_hz").as_double();
  frame_id_ = get_parameter("twist_frame_id").as_string();
  dpad_horizontal_axis_ = static_cast<int>(get_parameter("dpad_mapping.horizontal_axis").as_int());
  dpad_left_value_ = get_parameter("dpad_mapping.left_value").as_double();
  dpad_right_value_ = get_parameter("dpad_mapping.right_value").as_double();
  dpad_activation_threshold_ = get_parameter("dpad_mapping.activation_threshold").as_double();

  const double deadzone = get_parameter("input_processing.deadzone").as_double();
  const double exponent = get_parameter("input_processing.nonlinear_exponent").as_double();
  const double alpha = get_parameter("input_processing.lowpass_alpha").as_double();

  axis_mapper_ = build_axis_mapper_();
  processors_.lx = InputProcessor(deadzone, exponent, alpha);
  processors_.ly = InputProcessor(deadzone, exponent, alpha);
  processors_.lz = InputProcessor(deadzone, exponent, alpha);
  processors_.ax = InputProcessor(deadzone, exponent, alpha);
  processors_.ay = InputProcessor(deadzone, exponent, alpha);
  processors_.az = InputProcessor(deadzone, exponent, alpha);

  SafetyGuard::Config safety_config;
  safety_config.deadman_enabled = get_parameter("deadman_switch.enabled").as_bool();
  safety_config.deadman_button = get_parameter("button_mapping.deadman_switch").as_int();
  safety_config.joy_timeout_sec = get_parameter("joy_timeout_sec").as_double();
  safety_config.startup_delay_sec = get_parameter("safety.startup_delay_sec").as_double();
  safety_guard_.reconfigure(safety_config);
  safety_guard_.mark_started(std::chrono::steady_clock::now());

  button_handler_ = std::make_unique<ButtonHandler>(
    this,
    get_parameter("button_mapping.estop").as_int(),
    get_parameter("button_mapping.gripper_open").as_int(),
    get_parameter("button_mapping.gripper_close").as_int(),
    get_parameter("button_mapping.speed_down").as_int(),
    get_parameter("button_mapping.speed_up").as_int(),
    get_parameter("button_mapping.go_home").as_int());

  gripper_controller_ = std::make_unique<GripperController>(
    this,
    get_parameter("gripper.joint_name").as_string(),
    get_parameter("gripper.limit_open").as_double(),
    get_parameter("gripper.limit_close").as_double(),
    get_parameter("gripper.trajectory_duration").as_double(),
    get_parameter("gripper.direct_command_topic").as_string(),
    get_parameter("gripper.direct_status_topic").as_string(),
    get_parameter("gripper.direct_open_width_mm").as_double(),
    get_parameter("gripper.direct_close_width_mm").as_double(),
    get_parameter("gripper.direct_open_force_n").as_double(),
    get_parameter("gripper.direct_close_force_n").as_double(),
    get_parameter("gripper.direct_step_mm").as_double(),
    get_parameter("gripper.direct_repeat_period_sec").as_double());

  joy_sub_ = create_subscription<sensor_msgs::msg::Joy>(
    kJoyTopic,
    10,
    [this](const sensor_msgs::msg::Joy::SharedPtr msg) {
      std::lock_guard<std::mutex> lock(joy_mutex_);
      last_buttons_ = msg->buttons;
      last_axes_ = msg->axes;
      safety_guard_.update_joy_time(std::chrono::steady_clock::now());
    });

  twist_stamped_pub_ = create_publisher<geometry_msgs::msg::TwistStamped>(kTeleopTwistStampedTopic, 10);
  twist_pub_ = create_publisher<geometry_msgs::msg::Twist>(kTeleopTwistTopic, 10);
  status_pub_ = create_publisher<std_msgs::msg::String>("~/status", 10);

  status_srv_ = create_service<std_srvs::srv::Trigger>(
    "~/get_status",
    [this](
      const std::shared_ptr<std_srvs::srv::Trigger::Request> /*request*/,
      std::shared_ptr<std_srvs::srv::Trigger::Response> response) {
      const bool safe = (safety_reason_ == "ok");
      response->success = true;
      response->message = status_json(
        safe,
        safety_reason_,
        gripper_controller_ ? gripper_controller_->position() : 0.0);
    });

  const auto timer_period = std::chrono::duration<double>(1.0 / publish_rate_hz_);
  timer_ = create_wall_timer(timer_period, std::bind(&JoystickTeleopNode::on_timer_, this));

  RCLCPP_INFO(get_logger(), "Joystick teleop node started at %.2fHz (Pure Input Source Mode)", publish_rate_hz_);
}

void JoystickTeleopNode::declare_parameters_()
{
  declare_parameter("publish_rate_hz", 50.0);
  declare_parameter("joy_timeout_sec", 0.2);
  declare_parameter("twist_frame_id", "base_link");

  declare_parameter("input_processing.deadzone", 0.05);
  declare_parameter("input_processing.nonlinear_exponent", 1.5);
  declare_parameter("input_processing.lowpass_alpha", 0.8);

  declare_parameter("dpad_mapping.horizontal_axis", 6);
  declare_parameter("dpad_mapping.left_value", 1.0);
  declare_parameter("dpad_mapping.right_value", -1.0);
  declare_parameter("dpad_mapping.activation_threshold", 0.5);

  struct AxisDefaults {
    int axis;
    std::string component;
    double scale;
    bool trigger_mode;
  };

  const std::vector<std::pair<std::string, AxisDefaults>> defaults = {
    {"left_stick_x", {0, "lx", 1.0, false}},
    {"left_stick_y", {1, "ly", 1.0, false}},
    {"lt_trigger", {2, "ay", 1.0, true}},
    {"right_stick_x", {3, "az", -1.0, false}},
    {"right_stick_y", {4, "lz", 1.0, false}},
    {"rt_trigger", {5, "ax", 1.0, true}},
  };

  for (const auto & [name, d] : defaults) {
    declare_parameter("axis_mapping." + name + ".axis", d.axis);
    declare_parameter("axis_mapping." + name + ".component", d.component);
    declare_parameter("axis_mapping." + name + ".scale", d.scale);
    declare_parameter("axis_mapping." + name + ".trigger_mode", d.trigger_mode);
  }

  declare_parameter("button_mapping.deadman_switch", 4);
  declare_parameter("button_mapping.estop", 6);
  declare_parameter("button_mapping.gripper_open", 0);
  declare_parameter("button_mapping.gripper_close", 1);
  declare_parameter("button_mapping.speed_down", 3);
  declare_parameter("button_mapping.speed_up", 2);
  declare_parameter("button_mapping.go_home", 7);

  declare_parameter("deadman_switch.enabled", true);

  declare_parameter("gripper.joint_name", "onrobot_2fg14_finger_width");
  declare_parameter("gripper.trajectory_duration", 0.5);
  declare_parameter("gripper.limit_open", 0.105);
  declare_parameter("gripper.limit_close", 0.055);
  declare_parameter("gripper.direct_command_topic", "OnRobotRGOutput");
  declare_parameter("gripper.direct_status_topic", "OnRobotRGInput");
  declare_parameter("gripper.direct_open_width_mm", 100.0);
  declare_parameter("gripper.direct_close_width_mm", 0.0);
  declare_parameter("gripper.direct_open_force_n", 10.0);
  declare_parameter("gripper.direct_close_force_n", 40.0);
  declare_parameter("gripper.direct_step_mm", 1.0);
  declare_parameter("gripper.direct_repeat_period_sec", 0.05);

  declare_parameter("safety.startup_delay_sec", 1.0);
}

AxisMapper JoystickTeleopNode::build_axis_mapper_()
{
  const std::vector<std::string> names = {
    "left_stick_x",
    "left_stick_y",
    "lt_trigger",
    "right_stick_x",
    "right_stick_y",
    "rt_trigger",
  };

  std::vector<AxisMapping> mappings;
  mappings.reserve(names.size());
  for (const auto & name : names) {
    const int axis = get_parameter("axis_mapping." + name + ".axis").as_int();
    const std::string component_str = get_parameter("axis_mapping." + name + ".component").as_string();
    const double scale = get_parameter("axis_mapping." + name + ".scale").as_double();
    const bool trigger_mode = get_parameter("axis_mapping." + name + ".trigger_mode").as_bool();

    const auto comp = component_from_string(component_str);
    if (!comp) {
      RCLCPP_WARN(
        get_logger(),
        "Invalid component '%s' for axis_mapping.%s.component; skipping mapping",
        component_str.c_str(),
        name.c_str());
      continue;
    }

    AxisMapping m;
    m.axis = axis;
    m.component = *comp;
    m.scale = scale;
    m.trigger_mode = trigger_mode;
    mappings.push_back(m);
  }

  return AxisMapper(std::move(mappings));
}

int JoystickTeleopNode::detect_dpad_horizontal_(const std::vector<float> & axes) const
{
  if (dpad_horizontal_axis_ < 0) {
    return 0;
  }

  const auto idx = static_cast<std::size_t>(dpad_horizontal_axis_);
  if (idx >= axes.size()) {
    return 0;
  }

  const double value = static_cast<double>(axes[idx]);
  if (std::fabs(value - dpad_right_value_) <= dpad_activation_threshold_) {
    return 1;
  }
  if (std::fabs(value - dpad_left_value_) <= dpad_activation_threshold_) {
    return -1;
  }

  return 0;
}

void JoystickTeleopNode::on_timer_()
{
  std::vector<int32_t> buttons;
  std::vector<float> axes;
  {
    std::lock_guard<std::mutex> lock(joy_mutex_);
    buttons = last_buttons_.value_or(std::vector<int32_t>{});
    axes = last_axes_.value_or(std::vector<float>{});
  }

  const auto now_steady = std::chrono::steady_clock::now();
  const auto [is_safe, reason] = safety_guard_.is_safe(buttons, now_steady);
  safety_reason_ = reason;

  ButtonState btn;
  if (button_handler_) {
    btn = button_handler_->update(buttons);
  }

  geometry_msgs::msg::Twist twist;
  if (is_safe) {
    const auto raw = axis_mapper_.map_axes(axes);
    const TwistComponents processed = process_components_(raw);
    const int dpad_horizontal = detect_dpad_horizontal_(axes);
    const bool dpad_open = (dpad_horizontal == 1);
    const bool dpad_close = (dpad_horizontal == -1);

    twist.linear.x = processed.lx;
    twist.linear.y = processed.ly;
    twist.linear.z = processed.lz;
    twist.angular.x = processed.ax;
    twist.angular.y = processed.ay;
    twist.angular.z = processed.az;

    if (gripper_controller_) {
      gripper_controller_->update(btn.gripper_open, btn.gripper_close);
      gripper_controller_->update_direct(dpad_open, dpad_close);
    }
  } else {
    processors_.reset();
    if (gripper_controller_) {
      gripper_controller_->update_direct(false, false);
    }
  }

  geometry_msgs::msg::TwistStamped twist_stamped;
  twist_stamped.header.stamp = get_clock()->now();
  twist_stamped.header.frame_id = frame_id_;
  twist_stamped.twist = twist;
  twist_stamped_pub_->publish(twist_stamped);

  twist_pub_->publish(twist);

  maybe_publish_status_(is_safe, reason);
}

TwistComponents JoystickTeleopNode::process_components_(const TwistComponents & raw)
{
  TwistComponents out;
  out.lx = processors_.lx.process(raw.lx);
  out.ly = processors_.ly.process(raw.ly);
  out.lz = processors_.lz.process(raw.lz);
  out.ax = processors_.ax.process(raw.ax);
  out.ay = processors_.ay.process(raw.ay);
  out.az = processors_.az.process(raw.az);
  return out;
}

void JoystickTeleopNode::maybe_publish_status_(bool safe, const std::string & reason)
{
  const auto now = std::chrono::steady_clock::now();
  if (next_status_time_ && now < *next_status_time_) {
    return;
  }
  next_status_time_ = now + std::chrono::seconds(1);

  std_msgs::msg::String msg;
  msg.data = status_json(
    safe,
    reason,
    gripper_controller_ ? gripper_controller_->position() : 0.0);
  status_pub_->publish(msg);
}

}  // namespace eurodao_joystick_teleop
