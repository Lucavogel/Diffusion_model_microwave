// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
onrobot_rg_msgs__msg__OnRobotRGOutput__init(onrobot_rg_msgs__msg__OnRobotRGOutput * msg)
{
  if (!msg) {
    return false;
  }
  // r_gfr
  // r_gwd
  // r_ctr
  // out_zero
  // out_prox_off_r
  // out_prox_off_l
  return true;
}

void
onrobot_rg_msgs__msg__OnRobotRGOutput__fini(onrobot_rg_msgs__msg__OnRobotRGOutput * msg)
{
  if (!msg) {
    return;
  }
  // r_gfr
  // r_gwd
  // r_ctr
  // out_zero
  // out_prox_off_r
  // out_prox_off_l
}

bool
onrobot_rg_msgs__msg__OnRobotRGOutput__are_equal(const onrobot_rg_msgs__msg__OnRobotRGOutput * lhs, const onrobot_rg_msgs__msg__OnRobotRGOutput * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // r_gfr
  if (lhs->r_gfr != rhs->r_gfr) {
    return false;
  }
  // r_gwd
  if (lhs->r_gwd != rhs->r_gwd) {
    return false;
  }
  // r_ctr
  if (lhs->r_ctr != rhs->r_ctr) {
    return false;
  }
  // out_zero
  if (lhs->out_zero != rhs->out_zero) {
    return false;
  }
  // out_prox_off_r
  if (lhs->out_prox_off_r != rhs->out_prox_off_r) {
    return false;
  }
  // out_prox_off_l
  if (lhs->out_prox_off_l != rhs->out_prox_off_l) {
    return false;
  }
  return true;
}

bool
onrobot_rg_msgs__msg__OnRobotRGOutput__copy(
  const onrobot_rg_msgs__msg__OnRobotRGOutput * input,
  onrobot_rg_msgs__msg__OnRobotRGOutput * output)
{
  if (!input || !output) {
    return false;
  }
  // r_gfr
  output->r_gfr = input->r_gfr;
  // r_gwd
  output->r_gwd = input->r_gwd;
  // r_ctr
  output->r_ctr = input->r_ctr;
  // out_zero
  output->out_zero = input->out_zero;
  // out_prox_off_r
  output->out_prox_off_r = input->out_prox_off_r;
  // out_prox_off_l
  output->out_prox_off_l = input->out_prox_off_l;
  return true;
}

onrobot_rg_msgs__msg__OnRobotRGOutput *
onrobot_rg_msgs__msg__OnRobotRGOutput__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  onrobot_rg_msgs__msg__OnRobotRGOutput * msg = (onrobot_rg_msgs__msg__OnRobotRGOutput *)allocator.allocate(sizeof(onrobot_rg_msgs__msg__OnRobotRGOutput), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(onrobot_rg_msgs__msg__OnRobotRGOutput));
  bool success = onrobot_rg_msgs__msg__OnRobotRGOutput__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
onrobot_rg_msgs__msg__OnRobotRGOutput__destroy(onrobot_rg_msgs__msg__OnRobotRGOutput * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    onrobot_rg_msgs__msg__OnRobotRGOutput__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__init(onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  onrobot_rg_msgs__msg__OnRobotRGOutput * data = NULL;

  if (size) {
    data = (onrobot_rg_msgs__msg__OnRobotRGOutput *)allocator.zero_allocate(size, sizeof(onrobot_rg_msgs__msg__OnRobotRGOutput), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = onrobot_rg_msgs__msg__OnRobotRGOutput__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        onrobot_rg_msgs__msg__OnRobotRGOutput__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__fini(onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      onrobot_rg_msgs__msg__OnRobotRGOutput__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence *
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * array = (onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence *)allocator.allocate(sizeof(onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__destroy(onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__are_equal(const onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * lhs, const onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!onrobot_rg_msgs__msg__OnRobotRGOutput__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence__copy(
  const onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * input,
  onrobot_rg_msgs__msg__OnRobotRGOutput__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(onrobot_rg_msgs__msg__OnRobotRGOutput);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    onrobot_rg_msgs__msg__OnRobotRGOutput * data =
      (onrobot_rg_msgs__msg__OnRobotRGOutput *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!onrobot_rg_msgs__msg__OnRobotRGOutput__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          onrobot_rg_msgs__msg__OnRobotRGOutput__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!onrobot_rg_msgs__msg__OnRobotRGOutput__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
