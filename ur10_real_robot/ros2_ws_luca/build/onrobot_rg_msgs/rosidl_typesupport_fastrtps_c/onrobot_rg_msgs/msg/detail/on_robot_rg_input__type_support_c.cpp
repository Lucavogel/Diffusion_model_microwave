// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
// generated code does not contain a copyright notice
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "onrobot_rg_msgs/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__struct.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__functions.h"
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


using _OnRobotRGInput__ros_msg_type = onrobot_rg_msgs__msg__OnRobotRGInput;

static bool _OnRobotRGInput__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _OnRobotRGInput__ros_msg_type * ros_message = static_cast<const _OnRobotRGInput__ros_msg_type *>(untyped_ros_message);
  // Field name: g_fof
  {
    cdr << ros_message->g_fof;
  }

  // Field name: g_gwd
  {
    cdr << ros_message->g_gwd;
  }

  // Field name: g_sta
  {
    cdr << ros_message->g_sta;
  }

  // Field name: g_wdf
  {
    cdr << ros_message->g_wdf;
  }

  // Field name: sta_fing_l
  {
    cdr << ros_message->sta_fing_l;
  }

  // Field name: sta_fing_r
  {
    cdr << ros_message->sta_fing_r;
  }

  // Field name: sta_prox_l
  {
    cdr << ros_message->sta_prox_l;
  }

  // Field name: sta_prox_r
  {
    cdr << ros_message->sta_prox_r;
  }

  // Field name: busy
  {
    cdr << ros_message->busy;
  }

  // Field name: grip_det
  {
    cdr << ros_message->grip_det;
  }

  // Field name: prox_off_l
  {
    cdr << ros_message->prox_off_l;
  }

  // Field name: prox_off_r
  {
    cdr << ros_message->prox_off_r;
  }

  // Field name: fx_l
  {
    cdr << ros_message->fx_l;
  }

  // Field name: fy_l
  {
    cdr << ros_message->fy_l;
  }

  // Field name: fz_l
  {
    cdr << ros_message->fz_l;
  }

  // Field name: tx_l
  {
    cdr << ros_message->tx_l;
  }

  // Field name: ty_l
  {
    cdr << ros_message->ty_l;
  }

  // Field name: tz_l
  {
    cdr << ros_message->tz_l;
  }

  // Field name: fx_r
  {
    cdr << ros_message->fx_r;
  }

  // Field name: fy_r
  {
    cdr << ros_message->fy_r;
  }

  // Field name: fz_r
  {
    cdr << ros_message->fz_r;
  }

  // Field name: tx_r
  {
    cdr << ros_message->tx_r;
  }

  // Field name: ty_r
  {
    cdr << ros_message->ty_r;
  }

  // Field name: tz_r
  {
    cdr << ros_message->tz_r;
  }

  // Field name: prox_l
  {
    cdr << ros_message->prox_l;
  }

  // Field name: prox_r
  {
    cdr << ros_message->prox_r;
  }

  // Field name: grip_width
  {
    cdr << ros_message->grip_width;
  }

  // Field name: in_zero
  {
    cdr << ros_message->in_zero;
  }

  return true;
}

