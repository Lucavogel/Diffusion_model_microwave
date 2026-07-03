// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from onrobot_rg_msgs:msg/OnRobotRGInput.idl
// generated code does not contain a copyright notice

#ifndef ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__BUILDER_HPP_
#define ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "onrobot_rg_msgs/msg/detail/on_robot_rg_input__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace onrobot_rg_msgs
{

namespace msg
{

namespace builder
{

class Init_OnRobotRGInput_in_zero
{
public:
  explicit Init_OnRobotRGInput_in_zero(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  ::onrobot_rg_msgs::msg::OnRobotRGInput in_zero(::onrobot_rg_msgs::msg::OnRobotRGInput::_in_zero_type arg)
  {
    msg_.in_zero = std::move(arg);
    return std::move(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_grip_width
{
public:
  explicit Init_OnRobotRGInput_grip_width(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_in_zero grip_width(::onrobot_rg_msgs::msg::OnRobotRGInput::_grip_width_type arg)
  {
    msg_.grip_width = std::move(arg);
    return Init_OnRobotRGInput_in_zero(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_prox_r
{
public:
  explicit Init_OnRobotRGInput_prox_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_grip_width prox_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_prox_r_type arg)
  {
    msg_.prox_r = std::move(arg);
    return Init_OnRobotRGInput_grip_width(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_prox_l
{
public:
  explicit Init_OnRobotRGInput_prox_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_prox_r prox_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_prox_l_type arg)
  {
    msg_.prox_l = std::move(arg);
    return Init_OnRobotRGInput_prox_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_tz_r
{
public:
  explicit Init_OnRobotRGInput_tz_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_prox_l tz_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_tz_r_type arg)
  {
    msg_.tz_r = std::move(arg);
    return Init_OnRobotRGInput_prox_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_ty_r
{
public:
  explicit Init_OnRobotRGInput_ty_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_tz_r ty_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_ty_r_type arg)
  {
    msg_.ty_r = std::move(arg);
    return Init_OnRobotRGInput_tz_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_tx_r
{
public:
  explicit Init_OnRobotRGInput_tx_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_ty_r tx_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_tx_r_type arg)
  {
    msg_.tx_r = std::move(arg);
    return Init_OnRobotRGInput_ty_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_fz_r
{
public:
  explicit Init_OnRobotRGInput_fz_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_tx_r fz_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_fz_r_type arg)
  {
    msg_.fz_r = std::move(arg);
    return Init_OnRobotRGInput_tx_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_fy_r
{
public:
  explicit Init_OnRobotRGInput_fy_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_fz_r fy_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_fy_r_type arg)
  {
    msg_.fy_r = std::move(arg);
    return Init_OnRobotRGInput_fz_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_fx_r
{
public:
  explicit Init_OnRobotRGInput_fx_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_fy_r fx_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_fx_r_type arg)
  {
    msg_.fx_r = std::move(arg);
    return Init_OnRobotRGInput_fy_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_tz_l
{
public:
  explicit Init_OnRobotRGInput_tz_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_fx_r tz_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_tz_l_type arg)
  {
    msg_.tz_l = std::move(arg);
    return Init_OnRobotRGInput_fx_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_ty_l
{
public:
  explicit Init_OnRobotRGInput_ty_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_tz_l ty_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_ty_l_type arg)
  {
    msg_.ty_l = std::move(arg);
    return Init_OnRobotRGInput_tz_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_tx_l
{
public:
  explicit Init_OnRobotRGInput_tx_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_ty_l tx_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_tx_l_type arg)
  {
    msg_.tx_l = std::move(arg);
    return Init_OnRobotRGInput_ty_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_fz_l
{
public:
  explicit Init_OnRobotRGInput_fz_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_tx_l fz_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_fz_l_type arg)
  {
    msg_.fz_l = std::move(arg);
    return Init_OnRobotRGInput_tx_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_fy_l
{
public:
  explicit Init_OnRobotRGInput_fy_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_fz_l fy_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_fy_l_type arg)
  {
    msg_.fy_l = std::move(arg);
    return Init_OnRobotRGInput_fz_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_fx_l
{
public:
  explicit Init_OnRobotRGInput_fx_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_fy_l fx_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_fx_l_type arg)
  {
    msg_.fx_l = std::move(arg);
    return Init_OnRobotRGInput_fy_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_prox_off_r
{
public:
  explicit Init_OnRobotRGInput_prox_off_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_fx_l prox_off_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_prox_off_r_type arg)
  {
    msg_.prox_off_r = std::move(arg);
    return Init_OnRobotRGInput_fx_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_prox_off_l
{
public:
  explicit Init_OnRobotRGInput_prox_off_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_prox_off_r prox_off_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_prox_off_l_type arg)
  {
    msg_.prox_off_l = std::move(arg);
    return Init_OnRobotRGInput_prox_off_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_grip_det
{
public:
  explicit Init_OnRobotRGInput_grip_det(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_prox_off_l grip_det(::onrobot_rg_msgs::msg::OnRobotRGInput::_grip_det_type arg)
  {
    msg_.grip_det = std::move(arg);
    return Init_OnRobotRGInput_prox_off_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_busy
{
public:
  explicit Init_OnRobotRGInput_busy(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_grip_det busy(::onrobot_rg_msgs::msg::OnRobotRGInput::_busy_type arg)
  {
    msg_.busy = std::move(arg);
    return Init_OnRobotRGInput_grip_det(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_sta_prox_r
{
public:
  explicit Init_OnRobotRGInput_sta_prox_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_busy sta_prox_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_sta_prox_r_type arg)
  {
    msg_.sta_prox_r = std::move(arg);
    return Init_OnRobotRGInput_busy(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_sta_prox_l
{
public:
  explicit Init_OnRobotRGInput_sta_prox_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_sta_prox_r sta_prox_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_sta_prox_l_type arg)
  {
    msg_.sta_prox_l = std::move(arg);
    return Init_OnRobotRGInput_sta_prox_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_sta_fing_r
{
public:
  explicit Init_OnRobotRGInput_sta_fing_r(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_sta_prox_l sta_fing_r(::onrobot_rg_msgs::msg::OnRobotRGInput::_sta_fing_r_type arg)
  {
    msg_.sta_fing_r = std::move(arg);
    return Init_OnRobotRGInput_sta_prox_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_sta_fing_l
{
public:
  explicit Init_OnRobotRGInput_sta_fing_l(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_sta_fing_r sta_fing_l(::onrobot_rg_msgs::msg::OnRobotRGInput::_sta_fing_l_type arg)
  {
    msg_.sta_fing_l = std::move(arg);
    return Init_OnRobotRGInput_sta_fing_r(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_g_wdf
{
public:
  explicit Init_OnRobotRGInput_g_wdf(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_sta_fing_l g_wdf(::onrobot_rg_msgs::msg::OnRobotRGInput::_g_wdf_type arg)
  {
    msg_.g_wdf = std::move(arg);
    return Init_OnRobotRGInput_sta_fing_l(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_g_sta
{
public:
  explicit Init_OnRobotRGInput_g_sta(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_g_wdf g_sta(::onrobot_rg_msgs::msg::OnRobotRGInput::_g_sta_type arg)
  {
    msg_.g_sta = std::move(arg);
    return Init_OnRobotRGInput_g_wdf(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_g_gwd
{
public:
  explicit Init_OnRobotRGInput_g_gwd(::onrobot_rg_msgs::msg::OnRobotRGInput & msg)
  : msg_(msg)
  {}
  Init_OnRobotRGInput_g_sta g_gwd(::onrobot_rg_msgs::msg::OnRobotRGInput::_g_gwd_type arg)
  {
    msg_.g_gwd = std::move(arg);
    return Init_OnRobotRGInput_g_sta(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

class Init_OnRobotRGInput_g_fof
{
public:
  Init_OnRobotRGInput_g_fof()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_OnRobotRGInput_g_gwd g_fof(::onrobot_rg_msgs::msg::OnRobotRGInput::_g_fof_type arg)
  {
    msg_.g_fof = std::move(arg);
    return Init_OnRobotRGInput_g_gwd(msg_);
  }

private:
  ::onrobot_rg_msgs::msg::OnRobotRGInput msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::onrobot_rg_msgs::msg::OnRobotRGInput>()
{
  return onrobot_rg_msgs::msg::builder::Init_OnRobotRGInput_g_fof();
}

}  // namespace onrobot_rg_msgs

#endif  // ONROBOT_RG_MSGS__MSG__DETAIL__ON_ROBOT_RG_INPUT__BUILDER_HPP_
