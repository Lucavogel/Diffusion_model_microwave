#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to onrobot_rg_msgs__msg__OnRobotRGInput
/// gFOF : Current fingertip offset in 1/10 millimeters. The value is a signed two's complement number.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct OnRobotRGInput {

    // This member is not documented.
    #[allow(missing_docs)]
    pub g_fof: u16,

    /// gGWD : Current width between the gripper fingers in 1/10 millimeters.
    ///        The width is provided without any fingertip offset, as it is measured between the insides of the aluminum fingers.
    pub g_gwd: u16,

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
    pub g_sta: u16,

    /// gWDF : Current width between the gripper fingers in 1/10 millimeters.
    ///        The set fingertip offset is considered.
    pub g_wdf: u16,

    /// All 4 status signals
    pub sta_fing_l: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub sta_fing_r: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub sta_prox_l: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub sta_prox_r: u16,

    /// Signal that indicates if th gripper is busy (1) or accepts new commands (0)
    pub busy: u16,

    /// Signal that indicates whether an external or internal grip is detected (1)
    pub grip_det: u16,

    /// Proximity offsets of both fingers in 1/10 millimeters
    pub prox_off_l: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub prox_off_r: u16,

    ///  Force values along all 3 axis of the left finger in 1/10 newton.
    /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
    pub fx_l: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fy_l: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fz_l: i32,

    ///  Torque values about all 3 axis of the left finger in 1/100 newton-meter.
    /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
    pub tx_l: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ty_l: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub tz_l: i32,

    ///  Force Values along all 3 axis of the right finger in 1/10 newton.
    /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
    pub fx_r: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fy_r: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fz_r: i32,

    ///  Torque values about all 3 axis of the right finger in 1/100 newton-meter.
    /// (According to the manual the value is a signed INT), it seems to be a 2 complement number.
    pub tx_r: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub ty_r: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub tz_r: i32,

    /// Proximity values of both sensors in 1/10mm
    pub prox_l: i32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub prox_r: i32,

    /// Actual gripper width without any offset in 1/10 millimeters
    pub grip_width: i32,

    /// Current state of the Bias, that sets force and torque to zero if set to 1
    pub in_zero: i8,

}



impl Default for OnRobotRGInput {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::OnRobotRGInput::default())
  }
}

