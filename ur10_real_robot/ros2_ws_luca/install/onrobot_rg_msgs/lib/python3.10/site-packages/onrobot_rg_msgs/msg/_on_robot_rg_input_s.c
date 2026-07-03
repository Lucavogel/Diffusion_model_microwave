// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__struct.h"
#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__functions.h"


ROSIDL_GENERATOR_C_EXPORT
bool onrobot_rg_msgs__msg__on_robot_rg_input__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[54];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("onrobot_rg_msgs.msg._on_robot_rg_input.OnRobotRGInput", full_classname_dest, 53) == 0);
  }
  onrobot_rg_msgs__msg__OnRobotRGInput * ros_message = _ros_message;
  {  // g_fof
    PyObject * field = PyObject_GetAttrString(_pymsg, "g_fof");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->g_fof = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // g_gwd
    PyObject * field = PyObject_GetAttrString(_pymsg, "g_gwd");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->g_gwd = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // g_sta
    PyObject * field = PyObject_GetAttrString(_pymsg, "g_sta");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->g_sta = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // g_wdf
    PyObject * field = PyObject_GetAttrString(_pymsg, "g_wdf");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->g_wdf = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // sta_fing_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "sta_fing_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->sta_fing_l = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // sta_fing_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "sta_fing_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->sta_fing_r = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // sta_prox_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "sta_prox_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->sta_prox_l = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // sta_prox_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "sta_prox_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->sta_prox_r = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // busy
    PyObject * field = PyObject_GetAttrString(_pymsg, "busy");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->busy = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // grip_det
    PyObject * field = PyObject_GetAttrString(_pymsg, "grip_det");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->grip_det = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // prox_off_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "prox_off_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->prox_off_l = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // prox_off_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "prox_off_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->prox_off_r = (uint16_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // fx_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "fx_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->fx_l = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // fy_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "fy_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->fy_l = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // fz_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "fz_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->fz_l = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // tx_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "tx_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->tx_l = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // ty_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "ty_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->ty_l = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // tz_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "tz_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->tz_l = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // fx_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "fx_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->fx_r = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // fy_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "fy_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->fy_r = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // fz_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "fz_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->fz_r = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // tx_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "tx_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->tx_r = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // ty_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "ty_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->ty_r = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // tz_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "tz_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->tz_r = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // prox_l
    PyObject * field = PyObject_GetAttrString(_pymsg, "prox_l");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->prox_l = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // prox_r
    PyObject * field = PyObject_GetAttrString(_pymsg, "prox_r");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->prox_r = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // grip_width
    PyObject * field = PyObject_GetAttrString(_pymsg, "grip_width");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->grip_width = (int32_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }
  {  // in_zero
    PyObject * field = PyObject_GetAttrString(_pymsg, "in_zero");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->in_zero = (int8_t)PyLong_AsLong(field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * onrobot_rg_msgs__msg__on_robot_rg_input__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of OnRobotRGInput */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("onrobot_rg_msgs.msg._on_robot_rg_input");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "OnRobotRGInput");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  onrobot_rg_msgs__msg__OnRobotRGInput * ros_message = (onrobot_rg_msgs__msg__OnRobotRGInput *)raw_ros_message;
  {  // g_fof
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->g_fof);
    {
      int rc = PyObject_SetAttrString(_pymessage, "g_fof", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // g_gwd
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->g_gwd);
    {
      int rc = PyObject_SetAttrString(_pymessage, "g_gwd", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // g_sta
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->g_sta);
    {
      int rc = PyObject_SetAttrString(_pymessage, "g_sta", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // g_wdf
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->g_wdf);
    {
      int rc = PyObject_SetAttrString(_pymessage, "g_wdf", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // sta_fing_l
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->sta_fing_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "sta_fing_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // sta_fing_r
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->sta_fing_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "sta_fing_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // sta_prox_l
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->sta_prox_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "sta_prox_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // sta_prox_r
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->sta_prox_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "sta_prox_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // busy
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->busy);
    {
      int rc = PyObject_SetAttrString(_pymessage, "busy", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // grip_det
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->grip_det);
    {
      int rc = PyObject_SetAttrString(_pymessage, "grip_det", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // prox_off_l
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->prox_off_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "prox_off_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // prox_off_r
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->prox_off_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "prox_off_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // fx_l
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->fx_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "fx_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // fy_l
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->fy_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "fy_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // fz_l
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->fz_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "fz_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // tx_l
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->tx_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "tx_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // ty_l
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->ty_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "ty_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // tz_l
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->tz_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "tz_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // fx_r
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->fx_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "fx_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // fy_r
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->fy_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "fy_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // fz_r
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->fz_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "fz_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // tx_r
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->tx_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "tx_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // ty_r
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->ty_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "ty_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // tz_r
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->tz_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "tz_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // prox_l
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->prox_l);
    {
      int rc = PyObject_SetAttrString(_pymessage, "prox_l", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // prox_r
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->prox_r);
    {
      int rc = PyObject_SetAttrString(_pymessage, "prox_r", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // grip_width
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->grip_width);
    {
      int rc = PyObject_SetAttrString(_pymessage, "grip_width", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // in_zero
    PyObject * field = NULL;
    field = PyLong_FromLong(ros_message->in_zero);
    {
      int rc = PyObject_SetAttrString(_pymessage, "in_zero", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
