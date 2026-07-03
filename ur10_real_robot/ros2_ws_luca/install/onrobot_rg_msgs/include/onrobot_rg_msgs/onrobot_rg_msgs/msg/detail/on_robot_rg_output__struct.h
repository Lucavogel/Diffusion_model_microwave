// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__STRUCT_H_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/OnRobotRGOutput in the package onrobot_rg_msgs.
/**
  * r_gfr : The target force to be reached when gripping and holding a workpiece.
  *         It must be provided in 1/10th Newtons.
  *         The valid range is 0 to 400 for the RG2 and 0 to 1200 for the RG6.
 */
typedef struct onrobot_rg_msgs__msg__OnRobotRGOutput
{
  uint16_t r_gfr;
  /// r_gwd : The target width between the finger to be moved to and maintained.
  ///         It must be provided in 1/10th millimeters.
  ///         The valid range is 0 to 1100 for the RG2 and 0 to 1600 for the RG6.
  ///         Please note that the target width should be provided corrected for any fingertip offset,
  ///         as it is measured between the insides of the aluminum fingers.
  uint16_t r_gwd;
  /// r_ctr : The control field is used to start and stop gripper motion.
  ///         Only one option should be set at a time.
  ///         Please note that the gripper will not start a new motion
  ///         before the one currently being executed is done (see busy flag in the Status field).
  /// 0x0001 - grip
  ///           Start the motion, with the preset target force and width.
  ///           Width is calculated without the fingertip offset.
  ///           Please note that the gripper will ignore this command
  ///           if the busy flag is set in the status field.
  /// 0x0008 - stop
  ///           Stop the current motion.
  uint8_t r_ctr;
  /// out_zero : Zero the force and torque values to cancel any offset.
  /// 0x0000 - un-zero: use the unchanged values
  /// 0x0001 - zero: set all values to 0
  uint16_t out_zero;
  uint16_t out_prox_off_r;
  uint16_t out_prox_off_l;
} onrobot_rg_msgs__msg__OnRobotRGOutput;

// Struct for a sequence of onrobot_rg_msgs__msg__OnRobotRGOutput.
typedef struct onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence
{
  onrobot_rg_msgs__msg__OnRobotRGOutput * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__STRUCT_H_
