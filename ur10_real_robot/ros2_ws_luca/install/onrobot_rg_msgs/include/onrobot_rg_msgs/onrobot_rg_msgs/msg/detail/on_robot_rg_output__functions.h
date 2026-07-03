// generated from rosidl_generator_c/resource/idl__functions.h.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__FUNCTIONS_H_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__FUNCTIONS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stdlib.h>

#include "rosidl_runtime_c/visibility_control.h"
#include "onrobot_rg_msgs/msg/rosidl_generator_c__visibility_control.h"

#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__struct.h"

/// Initialize msg/OnRobotRGOutput message.
/**
 * If the init function is called twice for the same message without
 * calling fini inbetween previously allocated memory will be leaked.
 * \param[in,out] msg The previously allocated message pointer.
 * Fields without a default value will not be initialized by this function.
 * You might want to call memset(msg, 0, sizeof(
 * onrobot_rg_msgs__msg__OnRobotRGOutput
 * )) before or use
 * onrobot_rg_msgs__msg__OnRobotRGOutput__create()
 * to allocate and initialize the message.
 * \return true if initialization was successful, otherwise false
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
bool
onrobot_rg_msgs__msg__OnRobotRGOutput__init(onrobot_rg_msgs__msg__OnRobotRGOutput * msg);

/// Finalize msg/OnRobotRGOutput message.
/**
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
void
onrobot_rg_msgs__msg__OnRobotRGOutput__fini(onrobot_rg_msgs__msg__OnRobotRGOutput * msg);

/// Create msg/OnRobotRGOutput message.
/**
 * It allocates the memory for the message, sets the memory to zero, and
 * calls
 * onrobot_rg_msgs__msg__OnRobotRGOutput__init().
 * \return The pointer to the initialized message if successful,
 * otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
onrobot_rg_msgs__msg__OnRobotRGOutput *
onrobot_rg_msgs__msg__OnRobotRGOutput__create();

/// Destroy msg/OnRobotRGOutput message.
/**
 * It calls
 * onrobot_rg_msgs__msg__OnRobotRGOutput__fini()
 * and frees the memory of the message.
 * \param[in,out] msg The allocated message pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
void
onrobot_rg_msgs__msg__OnRobotRGOutput__destroy(onrobot_rg_msgs__msg__OnRobotRGOutput * msg);

/// Check for msg/OnRobotRGOutput message equality.
/**
 * \param[in] lhs The message on the left hand size of the equality operator.
 * \param[in] rhs The message on the right hand size of the equality operator.
 * \return true if messages are equal, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
bool
onrobot_rg_msgs__msg__OnRobotRGOutput__are_equal(const onrobot_rg_msgs__msg__OnRobotRGOutput * lhs, const onrobot_rg_msgs__msg__OnRobotRGOutput * rhs);

/// Copy a msg/OnRobotRGOutput message.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source message pointer.
 * \param[out] output The target message pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer is null
 *   or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
bool
onrobot_rg_msgs__msg__OnRobotRGOutput__copy(
  const onrobot_rg_msgs__msg__OnRobotRGOutput * input,
  onrobot_rg_msgs__msg__OnRobotRGOutput * output);

/// Initialize array of msg/OnRobotRGOutput messages.
/**
 * It allocates the memory for the number of elements and calls
 * onrobot_rg_msgs__msg__OnRobotRGOutput__init()
 * for each element of the array.
 * \param[in,out] array The allocated array pointer.
 * \param[in] size The size / capacity of the array.
 * \return true if initialization was successful, otherwise false
 * If the array pointer is valid and the size is zero it is guaranteed
 # to return true.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
bool
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__init(onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * array, size_t size);

/// Finalize array of msg/OnRobotRGOutput messages.
/**
 * It calls
 * onrobot_rg_msgs__msg__OnRobotRGOutput__fini()
 * for each element of the array and frees the memory for the number of
 * elements.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
void
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__fini(onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * array);

/// Create array of msg/OnRobotRGOutput messages.
/**
 * It allocates the memory for the array and calls
 * onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__init().
 * \param[in] size The size / capacity of the array.
 * \return The pointer to the initialized array if successful, otherwise NULL
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence *
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__create(size_t size);

/// Destroy array of msg/OnRobotRGOutput messages.
/**
 * It calls
 * onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__fini()
 * on the array,
 * and frees the memory of the array.
 * \param[in,out] array The initialized array pointer.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
void
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__destroy(onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * array);

/// Check for msg/OnRobotRGOutput message array equality.
/**
 * \param[in] lhs The message array on the left hand size of the equality operator.
 * \param[in] rhs The message array on the right hand size of the equality operator.
 * \return true if message arrays are equal in size and content, otherwise false.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
bool
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__are_equal(const onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * lhs, const onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * rhs);

/// Copy an array of msg/OnRobotRGOutput messages.
/**
 * This functions performs a deep copy, as opposed to the shallow copy that
 * plain assignment yields.
 *
 * \param[in] input The source array pointer.
 * \param[out] output The target array pointer, which must
 *   have been initialized before calling this function.
 * \return true if successful, or false if either pointer
 *   is null or memory allocation fails.
 */
ROSIDL_GENERATOR_C_PUBLIC_onrobot_rg_msgs
bool
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__copy(
  const onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * input,
  onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * output);

#ifdef __cplusplus
}
#endif

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__FUNCTIONS_H_
