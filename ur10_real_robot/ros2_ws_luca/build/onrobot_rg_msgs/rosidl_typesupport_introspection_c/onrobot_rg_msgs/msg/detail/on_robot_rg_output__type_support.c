// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__rosidl_typesupport_introspection_c.h"
#include "onrobot_rg_msgs/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__functions.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__struct.h"


#ifdef __cplusplus
extern "C"
{
#endif

void onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  onrobot_rg_msgs__msg__OnRobotRGOutput__init(message_memory);
}

void onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_fini_function(void * message_memory)
{
  onrobot_rg_msgs__msg__OnRobotRGOutput__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_member_array[6] = {
  {
    "r_gfr",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(onrobot_rg_msgs__msg__OnRobotRGOutput, r_gfr),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "r_gwd",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(onrobot_rg_msgs__msg__OnRobotRGOutput, r_gwd),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "r_ctr",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT8,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(onrobot_rg_msgs__msg__OnRobotRGOutput, r_ctr),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "out_zero",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(onrobot_rg_msgs__msg__OnRobotRGOutput, out_zero),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "out_prox_off_r",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(onrobot_rg_msgs__msg__OnRobotRGOutput, out_prox_off_r),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "out_prox_off_l",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT16,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(onrobot_rg_msgs__msg__OnRobotRGOutput, out_prox_off_l),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL,  // fetch(index, &value) function pointer
    NULL,  // assign(index, value) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_members = {
  "onrobot_rg_msgs__msg",  // message namespace
  "OnRobotRGOutput",  // message name
  6,  // number of fields
  sizeof(onrobot_rg_msgs__msg__OnRobotRGOutput),
  onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_member_array,  // message members
  onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_init_function,  // function to initialize message memory (memory has to be allocated)
  onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_type_support_handle = {
  0,
  &onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_onrobot_rg_msgs
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, onrobot_rg_msgs, msg, OnRobotRGOutput)() {
  if (!onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_type_support_handle.typesupport_identifier) {
    onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &onrobot_rg_msgs__msg__OnRobotRGOutput__rosidl_typesupport_introspection_c__OnRobotRGOutput_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
