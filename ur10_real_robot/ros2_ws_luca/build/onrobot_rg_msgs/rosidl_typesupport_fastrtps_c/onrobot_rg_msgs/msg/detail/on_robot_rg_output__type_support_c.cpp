// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "onrobot_rg_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__struct.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__functions.h"
#include "fastcdr/Cdr.h"

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

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif


// forward declare type support functions


using _OnRobotRGOutput__ros_msg_type = onrobot_rg_msgs__msg__OnRobotRGOutput;

static bool _OnRobotRGOutput__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _OnRobotRGOutput__ros_msg_type * ros_message = static_cast<const _OnRobotRGOutput__ros_msg_type *>(untyped_ros_message);
  // Field name: r_gfr
  {
    cdr << ros_message->r_gfr;
  }

  // Field name: r_gwd
  {
    cdr << ros_message->r_gwd;
  }

  // Field name: r_ctr
  {
    cdr << ros_message->r_ctr;
  }

  // Field name: out_zero
  {
    cdr << ros_message->out_zero;
  }

  // Field name: out_prox_off_r
  {
    cdr << ros_message->out_prox_off_r;
  }

  // Field name: out_prox_off_l
  {
    cdr << ros_message->out_prox_off_l;
  }

  return true;
}

static bool _OnRobotRGOutput__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _OnRobotRGOutput__ros_msg_type * ros_message = static_cast<_OnRobotRGOutput__ros_msg_type *>(untyped_ros_message);
  // Field name: r_gfr
  {
    cdr >> ros_message->r_gfr;
  }

  // Field name: r_gwd
  {
    cdr >> ros_message->r_gwd;
  }

  // Field name: r_ctr
  {
    cdr >> ros_message->r_ctr;
  }

  // Field name: out_zero
  {
    cdr >> ros_message->out_zero;
  }

  // Field name: out_prox_off_r
  {
    cdr >> ros_message->out_prox_off_r;
  }

  // Field name: out_prox_off_l
  {
    cdr >> ros_message->out_prox_off_l;
  }

  return true;
}  // NOLINT(readability/fn_size)

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_onrobot_rg_msgs
size_t get_serialized_size_onrobot_rg_msgs__msg__OnRobotRGOutput(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _OnRobotRGOutput__ros_msg_type * ros_message = static_cast<const _OnRobotRGOutput__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name r_gfr
  {
    size_t item_size = sizeof(ros_message->r_gfr);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name r_gwd
  {
    size_t item_size = sizeof(ros_message->r_gwd);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name r_ctr
  {
    size_t item_size = sizeof(ros_message->r_ctr);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name out_zero
  {
    size_t item_size = sizeof(ros_message->out_zero);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name out_prox_off_r
  {
    size_t item_size = sizeof(ros_message->out_prox_off_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name out_prox_off_l
  {
    size_t item_size = sizeof(ros_message->out_prox_off_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _OnRobotRGOutput__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_onrobot_rg_msgs__msg__OnRobotRGOutput(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_onrobot_rg_msgs
size_t max_serialized_size_onrobot_rg_msgs__msg__OnRobotRGOutput(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;

  // member: r_gfr
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: r_gwd
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: r_ctr
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: out_zero
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: out_prox_off_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: out_prox_off_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = onrobot_rg_msgs__msg__OnRobotRGOutput;
    is_plain =
      (
      offsetof(DataType, out_prox_off_l) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static size_t _OnRobotRGOutput__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_onrobot_rg_msgs__msg__OnRobotRGOutput(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_OnRobotRGOutput = {
  "onrobot_rg_msgs::msg",
  "OnRobotRGOutput",
  _OnRobotRGOutput__cdr_serialize,
  _OnRobotRGOutput__cdr_deserialize,
  _OnRobotRGOutput__get_serialized_size,
  _OnRobotRGOutput__max_serialized_size
};

static rosidl_message_type_support_t _OnRobotRGOutput__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_OnRobotRGOutput,
  get_message_typesupport_handle_function,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, onrobot_rg_msgs, msg, OnRobotRGOutput)() {
  return &_OnRobotRGOutput__type_support;
}

#if defined(__cplusplus)
}
#endif