impl rosidl_runtime_rs::Message for OnRobotRGInput {
  type RmwMsg = super::msg::rmw::OnRobotRGInput;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        g_fof: msg.g_fof,
        g_gwd: msg.g_gwd,
        g_sta: msg.g_sta,
        g_wdf: msg.g_wdf,
        sta_fing_l: msg.sta_fing_l,
        sta_fing_r: msg.sta_fing_r,
        sta_prox_l: msg.sta_prox_l,
        sta_prox_r: msg.sta_prox_r,
        busy: msg.busy,
        grip_det: msg.grip_det,
        prox_off_l: msg.prox_off_l,
        prox_off_r: msg.prox_off_r,
        fx_l: msg.fx_l,
        fy_l: msg.fy_l,
        fz_l: msg.fz_l,
        tx_l: msg.tx_l,
        ty_l: msg.ty_l,
        tz_l: msg.tz_l,
        fx_r: msg.fx_r,
        fy_r: msg.fy_r,
        fz_r: msg.fz_r,
        tx_r: msg.tx_r,
        ty_r: msg.ty_r,
        tz_r: msg.tz_r,
        prox_l: msg.prox_l,
        prox_r: msg.prox_r,
        grip_width: msg.grip_width,
        in_zero: msg.in_zero,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      g_fof: msg.g_fof,
      g_gwd: msg.g_gwd,
      g_sta: msg.g_sta,
      g_wdf: msg.g_wdf,
      sta_fing_l: msg.sta_fing_l,
      sta_fing_r: msg.sta_fing_r,
      sta_prox_l: msg.sta_prox_l,
      sta_prox_r: msg.sta_prox_r,
      busy: msg.busy,
      grip_det: msg.grip_det,
      prox_off_l: msg.prox_off_l,
      prox_off_r: msg.prox_off_r,
      fx_l: msg.fx_l,
      fy_l: msg.fy_l,
      fz_l: msg.fz_l,
      tx_l: msg.tx_l,
      ty_l: msg.ty_l,
      tz_l: msg.tz_l,
      fx_r: msg.fx_r,
      fy_r: msg.fy_r,
      fz_r: msg.fz_r,
      tx_r: msg.tx_r,
      ty_r: msg.ty_r,
      tz_r: msg.tz_r,
      prox_l: msg.prox_l,
      prox_r: msg.prox_r,
      grip_width: msg.grip_width,
      in_zero: msg.in_zero,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      g_fof: msg.g_fof,
      g_gwd: msg.g_gwd,
      g_sta: msg.g_sta,
      g_wdf: msg.g_wdf,
      sta_fing_l: msg.sta_fing_l,
      sta_fing_r: msg.sta_fing_r,
      sta_prox_l: msg.sta_prox_l,
      sta_prox_r: msg.sta_prox_r,
      busy: msg.busy,
      grip_det: msg.grip_det,
      prox_off_l: msg.prox_off_l,
      prox_off_r: msg.prox_off_r,
      fx_l: msg.fx_l,
      fy_l: msg.fy_l,
      fz_l: msg.fz_l,
      tx_l: msg.tx_l,
      ty_l: msg.ty_l,
      tz_l: msg.tz_l,
      fx_r: msg.fx_r,
      fy_r: msg.fy_r,
      fz_r: msg.fz_r,
      tx_r: msg.tx_r,
      ty_r: msg.ty_r,
      tz_r: msg.tz_r,
      prox_l: msg.prox_l,
      prox_r: msg.prox_r,
      grip_width: msg.grip_width,
      in_zero: msg.in_zero,
    }
  }
}


// Corresponds to onrobot_rg_msgs__msg__OnRobotRGOutput
/// r_gfr : The target force to be reached when gripping and holding a workpiece.
///         It must be provided in 1/10th Newtons.
///         The valid range is 0 to 400 for the RG2 and 0 to 1200 for the RG6.

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct OnRobotRGOutput {

    // This member is not documented.
    #[allow(missing_docs)]
    pub r_gfr: u16,

    /// r_gwd : The target width between the finger to be moved to and maintained.
    ///         It must be provided in 1/10th millimeters.
    ///         The valid range is 0 to 1100 for the RG2 and 0 to 1600 for the RG6.
    ///         Please note that the target width should be provided corrected for any fingertip offset,
    ///         as it is measured between the insides of the aluminum fingers.
    pub r_gwd: u16,

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
    pub r_ctr: u8,

    /// out_zero : Zero the force and torque values to cancel any offset.
    /// 0x0000 - un-zero: use the unchanged values
    /// 0x0001 - zero: set all values to 0
    pub out_zero: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub out_prox_off_r: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub out_prox_off_l: u16,

}



impl Default for OnRobotRGOutput {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::OnRobotRGOutput::default())
  }
}

impl rosidl_runtime_rs::Message for OnRobotRGOutput {
  type RmwMsg = super::msg::rmw::OnRobotRGOutput;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        r_gfr: msg.r_gfr,
        r_gwd: msg.r_gwd,
        r_ctr: msg.r_ctr,
        out_zero: msg.out_zero,
        out_prox_off_r: msg.out_prox_off_r,
        out_prox_off_l: msg.out_prox_off_l,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      r_gfr: msg.r_gfr,
      r_gwd: msg.r_gwd,
      r_ctr: msg.r_ctr,
      out_zero: msg.out_zero,
      out_prox_off_r: msg.out_prox_off_r,
      out_prox_off_l: msg.out_prox_off_l,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      r_gfr: msg.r_gfr,
      r_gwd: msg.r_gwd,
      r_ctr: msg.r_ctr,
      out_zero: msg.out_zero,
      out_prox_off_r: msg.out_prox_off_r,
      out_prox_off_l: msg.out_prox_off_l,
    }
  }
}


