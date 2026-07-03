// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__TRAITS_HPP_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace onrobot_rg_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const OnRobotRGOutput & msg,
  std::ostream & out)
{
  out << "{";
  // member: r_gfr
  {
    out << "r_gfr: ";
    rosidl_generator_traits::value_to_yaml(msg.r_gfr, out);
    out << ", ";
  }

  // member: r_gwd
  {
    out << "r_gwd: ";
    rosidl_generator_traits::value_to_yaml(msg.r_gwd, out);
    out << ", ";
  }

  // member: r_ctr
  {
    out << "r_ctr: ";
    rosidl_generator_traits::value_to_yaml(msg.r_ctr, out);
    out << ", ";
  }

  // member: out_zero
  {
    out << "out_zero: ";
    rosidl_generator_traits::value_to_yaml(msg.out_zero, out);
    out << ", ";
  }

  // member: out_prox_off_r
  {
    out << "out_prox_off_r: ";
    rosidl_generator_traits::value_to_yaml(msg.out_prox_off_r, out);
    out << ", ";
  }

  // member: out_prox_off_l
  {
    out << "out_prox_off_l: ";
    rosidl_generator_traits::value_to_yaml(msg.out_prox_off_l, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const OnRobotRGOutput & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: r_gfr
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "r_gfr: ";
    rosidl_generator_traits::value_to_yaml(msg.r_gfr, out);
    out << "\n";
  }

  // member: r_gwd
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "r_gwd: ";
    rosidl_generator_traits::value_to_yaml(msg.r_gwd, out);
    out << "\n";
  }

  // member: r_ctr
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "r_ctr: ";
    rosidl_generator_traits::value_to_yaml(msg.r_ctr, out);
    out << "\n";
  }

  // member: out_zero
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "out_zero: ";
    rosidl_generator_traits::value_to_yaml(msg.out_zero, out);
    out << "\n";
  }

  // member: out_prox_off_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "out_prox_off_r: ";
    rosidl_generator_traits::value_to_yaml(msg.out_prox_off_r, out);
    out << "\n";
  }

  // member: out_prox_off_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "out_prox_off_l: ";
    rosidl_generator_traits::value_to_yaml(msg.out_prox_off_l, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const OnRobotRGOutput & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace onrobot_rg_msgs

namespace rosidl_generator_traits
{

[[deprecated("use onrobot_rg_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const onrobot_rg_msgs::msg::OnRobotRGOutput & msg,
  std::ostream & out, size_t indentation = 0)
{
  onrobot_rg_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use onrobot_rg_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const onrobot_rg_msgs::msg::OnRobotRGOutput & msg)
{
  return onrobot_rg_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<onrobot_rg_msgs::msg::OnRobotRGOutput>()
{
  return "onrobot_rg_msgs::msg::OnRobotRGOutput";
}

template<>
inline const char * name<onrobot_rg_msgs::msg::OnRobotRGOutput>()
{
  return "onrobot_rg_msgs/msg/OnRobotRGOutput";
}

template<>
struct has_fixed_size<onrobot_rg_msgs::msg::OnRobotRGOutput>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<onrobot_rg_msgs::msg::OnRobotRGOutput>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<onrobot_rg_msgs::msg::OnRobotRGOutput>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__TRAITS_HPP_
