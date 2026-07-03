// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
// generated code does not contain a copyright notice
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


bool
onrobot_rg_msgs__msg__OnRobotRGInput__init(onrobot_rg_msgs__msg__OnRobotRGInput * msg)
{
  if (!msg) {
    return false;
  }
  // g_fof
  // g_gwd
  // g_sta
  // g_wdf
  // sta_fing_l
  // sta_fing_r
  // sta_prox_l
  // sta_prox_r
  // busy
  // grip_det
  // prox_off_l
  // prox_off_r
  // fx_l
  // fy_l
  // fz_l
  // tx_l
  // ty_l
  // tz_l
  // fx_r
  // fy_r
  // fz_r
  // tx_r
  // ty_r
  // tz_r
  // prox_l
  // prox_r
  // grip_width
  // in_zero
  return true;
}

void
onrobot_rg_msgs__msg__OnRobotRGInput__fini(onrobot_rg_msgs__msg__OnRobotRGInput * msg)
{
  if (!msg) {
    return;
  }
  // g_fof
  // g_gwd
  // g_sta
  // g_wdf
  // sta_fing_l
  // sta_fing_r
  // sta_prox_l
  // sta_prox_r
  // busy
  // grip_det
  // prox_off_l
  // prox_off_r
  // fx_l
  // fy_l
  // fz_l
  // tx_l
  // ty_l
  // tz_l
  // fx_r
  // fy_r
  // fz_r
  // tx_r
  // ty_r
  // tz_r
  // prox_l
  // prox_r
  // grip_width
  // in_zero
}

bool
onrobot_rg_msgs__msg__OnRobotRGInput__are_equal(const onrobot_rg_msgs__msg__OnRobotRGInput * lhs, const onrobot_rg_msgs__msg__OnRobotRGInput * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // g_fof
  if (lhs->g_fof != rhs->g_fof) {
    return false;
  }
  // g_gwd
  if (lhs->g_gwd != rhs->g_gwd) {
    return false;
  }
  // g_sta
  if (lhs->g_sta != rhs->g_sta) {
    return false;
  }
  // g_wdf
  if (lhs->g_wdf != rhs->g_wdf) {
    return false;
  }
  // sta_fing_l
  if (lhs->sta_fing_l != rhs->sta_fing_l) {
    return false;
  }
  // sta_fing_r
  if (lhs->sta_fing_r != rhs->sta_fing_r) {
    return false;
  }
  // sta_prox_l
  if (lhs->sta_prox_l != rhs->sta_prox_l) {
    return false;
  }
  // sta_prox_r
  if (lhs->sta_prox_r != rhs->sta_prox_r) {
    return false;
  }
  // busy
  if (lhs->busy != rhs->busy) {
    return false;
  }
  // grip_det
  if (lhs->grip_det != rhs->grip_det) {
    return false;
  }
  // prox_off_l
  if (lhs->prox_off_l != rhs->prox_off_l) {
    return false;
  }
  // prox_off_r
  if (lhs->prox_off_r != rhs->prox_off_r) {
    return false;
  }
  // fx_l
  if (lhs->fx_l != rhs->fx_l) {
    return false;
  }
  // fy_l
  if (lhs->fy_l != rhs->fy_l) {
    return false;
  }
  // fz_l
  if (lhs->fz_l != rhs->fz_l) {
    return false;
  }
  // tx_l
  if (lhs->tx_l != rhs->tx_l) {
    return false;
  }
  // ty_l
  if (lhs->ty_l != rhs->ty_l) {
    return false;
  }
  // tz_l
  if (lhs->tz_l != rhs->tz_l) {
    return false;
  }
  // fx_r
  if (lhs->fx_r != rhs->fx_r) {
    return false;
  }
  // fy_r
  if (lhs->fy_r != rhs->fy_r) {
    return false;
  }
  // fz_r
  if (lhs->fz_r != rhs->fz_r) {
    return false;
  }
  // tx_r
  if (lhs->tx_r != rhs->tx_r) {
    return false;
  }
  // ty_r
  if (lhs->ty_r != rhs->ty_r) {
    return false;
  }
  // tz_r
  if (lhs->tz_r != rhs->tz_r) {
    return false;
  }
  // prox_l
  if (lhs->prox_l != rhs->prox_l) {
    return false;
  }
  // prox_r
  if (lhs->prox_r != rhs->prox_r) {
    return false;
  }
  // grip_width
  if (lhs->grip_width != rhs->grip_width) {
    return false;
  }
  // in_zero
  if (lhs->in_zero != rhs->in_zero) {
    return false;
  }
  return true;
}

