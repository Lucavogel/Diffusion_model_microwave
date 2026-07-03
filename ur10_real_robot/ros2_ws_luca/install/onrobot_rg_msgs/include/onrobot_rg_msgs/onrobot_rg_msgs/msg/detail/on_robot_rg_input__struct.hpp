// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__STRUCT_HPP_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGInput __attribute__((deprecated))
#else
# define DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGInput __declspec(deprecated)
#endif

namespace onrobot_rg_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct OnRobotRGInput_
{
  using Type = OnRobotRGInput_<ContainerAllocator>;

  explicit OnRobotRGInput_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->g_fof = 0;
      this->g_gwd = 0;
      this->g_sta = 0;
      this->g_wdf = 0;
      this->sta_fing_l = 0;
      this->sta_fing_r = 0;
      this->sta_prox_l = 0;
      this->sta_prox_r = 0;
      this->busy = 0;
      this->grip_det = 0;
      this->prox_off_l = 0;
      this->prox_off_r = 0;
      this->fx_l = 0l;
      this->fy_l = 0l;
      this->fz_l = 0l;
      this->tx_l = 0l;
      this->ty_l = 0l;
      this->tz_l = 0l;
      this->fx_r = 0l;
      this->fy_r = 0l;
      this->fz_r = 0l;
      this->tx_r = 0l;
      this->ty_r = 0l;
      this->tz_r = 0l;
      this->prox_l = 0l;
      this->prox_r = 0l;
      this->grip_width = 0l;
      this->in_zero = 0;
    }
  }

  explicit OnRobotRGInput_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->g_fof = 0;
      this->g_gwd = 0;
      this->g_sta = 0;
      this->g_wdf = 0;
      this->sta_fing_l = 0;
      this->sta_fing_r = 0;
      this->sta_prox_l = 0;
      this->sta_prox_r = 0;
      this->busy = 0;
      this->grip_det = 0;
      this->prox_off_l = 0;
      this->prox_off_r = 0;
      this->fx_l = 0l;
      this->fy_l = 0l;
      this->fz_l = 0l;
      this->tx_l = 0l;
      this->ty_l = 0l;
      this->tz_l = 0l;
      this->fx_r = 0l;
      this->fy_r = 0l;
      this->fz_r = 0l;
      this->tx_r = 0l;
      this->ty_r = 0l;
      this->tz_r = 0l;
      this->prox_l = 0l;
      this->prox_r = 0l;
      this->grip_width = 0l;
      this->in_zero = 0;
    }
  }

  // field types and members
  using _g_fof_type =
    uint16_t;
  _g_fof_type g_fof;
  using _g_gwd_type =
    uint16_t;
  _g_gwd_type g_gwd;
  using _g_sta_type =
    uint16_t;
  _g_sta_type g_sta;
  using _g_wdf_type =
    uint16_t;
  _g_wdf_type g_wdf;
  using _sta_fing_l_type =
    uint16_t;
  _sta_fing_l_type sta_fing_l;
  using _sta_fing_r_type =
    uint16_t;
  _sta_fing_r_type sta_fing_r;
  using _sta_prox_l_type =
    uint16_t;
  _sta_prox_l_type sta_prox_l;
  using _sta_prox_r_type =
    uint16_t;
  _sta_prox_r_type sta_prox_r;
  using _busy_type =
    uint16_t;
  _busy_type busy;
  using _grip_det_type =
    uint16_t;
  _grip_det_type grip_det;
  using _prox_off_l_type =
    uint16_t;
  _prox_off_l_type prox_off_l;
  using _prox_off_r_type =
    uint16_t;
  _prox_off_r_type prox_off_r;
  using _fx_l_type =
    int32_t;
  _fx_l_type fx_l;
  using _fy_l_type =
    int32_t;
  _fy_l_type fy_l;
  using _fz_l_type =
    int32_t;
  _fz_l_type fz_l;
  using _tx_l_type =
    int32_t;
  _tx_l_type tx_l;
  using _ty_l_type =
    int32_t;
  _ty_l_type ty_l;
  using _tz_l_type =
    int32_t;
  _tz_l_type tz_l;
  using _fx_r_type =
    int32_t;
  _fx_r_type fx_r;
  using _fy_r_type =
    int32_t;
  _fy_r_type fy_r;
  using _fz_r_type =
    int32_t;
  _fz_r_type fz_r;
  using _tx_r_type =
    int32_t;
  _tx_r_type tx_r;
  using _ty_r_type =
    int32_t;
  _ty_r_type ty_r;
  using _tz_r_type =
    int32_t;
  _tz_r_type tz_r;
  using _prox_l_type =
    int32_t;
  _prox_l_type prox_l;
  using _prox_r_type =
    int32_t;
  _prox_r_type prox_r;
  using _grip_width_type =
    int32_t;
  _grip_width_type grip_width;
  using _in_zero_type =
    int8_t;
  _in_zero_type in_zero;

  // setters for named parameter idiom
  Type & set__g_fof(
    const uint16_t & _arg)
  {
    this->g_fof = _arg;
    return *this;
  }
  Type & set__g_gwd(
    const uint16_t & _arg)
  {
    this->g_gwd = _arg;
    return *this;
  }
  Type & set__g_sta(
    const uint16_t & _arg)
  {
    this->g_sta = _arg;
    return *this;
  }
  Type & set__g_wdf(
    const uint16_t & _arg)
  {
    this->g_wdf = _arg;
    return *this;
  }
  Type & set__sta_fing_l(
    const uint16_t & _arg)
  {
    this->sta_fing_l = _arg;
    return *this;
  }
  Type & set__sta_fing_r(
    const uint16_t & _arg)
  {
    this->sta_fing_r = _arg;
    return *this;
  }
  Type & set__sta_prox_l(
    const uint16_t & _arg)
  {
    this->sta_prox_l = _arg;
    return *this;
  }
  Type & set__sta_prox_r(
    const uint16_t & _arg)
  {
    this->sta_prox_r = _arg;
    return *this;
  }
  Type & set__busy(
    const uint16_t & _arg)
  {
    this->busy = _arg;
    return *this;
  }
  Type & set__grip_det(
    const uint16_t & _arg)
  {
    this->grip_det = _arg;
    return *this;
  }
  Type & set__prox_off_l(
    const uint16_t & _arg)
  {
    this->prox_off_l = _arg;
    return *this;
  }
  Type & set__prox_off_r(
    const uint16_t & _arg)
  {
    this->prox_off_r = _arg;
    return *this;
  }
  Type & set__fx_l(
    const int32_t & _arg)
  {
    this->fx_l = _arg;
    return *this;
  }
  Type & set__fy_l(
    const int32_t & _arg)
  {
    this->fy_l = _arg;
    return *this;
  }
  Type & set__fz_l(
    const int32_t & _arg)
  {
    this->fz_l = _arg;
    return *this;
  }
  Type & set__tx_l(
    const int32_t & _arg)
  {
    this->tx_l = _arg;
    return *this;
  }
  Type & set__ty_l(
    const int32_t & _arg)
  {
    this->ty_l = _arg;
    return *this;
  }
  Type & set__tz_l(
    const int32_t & _arg)
  {
    this->tz_l = _arg;
    return *this;
  }
  Type & set__fx_r(
    const int32_t & _arg)
  {
    this->fx_r = _arg;
    return *this;
  }
  Type & set__fy_r(
    const int32_t & _arg)
  {
    this->fy_r = _arg;
    return *this;
  }
  Type & set__fz_r(
    const int32_t & _arg)
  {
    this->fz_r = _arg;
    return *this;
  }
  Type & set__tx_r(
    const int32_t & _arg)
  {
    this->tx_r = _arg;
    return *this;
  }
  Type & set__ty_r(
    const int32_t & _arg)
  {
    this->ty_r = _arg;
    return *this;
  }
  Type & set__tz_r(
    const int32_t & _arg)
  {
    this->tz_r = _arg;
    return *this;
  }
  Type & set__prox_l(
    const int32_t & _arg)
  {
    this->prox_l = _arg;
    return *this;
  }
  Type & set__prox_r(
    const int32_t & _arg)
  {
    this->prox_r = _arg;
    return *this;
  }
  Type & set__grip_width(
    const int32_t & _arg)
  {
    this->grip_width = _arg;
    return *this;
  }
  Type & set__in_zero(
    const int8_t & _arg)
  {
    this->in_zero = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator> *;
  using ConstRawPtr =
    const onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGInput
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGInput
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGInput_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const OnRobotRGInput_ & other) const
  {
    if (this->g_fof != other.g_fof) {
      return false;
    }
    if (this->g_gwd != other.g_gwd) {
      return false;
    }
    if (this->g_sta != other.g_sta) {
      return false;
    }
    if (this->g_wdf != other.g_wdf) {
      return false;
    }
    if (this->sta_fing_l != other.sta_fing_l) {
      return false;
    }
    if (this->sta_fing_r != other.sta_fing_r) {
      return false;
    }
    if (this->sta_prox_l != other.sta_prox_l) {
      return false;
    }
    if (this->sta_prox_r != other.sta_prox_r) {
      return false;
    }
    if (this->busy != other.busy) {
      return false;
    }
    if (this->grip_det != other.grip_det) {
      return false;
    }
    if (this->prox_off_l != other.prox_off_l) {
      return false;
    }
    if (this->prox_off_r != other.prox_off_r) {
      return false;
    }
    if (this->fx_l != other.fx_l) {
      return false;
    }
    if (this->fy_l != other.fy_l) {
      return false;
    }
    if (this->fz_l != other.fz_l) {
      return false;
    }
    if (this->tx_l != other.tx_l) {
      return false;
    }
    if (this->ty_l != other.ty_l) {
      return false;
    }
    if (this->tz_l != other.tz_l) {
      return false;
    }
    if (this->fx_r != other.fx_r) {
      return false;
    }
    if (this->fy_r != other.fy_r) {
      return false;
    }
    if (this->fz_r != other.fz_r) {
      return false;
    }
    if (this->tx_r != other.tx_r) {
      return false;
    }
    if (this->ty_r != other.ty_r) {
      return false;
    }
    if (this->tz_r != other.tz_r) {
      return false;
    }
    if (this->prox_l != other.prox_l) {
      return false;
    }
    if (this->prox_r != other.prox_r) {
      return false;
    }
    if (this->grip_width != other.grip_width) {
      return false;
    }
    if (this->in_zero != other.in_zero) {
      return false;
    }
    return true;
  }
  bool operator!=(const OnRobotRGInput_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct OnRobotRGInput_

// alias to use template instance with default allocator
using OnRobotRGInput =
  onrobot_rg_msgs::msg::OnRobotRGInput_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace onrobot_rg_msgs

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__STRUCT_HPP_
