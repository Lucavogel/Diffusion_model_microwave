#include <memory>

#include <rclcpp/rclcpp.hpp>

#include "eurodao_joystick_teleop/joystick_teleop_node.hpp"

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<eurodao_joystick_teleop::JoystickTeleopNode>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