bool
onrobot_rg_msgs__msg__OnRobotRGInput__copy(
  const onrobot_rg_msgs__msg__OnRobotRGInput * input,
  onrobot_rg_msgs__msg__OnRobotRGInput * output)
{
  if (!input || !output) {
    return false;
  }
  // g_fof
  output->g_fof = input->g_fof;
  // g_gwd
  output->g_gwd = input->g_gwd;
  // g_sta
  output->g_sta = input->g_sta;
  // g_wdf
  output->g_wdf = input->g_wdf;
  // sta_fing_l
  output->sta_fing_l = input->sta_fing_l;
  // sta_fing_r
  output->sta_fing_r = input->sta_fing_r;
  // sta_prox_l
  output->sta_prox_l = input->sta_prox_l;
  // sta_prox_r
  output->sta_prox_r = input->sta_prox_r;
  // busy
  output->busy = input->busy;
  // grip_det
  output->grip_det = input->grip_det;
  // prox_off_l
  output->prox_off_l = input->prox_off_l;
  // prox_off_r
  output->prox_off_r = input->prox_off_r;
  // fx_l
  output->fx_l = input->fx_l;
  // fy_l
  output->fy_l = input->fy_l;
  // fz_l
  output->fz_l = input->fz_l;
  // tx_l
  output->tx_l = input->tx_l;
  // ty_l
  output->ty_l = input->ty_l;
  // tz_l
  output->tz_l = input->tz_l;
  // fx_r
  output->fx_r = input->fx_r;
  // fy_r
  output->fy_r = input->fy_r;
  // fz_r
  output->fz_r = input->fz_r;
  // tx_r
  output->tx_r = input->tx_r;
  // ty_r
  output->ty_r = input->ty_r;
  // tz_r
  output->tz_r = input->tz_r;
  // prox_l
  output->prox_l = input->prox_l;
  // prox_r
  output->prox_r = input->prox_r;
  // grip_width
  output->grip_width = input->grip_width;
  // in_zero
  output->in_zero = input->in_zero;
  return true;
}

onrobot_rg_msgs__msg__OnRobotRGInput *
onrobot_rg_msgs__msg__OnRobotRGInput__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  onrobot_rg_msgs__msg__OnRobotRGInput * msg = (onrobot_rg_msgs__msg__OnRobotRGInput *)allocator.allocate(sizeof(onrobot_rg_msgs__msg__OnRobotRGInput), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(onrobot_rg_msgs__msg__OnRobotRGInput));
  bool success = onrobot_rg_msgs__msg__OnRobotRGInput__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
onrobot_rg_msgs__msg__OnRobotRGInput__destroy(onrobot_rg_msgs__msg__OnRobotRGInput * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    onrobot_rg_msgs__msg__OnRobotRGInput__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__init(onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  onrobot_rg_msgs__msg__OnRobotRGInput * data = NULL;

  if (size) {
    data = (onrobot_rg_msgs__msg__OnRobotRGInput *)allocator.zero_allocate(size, sizeof(onrobot_rg_msgs__msg__OnRobotRGInput), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = onrobot_rg_msgs__msg__OnRobotRGInput__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        onrobot_rg_msgs__msg__OnRobotRGInput__fini(&data[i - 1]);
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
onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__fini(onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * array)
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
      onrobot_rg_msgs__msg__OnRobotRGInput__fini(&array->data[i]);
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

onrobot_rg_msgs__msg__OnRobotRGInput__Sequence *
onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * array = (onrobot_rg_msgs__msg__OnRobotRGInput__Sequence *)allocator.allocate(sizeof(onrobot_rg_msgs__msg__OnRobotRGInput__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__destroy(onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__are_equal(const onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * lhs, const onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!onrobot_rg_msgs__msg__OnRobotRGInput__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
onrobot_rg_msgs__msg__OnRobotRGInput__Sequence__copy(
  const onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * input,
  onrobot_rg_msgs__msg__OnRobotRGInput__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(onrobot_rg_msgs__msg__OnRobotRGInput);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    onrobot_rg_msgs__msg__OnRobotRGInput * data =
      (onrobot_rg_msgs__msg__OnRobotRGInput *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!onrobot_rg_msgs__msg__OnRobotRGInput__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          onrobot_rg_msgs__msg__OnRobotRGInput__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!onrobot_rg_msgs__msg__OnRobotRGInput__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
