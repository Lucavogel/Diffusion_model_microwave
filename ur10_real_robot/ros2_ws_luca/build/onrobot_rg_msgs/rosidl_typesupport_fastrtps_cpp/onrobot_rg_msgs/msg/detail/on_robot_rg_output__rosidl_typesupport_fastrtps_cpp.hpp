// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "onrobot_rg_msgs/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__struct.hpp"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

#include "fastcdr/Cdr.h"

namespace onrobot_rg_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_onrobot_rg_msgs
cdr_serialize(
  const onrobot_rg_msgs::msg::OnRobotRGOutput & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_onrobot_rg_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  onrobot_rg_msgs::msg::OnRobotRGOutput & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_onrobot_rg_msgs
get_serialized_size(
  const onrobot_rg_msgs::msg::OnRobotRGOutput & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_onrobot_rg_msgs
max_serialized_size_OnRobotRGOutput(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace onrobot_rg_msgs

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_onrobot_rg_msgs
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, onrobot_rg_msgs, msg, OnRobotRGOutput)();

#ifdef __cplusplus
}
#endif

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
