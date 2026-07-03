// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGOutput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__BUILDER_HPP_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "onrobot_rg_msgs/msg/detail/on_robot_rg_output__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace onrobot_rg_msgs
{

namespace msg
{

namespace builder
{

class Init_OnRobotRGOutput_out_prox_off_l
{
public:
  explicit Init_OnRobotRGOutput_out_prox_off_l(::onrobot_rg_msgs::msg::OnRobotRGOutput & msg)
  : msg_(msg)
  {}
  ::onrobot_rg_msgs::msg::OnRobotRGOutput out_prox_off_l(::onrobot_rg_msgs::msg::OnRobotRGOutput::_out_prox_off_l_type arg)
  {
    msg_.out_prox_off_l = std::move(arg);
    return std::move(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGOutput msg_;
};

class Init_OnRobotRGOutput_out_prox_off_r
{
public:
  explicit Init_OnRobotRGOutput_out_prox_off_r(::onrobot_rg_msgs::msg::OnRobotRGOutput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGOutput_out_prox_off_l out_prox_off_r(::onrobot_rg_msgs::msg::OnRobotRGOutput::_out_prox_off_r_type arg)
  {
    msg_.out_prox_off_r = std::move(arg);
    return Init_OnRobotRGOutput_out_prox_off_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGOutput msg_;
};

class Init_OnRobotRGOutput_out_zero
{
public:
  explicit Init_OnRobotRGOutput_out_zero(::onrobot_rg_msgs::msg::OnRobotRGOutput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGOutput_out_prox_off_r out_zero(::onrobot_rg_msgs::msg::OnRobotRGOutput::_out_zero_type arg)
  {
    msg_.out_zero = std::move(arg);
    return Init_OnRobotRGOutput_out_prox_off_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGOutput msg_;
};

class Init_OnRobotRGOutput_r_ctr
{
public:
  explicit Init_OnRobotRGOutput_r_ctr(::onrobot_rg_msgs::msg::OnRobotRGOutput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGOutput_out_zero r_ctr(::onrobot_rg_msgs::msg::OnRobotRGOutput::_r_ctr_type arg)
  {
    msg_.r_ctr = std::move(arg);
    return Init_OnRobotRGOutput_out_zero(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGOutput msg_;
};

class Init_OnRobotRGOutput_r_gwd
{
public:
  explicit Init_OnRobotRGOutput_r_gwd(::onrobot_rg_msgs::msg::OnRobotRGOutput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGOutput_r_ctr r_gwd(::onrobot_rg_msgs::msg::OnRobotRGOutput::_r_gwd_type arg)
  {
    msg_.r_gwd = std::move(arg);
    return Init_OnRobotRGOutput_r_ctr(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGOutput msg_;
};

class Init_OnRobotRGOutput_r_gfr
{
public:
  Init_OnRobotRGOutput_r_gfr()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_OnRobotRGOutput_r_gwd r_gfr(::onrobot_rg_msgs::msg::OnRobotRGOutput::_r_gfr_type arg)
  {
    msg_.r_gfr = std::move(arg);
    return Init_OnRobotRGOutput_r_gwd(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGOutput msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::onrobot_rg_msgs::msg::OnRobotRGOutput>()
{
  return onrobot_rg_msgs::msg::builder::Init_OnRobotRGOutput_r_gfr();
}

}  // namespace onrobot_rg_msgs

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_OUTPUT__BUILDER_HPP_
