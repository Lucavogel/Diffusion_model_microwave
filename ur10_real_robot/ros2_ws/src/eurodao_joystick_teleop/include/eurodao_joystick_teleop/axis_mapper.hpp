#pragma once

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace eurodao_joystick_teleop {

enum class Component : uint8_t {
  LX,
  LY,
  LZ,
  AX,
  AY,
  AZ,
};

struct TwistComponents {
  double lx{0.0};
  double ly{0.0};
  double lz{0.0};
  double ax{0.0};
  double ay{0.0};
  double az{0.0};

  void reset()
  {
    lx = ly = lz = ax = ay = az = 0.0;
  }
};

inline std::optional<Component> component_from_string(const std::string & s)
{
  if (s == "lx") return Component::LX;
  if (s == "ly") return Component::LY;
  if (s == "lz") return Component::LZ;
  if (s == "ax") return Component::AX;
  if (s == "ay") return Component::AY;
  if (s == "az") return Component::AZ;
  return std::nullopt;
}

struct AxisMapping {
  int axis{0};
  Component component{Component::LX};
  double scale{1.0};
  bool trigger_mode{false};
};

class AxisMapper {
public:
  explicit AxisMapper(std::vector<AxisMapping> mappings) : mappings_(std::move(mappings)) {}

  TwistComponents map_axes(const std::vector<float> & axes) const
  {
    TwistComponents result;

    for (const auto & mapping : mappings_) {
      if (mapping.axis < 0) {
        continue;
      }
      const std::size_t idx = static_cast<std::size_t>(mapping.axis);
      if (idx >= axes.size()) {
        continue;
      }

      double raw = static_cast<double>(axes[idx]);
      if (mapping.trigger_mode) {
        raw = (1.0 - raw) / 2.0;
      }

      const double value = raw * mapping.scale;
      add_to_component(result, mapping.component, value);
    }

    return result;
  }

private:
  static void add_to_component(TwistComponents & c, Component comp, double value)
  {
    switch (comp) {
      case Component::LX: c.lx += value; break;
      case Component::LY: c.ly += value; break;
      case Component::LZ: c.lz += value; break;
      case Component::AX: c.ax += value; break;
      case Component::AY: c.ay += value; break;
      case Component::AZ: c.az += value; break;
    }
  }

  std::vector<AxisMapping> mappings_;
};

}  // namespace eurodao_joystick_teleop

