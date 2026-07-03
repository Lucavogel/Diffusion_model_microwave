#pragma once

#include <cmath>

namespace eurodao_joystick_teleop {

class InputProcessor {
public:
  InputProcessor(double deadzone = 0.05, double exponent = 1.5, double alpha = 0.8)
  : deadzone_(deadzone), exponent_(exponent), alpha_(alpha) {}

  double process(double raw)
  {
    double shaped = 0.0;

    if (std::abs(raw) < deadzone_) {
      shaped = 0.0;
    } else {
      const double remapped = (std::abs(raw) - deadzone_) / (1.0 - deadzone_);
      shaped = std::pow(remapped, exponent_);
      shaped *= (raw > 0.0) ? 1.0 : -1.0;
    }

    filtered_ = alpha_ * shaped + (1.0 - alpha_) * filtered_;
    return filtered_;
  }

  void reset() { filtered_ = 0.0; }

private:
  double deadzone_{0.05};
  double exponent_{1.5};
  double alpha_{0.8};
  double filtered_{0.0};
};

}  // namespace eurodao_joystick_teleop

