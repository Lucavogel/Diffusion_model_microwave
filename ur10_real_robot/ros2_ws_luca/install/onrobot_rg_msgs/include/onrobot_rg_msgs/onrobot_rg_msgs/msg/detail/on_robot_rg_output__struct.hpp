// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__STRUCT_HPP_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGOutput __attribute__((deprecated))
#else
# define DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGOutput __declspec(deprecated)
#endif

namespace onrobot_rg_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct OnRobotRGOutput_
{
  using Type = OnRobotRGOutput_<ContainerAllocator>;

  explicit OnRobotRGOutput_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->r_gfr = 0;
      this->r_gwd = 0;
      this->r_ctr = 0;
      this->out_zero = 0;
      this->out_prox_off_r = 0;
      this->out_prox_off_l = 0;
    }
  }

  explicit OnRobotRGOutput_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->r_gfr = 0;
      this->r_gwd = 0;
      this->r_ctr = 0;
      this->out_zero = 0;
      this->out_prox_off_r = 0;
      this->out_prox_off_l = 0;
    }
  }

  // field types and members
  using _r_gfr_type =
    uint16_t;
  _r_gfr_type r_gfr;
  using _r_gwd_type =
    uint16_t;
  _r_gwd_type r_gwd;
  using _r_ctr_type =
    uint8_t;
  _r_ctr_type r_ctr;
  using _out_zero_type =
    uint16_t;
  _out_zero_type out_zero;
  using _out_prox_off_r_type =
    uint16_t;
  _out_prox_off_r_type out_prox_off_r;
  using _out_prox_off_l_type =
    uint16_t;
  _out_prox_off_l_type out_prox_off_l;

  // setters for named parameter idiom
  Type & set__r_gfr(
    const uint16_t & _arg)
  {
    this->r_gfr = _arg;
    return *this;
  }
  Type & set__r_gwd(
    const uint16_t & _arg)
  {
    this->r_gwd = _arg;
    return *this;
  }
  Type & set__r_ctr(
    const uint8_t & _arg)
  {
    this->r_ctr = _arg;
    return *this;
  }
  Type & set__out_zero(
    const uint16_t & _arg)
  {
    this->out_zero = _arg;
    return *this;
  }
  Type & set__out_prox_off_r(
    const uint16_t & _arg)
  {
    this->out_prox_off_r = _arg;
    return *this;
  }
  Type & set__out_prox_off_l(
    const uint16_t & _arg)
  {
    this->out_prox_off_l = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator> *;
  using ConstRawPtr =
    const onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGOutput
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__onrobot_rg_msgs__msg__OnRobotRGOutput
    std::shared_ptr<onrobot_rg_msgs::msg::OnRobotRGOutput_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const OnRobotRGOutput_ & other) const
  {
    if (this->r_gfr != other.r_gfr) {
      return false;
    }
    if (this->r_gwd != other.r_gwd) {
      return false;
    }
    if (this->r_ctr != other.r_ctr) {
      return false;
    }
    if (this->out_zero != other.out_zero) {
      return false;
    }
    if (this->out_prox_off_r != other.out_prox_off_r) {
      return false;
    }
    if (this->out_prox_off_l != other.out_prox_off_l) {
      return false;
    }
    return true;
  }
  bool operator!=(const OnRobotRGOutput_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct OnRobotRGOutput_

// alias to use template instance with default allocator
using OnRobotRGOutput =
  onrobot_rg_msgs::msg::OnRobotRGOutput_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace onrobot_rg_msgs

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__STRUCT_HPP_
