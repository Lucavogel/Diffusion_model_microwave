// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__TRAITS_HPP_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace onrobot_rg_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const OnRobotRGInput & msg,
  std::ostream & out)
{
  out << "{";
  // member: g_fof
  {
    out << "g_fof: ";
    rosidl_generator_traits::value_to_yaml(msg.g_fof, out);
    out << ", ";
  }

  // member: g_gwd
  {
    out << "g_gwd: ";
    rosidl_generator_traits::value_to_yaml(msg.g_gwd, out);
    out << ", ";
  }

  // member: g_sta
  {
    out << "g_sta: ";
    rosidl_generator_traits::value_to_yaml(msg.g_sta, out);
    out << ", ";
  }

  // member: g_wdf
  {
    out << "g_wdf: ";
    rosidl_generator_traits::value_to_yaml(msg.g_wdf, out);
    out << ", ";
  }

  // member: sta_fing_l
  {
    out << "sta_fing_l: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_fing_l, out);
    out << ", ";
  }

  // member: sta_fing_r
  {
    out << "sta_fing_r: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_fing_r, out);
    out << ", ";
  }

  // member: sta_prox_l
  {
    out << "sta_prox_l: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_prox_l, out);
    out << ", ";
  }

  // member: sta_prox_r
  {
    out << "sta_prox_r: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_prox_r, out);
    out << ", ";
  }

  // member: busy
  {
    out << "busy: ";
    rosidl_generator_traits::value_to_yaml(msg.busy, out);
    out << ", ";
  }

  // member: grip_det
  {
    out << "grip_det: ";
    rosidl_generator_traits::value_to_yaml(msg.grip_det, out);
    out << ", ";
  }

  // member: prox_off_l
  {
    out << "prox_off_l: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_off_l, out);
    out << ", ";
  }

  // member: prox_off_r
  {
    out << "prox_off_r: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_off_r, out);
    out << ", ";
  }

  // member: fx_l
  {
    out << "fx_l: ";
    rosidl_generator_traits::value_to_yaml(msg.fx_l, out);
    out << ", ";
  }

  // member: fy_l
  {
    out << "fy_l: ";
    rosidl_generator_traits::value_to_yaml(msg.fy_l, out);
    out << ", ";
  }

  // member: fz_l
  {
    out << "fz_l: ";
    rosidl_generator_traits::value_to_yaml(msg.fz_l, out);
    out << ", ";
  }

  // member: tx_l
  {
    out << "tx_l: ";
    rosidl_generator_traits::value_to_yaml(msg.tx_l, out);
    out << ", ";
  }

  // member: ty_l
  {
    out << "ty_l: ";
    rosidl_generator_traits::value_to_yaml(msg.ty_l, out);
    out << ", ";
  }

  // member: tz_l
  {
    out << "tz_l: ";
    rosidl_generator_traits::value_to_yaml(msg.tz_l, out);
    out << ", ";
  }

  // member: fx_r
  {
    out << "fx_r: ";
    rosidl_generator_traits::value_to_yaml(msg.fx_r, out);
    out << ", ";
  }

  // member: fy_r
  {
    out << "fy_r: ";
    rosidl_generator_traits::value_to_yaml(msg.fy_r, out);
    out << ", ";
  }

  // member: fz_r
  {
    out << "fz_r: ";
    rosidl_generator_traits::value_to_yaml(msg.fz_r, out);
    out << ", ";
  }

  // member: tx_r
  {
    out << "tx_r: ";
    rosidl_generator_traits::value_to_yaml(msg.tx_r, out);
    out << ", ";
  }

  // member: ty_r
  {
    out << "ty_r: ";
    rosidl_generator_traits::value_to_yaml(msg.ty_r, out);
    out << ", ";
  }

  // member: tz_r
  {
    out << "tz_r: ";
    rosidl_generator_traits::value_to_yaml(msg.tz_r, out);
    out << ", ";
  }

  // member: prox_l
  {
    out << "prox_l: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_l, out);
    out << ", ";
  }

  // member: prox_r
  {
    out << "prox_r: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_r, out);
    out << ", ";
  }

  // member: grip_width
  {
    out << "grip_width: ";
    rosidl_generator_traits::value_to_yaml(msg.grip_width, out);
    out << ", ";
  }

  // member: in_zero
  {
    out << "in_zero: ";
    rosidl_generator_traits::value_to_yaml(msg.in_zero, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const OnRobotRGInput & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: g_fof
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "g_fof: ";
    rosidl_generator_traits::value_to_yaml(msg.g_fof, out);
    out << "\n";
  }

  // member: g_gwd
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "g_gwd: ";
    rosidl_generator_traits::value_to_yaml(msg.g_gwd, out);
    out << "\n";
  }

  // member: g_sta
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "g_sta: ";
    rosidl_generator_traits::value_to_yaml(msg.g_sta, out);
    out << "\n";
  }

  // member: g_wdf
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "g_wdf: ";
    rosidl_generator_traits::value_to_yaml(msg.g_wdf, out);
    out << "\n";
  }

  // member: sta_fing_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sta_fing_l: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_fing_l, out);
    out << "\n";
  }

  // member: sta_fing_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sta_fing_r: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_fing_r, out);
    out << "\n";
  }

  // member: sta_prox_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sta_prox_l: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_prox_l, out);
    out << "\n";
  }

  // member: sta_prox_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "sta_prox_r: ";
    rosidl_generator_traits::value_to_yaml(msg.sta_prox_r, out);
    out << "\n";
  }

  // member: busy
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "busy: ";
    rosidl_generator_traits::value_to_yaml(msg.busy, out);
    out << "\n";
  }

  // member: grip_det
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "grip_det: ";
    rosidl_generator_traits::value_to_yaml(msg.grip_det, out);
    out << "\n";
  }

  // member: prox_off_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "prox_off_l: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_off_l, out);
    out << "\n";
  }

  // member: prox_off_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "prox_off_r: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_off_r, out);
    out << "\n";
  }

  // member: fx_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fx_l: ";
    rosidl_generator_traits::value_to_yaml(msg.fx_l, out);
    out << "\n";
  }

  // member: fy_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fy_l: ";
    rosidl_generator_traits::value_to_yaml(msg.fy_l, out);
    out << "\n";
  }

  // member: fz_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fz_l: ";
    rosidl_generator_traits::value_to_yaml(msg.fz_l, out);
    out << "\n";
  }

  // member: tx_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "tx_l: ";
    rosidl_generator_traits::value_to_yaml(msg.tx_l, out);
    out << "\n";
  }

  // member: ty_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "ty_l: ";
    rosidl_generator_traits::value_to_yaml(msg.ty_l, out);
    out << "\n";
  }

  // member: tz_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "tz_l: ";
    rosidl_generator_traits::value_to_yaml(msg.tz_l, out);
    out << "\n";
  }

  // member: fx_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fx_r: ";
    rosidl_generator_traits::value_to_yaml(msg.fx_r, out);
    out << "\n";
  }

  // member: fy_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fy_r: ";
    rosidl_generator_traits::value_to_yaml(msg.fy_r, out);
    out << "\n";
  }

  // member: fz_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "fz_r: ";
    rosidl_generator_traits::value_to_yaml(msg.fz_r, out);
    out << "\n";
  }

  // member: tx_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "tx_r: ";
    rosidl_generator_traits::value_to_yaml(msg.tx_r, out);
    out << "\n";
  }

  // member: ty_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "ty_r: ";
    rosidl_generator_traits::value_to_yaml(msg.ty_r, out);
    out << "\n";
  }

  // member: tz_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "tz_r: ";
    rosidl_generator_traits::value_to_yaml(msg.tz_r, out);
    out << "\n";
  }

  // member: prox_l
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "prox_l: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_l, out);
    out << "\n";
  }

  // member: prox_r
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "prox_r: ";
    rosidl_generator_traits::value_to_yaml(msg.prox_r, out);
    out << "\n";
  }

  // member: grip_width
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "grip_width: ";
    rosidl_generator_traits::value_to_yaml(msg.grip_width, out);
    out << "\n";
  }

  // member: in_zero
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "in_zero: ";
    rosidl_generator_traits::value_to_yaml(msg.in_zero, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const OnRobotRGInput & msg, bool use_flow_style = false)
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
  const onrobot_rg_msgs::msg::OnRobotRGInput & msg,
  std::ostream & out, size_t indentation = 0)
{
  onrobot_rg_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use onrobot_rg_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const onrobot_rg_msgs::msg::OnRobotRGInput & msg)
{
  return onrobot_rg_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<onrobot_rg_msgs::msg::OnRobotRGInput>()
{
  return "onrobot_rg_msgs::msg::OnRobotRGInput";
}

template<>
inline const char * name<onrobot_rg_msgs::msg::OnRobotRGInput>()
{
  return "onrobot_rg_msgs/msg/OnRobotRGInput";
}

template<>
struct has_fixed_size<onrobot_rg_msgs::msg::OnRobotRGInput>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<onrobot_rg_msgs::msg::OnRobotRGInput>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<onrobot_rg_msgs::msg::OnRobotRGInput>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__TRAITS_HPP_