static bool _OnRobotRGInput__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _OnRobotRGInput__ros_msg_type * ros_message = static_cast<_OnRobotRGInput__ros_msg_type *>(untyped_ros_message);
  // Field name: g_fof
  {
    cdr >> ros_message->g_fof;
  }

  // Field name: g_gwd
  {
    cdr >> ros_message->g_gwd;
  }

  // Field name: g_sta
  {
    cdr >> ros_message->g_sta;
  }

  // Field name: g_wdf
  {
    cdr >> ros_message->g_wdf;
  }

  // Field name: sta_fing_l
  {
    cdr >> ros_message->sta_fing_l;
  }

  // Field name: sta_fing_r
  {
    cdr >> ros_message->sta_fing_r;
  }

  // Field name: sta_prox_l
  {
    cdr >> ros_message->sta_prox_l;
  }

  // Field name: sta_prox_r
  {
    cdr >> ros_message->sta_prox_r;
  }

  // Field name: busy
  {
    cdr >> ros_message->busy;
  }

  // Field name: grip_det
  {
    cdr >> ros_message->grip_det;
  }

  // Field name: prox_off_l
  {
    cdr >> ros_message->prox_off_l;
  }

  // Field name: prox_off_r
  {
    cdr >> ros_message->prox_off_r;
  }

  // Field name: fx_l
  {
    cdr >> ros_message->fx_l;
  }

  // Field name: fy_l
  {
    cdr >> ros_message->fy_l;
  }

  // Field name: fz_l
  {
    cdr >> ros_message->fz_l;
  }

  // Field name: tx_l
  {
    cdr >> ros_message->tx_l;
  }

  // Field name: ty_l
  {
    cdr >> ros_message->ty_l;
  }

  // Field name: tz_l
  {
    cdr >> ros_message->tz_l;
  }

  // Field name: fx_r
  {
    cdr >> ros_message->fx_r;
  }

  // Field name: fy_r
  {
    cdr >> ros_message->fy_r;
  }

  // Field name: fz_r
  {
    cdr >> ros_message->fz_r;
  }

  // Field name: tx_r
  {
    cdr >> ros_message->tx_r;
  }

  // Field name: ty_r
  {
    cdr >> ros_message->ty_r;
  }

  // Field name: tz_r
  {
    cdr >> ros_message->tz_r;
  }

  // Field name: prox_l
  {
    cdr >> ros_message->prox_l;
  }

  // Field name: prox_r
  {
    cdr >> ros_message->prox_r;
  }

  // Field name: grip_width
  {
    cdr >> ros_message->grip_width;
  }

  // Field name: in_zero
  {
    cdr >> ros_message->in_zero;
  }

  return true;
}  // NOLINT(readability/fn_size)

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_onrobot_rg_msgs
size_t get_serialized_size_onrobot_rg_msgs__msg__OnRobotRGInput(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _OnRobotRGInput__ros_msg_type * ros_message = static_cast<const _OnRobotRGInput__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name g_fof
  {
    size_t item_size = sizeof(ros_message->g_fof);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name g_gwd
  {
    size_t item_size = sizeof(ros_message->g_gwd);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name g_sta
  {
    size_t item_size = sizeof(ros_message->g_sta);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name g_wdf
  {
    size_t item_size = sizeof(ros_message->g_wdf);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name sta_fing_l
  {
    size_t item_size = sizeof(ros_message->sta_fing_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name sta_fing_r
  {
    size_t item_size = sizeof(ros_message->sta_fing_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name sta_prox_l
  {
    size_t item_size = sizeof(ros_message->sta_prox_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name sta_prox_r
  {
    size_t item_size = sizeof(ros_message->sta_prox_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name busy
  {
    size_t item_size = sizeof(ros_message->busy);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name grip_det
  {
    size_t item_size = sizeof(ros_message->grip_det);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name prox_off_l
  {
    size_t item_size = sizeof(ros_message->prox_off_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name prox_off_r
  {
    size_t item_size = sizeof(ros_message->prox_off_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name fx_l
  {
    size_t item_size = sizeof(ros_message->fx_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name fy_l
  {
    size_t item_size = sizeof(ros_message->fy_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name fz_l
  {
    size_t item_size = sizeof(ros_message->fz_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name tx_l
  {
    size_t item_size = sizeof(ros_message->tx_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name ty_l
  {
    size_t item_size = sizeof(ros_message->ty_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name tz_l
  {
    size_t item_size = sizeof(ros_message->tz_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name fx_r
  {
    size_t item_size = sizeof(ros_message->fx_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name fy_r
  {
    size_t item_size = sizeof(ros_message->fy_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name fz_r
  {
    size_t item_size = sizeof(ros_message->fz_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name tx_r
  {
    size_t item_size = sizeof(ros_message->tx_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name ty_r
  {
    size_t item_size = sizeof(ros_message->ty_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name tz_r
  {
    size_t item_size = sizeof(ros_message->tz_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name prox_l
  {
    size_t item_size = sizeof(ros_message->prox_l);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name prox_r
  {
    size_t item_size = sizeof(ros_message->prox_r);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name grip_width
  {
    size_t item_size = sizeof(ros_message->grip_width);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name in_zero
  {
    size_t item_size = sizeof(ros_message->in_zero);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _OnRobotRGInput__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_onrobot_rg_msgs__msg__OnRobotRGInput(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_onrobot_rg_msgs
size_t max_serialized_size_onrobot_rg_msgs__msg__OnRobotRGInput(
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

  // member: g_fof
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: g_gwd
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: g_sta
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: g_wdf
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: sta_fing_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: sta_fing_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: sta_prox_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: sta_prox_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: busy
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: grip_det
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: prox_off_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: prox_off_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint16_t);
    current_alignment += array_size * sizeof(uint16_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint16_t));
  }
  // member: fx_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: fy_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: fz_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: tx_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: ty_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: tz_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: fx_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: fy_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: fz_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: tx_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: ty_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: tz_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: prox_l
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: prox_r
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: grip_width
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint32_t);
    current_alignment += array_size * sizeof(uint32_t) +
      eprosima::fastcdr::Cdr::alignment(current_alignment, sizeof(uint32_t));
  }
  // member: in_zero
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = onrobot_rg_msgs__msg__OnRobotRGInput;
    is_plain =
      (
      offsetof(DataType, in_zero) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static size_t _OnRobotRGInput__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_onrobot_rg_msgs__msg__OnRobotRGInput(
    full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}


static message_type_support_callbacks_t __callbacks_OnRobotRGInput = {
  "onrobot_rg_msgs::msg",
  "OnRobotRGInput",
  _OnRobotRGInput__cdr_serialize,
  _OnRobotRGInput__cdr_deserialize,
  _OnRobotRGInput__get_serialized_size,
  _OnRobotRGInput__max_serialized_size
};

static rosidl_message_type_support_t _OnRobotRGInput__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_OnRobotRGInput,
  get_message_typesupport_handle_function,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, onrobot_rg_msgs, msg, OnRobotRGInput)() {
  return &_OnRobotRGInput__type_support;
}

#if defined(__cplusplus)
}
#endif
