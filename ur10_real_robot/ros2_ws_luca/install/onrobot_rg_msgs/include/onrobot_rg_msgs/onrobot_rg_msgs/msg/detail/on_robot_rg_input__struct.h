// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__STRUCT_H_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in msg/OnRobotRGInput in the package onrobot_rg_msgs.
/**
  * gFOF : Current fingertip offset in 1/10 millimeters. The value is a signed two's complement number.
 */
typedef struct onrobot_rg_msgs__msg__OnRobotRGInput
{
  uint16_t g_fof;
  /// gGWD : Current width between the gripper fingers in 1/10 millimeters.
  ///        The width is provided without any fingertip offset, as it is measured between the insides of the aluminum fingers.
  uint16_t g_gwd;
  /// gSTA : Current device status, which indicates the status of the gripper and its motion.
  /// Bit       - Name              - Description
  /// 0 (LSB)   - Busy              - High (1) when a motion is ongoing, low (0) when not. The gripper will only accept new commands when this flag is low.
  /// 1         - Grip detected     - High (1) when an internal- or external grip is detected.
  /// 2         - S1 pushed         - High (1) when safety switch 1 is pushed.
  /// 3         - S1 trigged        - High (1) when safety circuit 1 is activated. The gripper will not move while this flag is high.
  /// 4         - S2 pushed         - High (1) when safety switch 2 is pushed.
  /// 5         - S2 trigged        - High (1) when safety circuit 2 is activated. The gripper will not move while this flag is high.
  /// 6         - Safety error      - High (1) when on power on any of the safety switch is pushed.
  /// 7 - 15    - Reserved          - Not used.
  uint16_t g_sta;
  /// gWDF : Current width between the gripper fingers in 1/10 millimeters.
  ///        The set fingertip offset is considered.
  uint16_t g_wdf;
  /// All 4 status signals
  uint16_t sta_fing_l;
  uint16_t sta_fing_r;
  uint16_t sta_prox_l;
  uint16_t sta_prox_r;
  /// Signal that indicates if th gripper is busy (1) or accepts new commands (0)
  uint16_t busy;
  /// Signal that indicates whether an external or internal grip is detected (1)
  uint16_t grip_det;
  /// Proximity offsets of both fingers in 1/10 millimeters
  uint16_t prox_off_l;
  uint16_t prox_off_r;
  ///  Force values along all 3 axis of the left finger in 1/10 newton.
  /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
  int32_t fx_l;
  int32_t fy_l;
  int32_t fz_l;
  ///  Torque values about all 3 axis of the left finger in 1/100 newton-meter.
  /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
  int32_t tx_l;
  int32_t ty_l;
  int32_t tz_l;
  ///  Force Values along all 3 axis of the right finger in 1/10 newton.
  /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
  int32_t fx_r;
  int32_t fy_r;
  int32_t fz_r;
  ///  Torque values about all 3 axis of the right finger in 1/100 newton-meter.
  /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
  int32_t tx_r;
  int32_t ty_r;
  int32_t tz_r;
  /// Proximity values of both sensors in 1/10mm
  int32_t prox_l;
  int32_t prox_r;
  /// Actual gripper width without any offset in 1/10 millimeters
  int32_t grip_width;
  /// Current state of the Bias, that sets force and torque to zero if set to 1
  int8_t in_zero;
} onrobot_rg_msgs__msg__OnRobotRGInput;

// Struct for a sequence of onrobot_rg_msgs__msg__OnRobotRGInput.
typedef struct onrobot_rg_msgs__msg__OnRobotRGInput__Sequence
{
  onrobot_rg_msgs__msg__OnRobotRGInput * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} onrobot_rg_msgs__msg__OnRobotRGInput__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__STRUCT_H_
