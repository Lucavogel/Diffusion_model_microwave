#include <algorithm>
#include <chrono>
#include <cctype>
#include <cmath>
#include <fstream>
#include <memory>
#include <mutex>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

#include <ament_index_cpp/get_package_share_directory.hpp>
#include <geometry_msgs/msg/transform_stamped.hpp>
#include <geometry_msgs/msg/pose.hpp>
#include <geometry_msgs/msg/pose_stamped.hpp>
#include <moveit/move_group_interface/move_group_interface.hpp>
#include <moveit/planning_scene/planning_scene.hpp>
#include <moveit/planning_scene_interface/planning_scene_interface.hpp>
#include <moveit/robot_state/conversions.hpp>
#include <moveit_msgs/msg/collision_object.hpp>
#include <moveit_msgs/msg/move_it_error_codes.hpp>
#include <moveit_msgs/msg/robot_trajectory.hpp>
#include <moveit_msgs/srv/get_motion_plan.hpp>
#include <moveit_msgs/srv/get_position_ik.hpp>
#include <onrobot_rg_msgs/msg/on_robot_rg_input.hpp>
#include <onrobot_rg_msgs/msg/on_robot_rg_output.hpp>
#include <rclcpp/rclcpp.hpp>
#include <shape_msgs/msg/solid_primitive.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2/LinearMath/Transform.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

namespace
{

enum class WaypointType
{
  PoseTarget,
  JointTarget,
  GripperCommand,
};

struct WaypointSpec
{
  WaypointType type{WaypointType::PoseTarget};
  geometry_msgs::msg::Pose pose;
  bool has_orientation{false};
  std::vector<double> joint_positions;
  double gripper_width_mm{0.0};
  double gripper_force_n{0.0};
  std::string description;
  double pause_after_sec{0.0};
};

struct GripperDefaults
{
  double open_width_mm{47.3};
  double open_force_n{10.0};
  double close_width_mm{0.0};
  double close_force_n{40.0};
};

bool starts_with(const std::string & value, const std::string & prefix)
{
  return value.rfind(prefix, 0) == 0;
}

std::string trim(const std::string & input)
{
  const auto begin = input.find_first_not_of(" \t\r\n");
  if (begin == std::string::npos) {
    return "";
  }

  const auto end = input.find_last_not_of(" \t\r\n");
  return input.substr(begin, end - begin + 1);
}

std::string to_lower(std::string value)
{
  std::transform(
    value.begin(), value.end(), value.begin(),
    [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
  return value;
}

std::string sanitize_id(std::string value)
{
  std::transform(
    value.begin(), value.end(), value.begin(),
    [](unsigned char c) {
      return static_cast<char>(std::isalnum(c) || c == '_' ? c : '_');
    });
  return value;
}

std::string format_joint_positions(const std::vector<double> & values)
{
  std::ostringstream stream;
  stream.setf(std::ios::fixed, std::ios::floatfield);
  stream.precision(5);
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0) {
      stream << ' ';
    }
    stream << values[index];
  }
  return stream.str();
}

double clamp_gripper_width_mm(double width_mm)
{
  return std::clamp(width_mm, 0.0, 110.0);
}

double clamp_gripper_force_n(double force_n)
{
  return std::clamp(force_n, 0.0, 40.0);
}

std::vector<std::string> read_data_lines(const std::string & file_path)
{
  std::ifstream input(file_path);
  if (!input.is_open()) {
    throw std::runtime_error("Impossible d'ouvrir le fichier: " + file_path);
  }

  std::vector<std::string> lines;
  std::string line;
  while (std::getline(input, line)) {
    const auto cleaned = trim(line);
    if (cleaned.empty() || starts_with(cleaned, "#")) {
      continue;
    }
    lines.push_back(cleaned);
  }

  return lines;
}

std::vector<double> parse_doubles(const std::string & line)
{
  std::istringstream stream(line);
  std::vector<double> values;
  double value = 0.0;
  while (stream >> value) {
    values.push_back(value);
  }

  if (!stream.eof()) {
    throw std::runtime_error("Valeur numerique invalide: " + line);
  }

  return values;
}

geometry_msgs::msg::Quaternion normalized_or_identity(geometry_msgs::msg::Quaternion quaternion)
{
  const double norm = std::sqrt(
    quaternion.x * quaternion.x + quaternion.y * quaternion.y +
    quaternion.z * quaternion.z + quaternion.w * quaternion.w);

  if (norm < 1e-9) {
    quaternion.x = 0.0;
    quaternion.y = 0.0;
    quaternion.z = 0.0;
    quaternion.w = 1.0;
    return quaternion;
  }

  quaternion.x /= norm;
  quaternion.y /= norm;
  quaternion.z /= norm;
  quaternion.w /= norm;
  return quaternion;
}

geometry_msgs::msg::Pose make_pose(
  const std::vector<double> & position,
  const std::vector<double> & orientation)
{
  if (position.size() != 3) {
    throw std::runtime_error("Une pose doit contenir 3 valeurs de position.");
  }
  if (orientation.size() != 4) {
    throw std::runtime_error("Une pose doit contenir 4 valeurs de quaternion.");
  }

  geometry_msgs::msg::Pose pose;
  pose.position.x = position[0];
  pose.position.y = position[1];
  pose.position.z = position[2];
  pose.orientation.x = orientation[0];
  pose.orientation.y = orientation[1];
  pose.orientation.z = orientation[2];
  pose.orientation.w = orientation[3];
  pose.orientation = normalized_or_identity(pose.orientation);
  return pose;
}

geometry_msgs::msg::Pose compose_pose(
  const geometry_msgs::msg::Pose & base_pose,
  const geometry_msgs::msg::Pose & local_pose)
{
  tf2::Transform base_tf;
  tf2::fromMsg(base_pose, base_tf);

  tf2::Transform local_tf;
  tf2::fromMsg(local_pose, local_tf);

  const tf2::Transform world_tf = base_tf * local_tf;
  geometry_msgs::msg::Pose world_pose;
  world_pose.position.x = world_tf.getOrigin().x();
  world_pose.position.y = world_tf.getOrigin().y();
  world_pose.position.z = world_tf.getOrigin().z();
  const tf2::Quaternion world_quaternion = world_tf.getRotation();
  world_pose.orientation.x = world_quaternion.x();
  world_pose.orientation.y = world_quaternion.y();
  world_pose.orientation.z = world_quaternion.z();
  world_pose.orientation.w = world_quaternion.w();
  return world_pose;
}

geometry_msgs::msg::Pose transform_to_pose(const geometry_msgs::msg::TransformStamped & transform)
{
  geometry_msgs::msg::Pose pose;
  pose.position.x = transform.transform.translation.x;
  pose.position.y = transform.transform.translation.y;
  pose.position.z = transform.transform.translation.z;
  pose.orientation = transform.transform.rotation;
  pose.orientation = normalized_or_identity(pose.orientation);
  return pose;
}

class GripperCommandRunner
{
public:
  GripperCommandRunner(
    rclcpp::Node * node,
    std::string command_topic,
    std::string status_topic)
  : node_(node),
    command_topic_(std::move(command_topic)),
    status_topic_(std::move(status_topic))
  {
    publisher_ = node_->create_publisher<onrobot_rg_msgs::msg::OnRobotRGOutput>(
      command_topic_,
      10);
    subscription_ = node_->create_subscription<onrobot_rg_msgs::msg::OnRobotRGInput>(
      status_topic_,
      10,
      [this](const onrobot_rg_msgs::msg::OnRobotRGInput::SharedPtr msg) {
        std::scoped_lock lock(mutex_);
        has_status_ = true;
        status_sequence_ += 1;
        busy_ = (msg->busy != 0);
        width_mm_ = clamp_gripper_width_mm(static_cast<double>(msg->grip_width) / 10.0);
      });
  }

  bool execute_command(
    const WaypointSpec & waypoint,
    double timeout_sec,
    double width_tolerance_mm,
    bool execute_motion,
    const rclcpp::Logger & logger)
  {
    if (waypoint.type != WaypointType::GripperCommand) {
      return true;
    }

    const double target_width_mm = clamp_gripper_width_mm(waypoint.gripper_width_mm);
    const double target_force_n = clamp_gripper_force_n(waypoint.gripper_force_n);
    const std::string label =
      waypoint.description.empty() ? "custom" : waypoint.description;

    if (!execute_motion) {
      RCLCPP_INFO(
        logger,
        "Simulation pince %s: target=%.1f mm force=%.1f N",
        label.c_str(),
        target_width_mm,
        target_force_n);
      return true;
    }

    if (!wait_for_status(timeout_sec)) {
      RCLCPP_ERROR(
        logger,
        "Aucun statut recu sur %s pour commander la pince.",
        status_topic_.c_str());
      return false;
    }

    if (!wait_until_idle(timeout_sec)) {
      RCLCPP_ERROR(
        logger,
        "La pince reste occupee avant la commande %s.",
        label.c_str());
      return false;
    }

    const auto initial_snapshot = snapshot();
    publish_command(target_width_mm, target_force_n, 1);
    RCLCPP_INFO(
      logger,
      "Commande pince %s via %s: target=%.1f mm force=%.1f N",
      label.c_str(),
      command_topic_.c_str(),
      target_width_mm,
      target_force_n);

    const auto deadline = std::chrono::steady_clock::now() + std::chrono::duration_cast<
      std::chrono::steady_clock::duration>(std::chrono::duration<double>(timeout_sec));
    bool saw_busy = false;

    while (std::chrono::steady_clock::now() < deadline) {
      const auto current_snapshot = snapshot();
      if (current_snapshot.has_status && current_snapshot.sequence > initial_snapshot.sequence) {
        saw_busy = saw_busy || current_snapshot.busy;
        if (!current_snapshot.busy) {
          if (saw_busy ||
            std::abs(current_snapshot.width_mm - target_width_mm) <= width_tolerance_mm)
          {
            RCLCPP_INFO(
              logger,
              "Commande pince %s terminee. Ouverture=%.1f mm",
              label.c_str(),
              current_snapshot.width_mm);
            return true;
          }
        }
      }

      rclcpp::sleep_for(std::chrono::milliseconds(50));
    }

    const auto final_snapshot = snapshot();
    if (final_snapshot.has_status && !final_snapshot.busy &&
      (saw_busy ||
      std::abs(final_snapshot.width_mm - target_width_mm) <= width_tolerance_mm))
    {
      RCLCPP_INFO(
        logger,
        "Commande pince %s terminee hors delai strict. Ouverture=%.1f mm",
        label.c_str(),
        final_snapshot.width_mm);
      return true;
    }

    RCLCPP_ERROR(
      logger,
      "Timeout sur la commande pince %s. Ouverture finale=%.1f mm busy=%s",
      label.c_str(),
      final_snapshot.width_mm,
      final_snapshot.busy ? "true" : "false");
    return false;
  }

private:
  struct StatusSnapshot
  {
    bool has_status{false};
    bool busy{false};
    double width_mm{0.0};
    std::size_t sequence{0};
  };

  StatusSnapshot snapshot() const
  {
    std::scoped_lock lock(mutex_);
    return StatusSnapshot{has_status_, busy_, width_mm_, status_sequence_};
  }

  bool wait_for_status(double timeout_sec) const
  {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::duration_cast<
      std::chrono::steady_clock::duration>(std::chrono::duration<double>(timeout_sec));
    while (std::chrono::steady_clock::now() < deadline) {
      if (snapshot().has_status) {
        return true;
      }
      rclcpp::sleep_for(std::chrono::milliseconds(50));
    }
    return snapshot().has_status;
  }

  bool wait_until_idle(double timeout_sec) const
  {
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::duration_cast<
      std::chrono::steady_clock::duration>(std::chrono::duration<double>(timeout_sec));
    while (std::chrono::steady_clock::now() < deadline) {
      const auto current_snapshot = snapshot();
      if (current_snapshot.has_status && !current_snapshot.busy) {
        return true;
      }
      rclcpp::sleep_for(std::chrono::milliseconds(50));
    }

    const auto current_snapshot = snapshot();
    return current_snapshot.has_status && !current_snapshot.busy;
  }

  void publish_command(double width_mm, double force_n, uint8_t control)
  {
    onrobot_rg_msgs::msg::OnRobotRGOutput command;
    command.r_gwd = static_cast<uint16_t>(std::lround(clamp_gripper_width_mm(width_mm) * 10.0));
    command.r_gfr = static_cast<uint16_t>(std::lround(clamp_gripper_force_n(force_n) * 10.0));
    command.r_ctr = control;
    command.out_zero = 0;
    command.out_prox_off_r = 0;
    command.out_prox_off_l = 0;
    publisher_->publish(command);
  }

  rclcpp::Node * node_{nullptr};
  std::string command_topic_;
  std::string status_topic_;
  mutable std::mutex mutex_;
  bool has_status_{false};
  bool busy_{false};
  double width_mm_{0.0};
  std::size_t status_sequence_{0};
  rclcpp::Publisher<onrobot_rg_msgs::msg::OnRobotRGOutput>::SharedPtr publisher_;
  rclcpp::Subscription<onrobot_rg_msgs::msg::OnRobotRGInput>::SharedPtr subscription_;
};

std::optional<moveit_msgs::msg::CollisionObject> parse_scene_object(
  const std::string & raw_name,
  const std::vector<std::string> & block_lines,
  const std::string & frame_id,
  const rclcpp::Logger & logger)
{
  if (block_lines.size() < 5) {
    throw std::runtime_error("Bloc scene incomplet pour " + raw_name);
  }

  const auto position = parse_doubles(block_lines[0]);
  const auto orientation = parse_doubles(block_lines[1]);
  const auto enabled = parse_doubles(block_lines[2]);
  const auto type = to_lower(block_lines[3]);
  const auto dimensions = parse_doubles(block_lines[4]);

  if (!enabled.empty() && enabled.front() == 0.0) {
    RCLCPP_INFO(logger, "Objet de scene ignore car desactive: %s", raw_name.c_str());
    return std::nullopt;
  }

  geometry_msgs::msg::Pose base_pose = make_pose(position, orientation);
  geometry_msgs::msg::Pose local_pose;
  local_pose.orientation.w = 1.0;
  if (block_lines.size() >= 7) {
    local_pose = make_pose(parse_doubles(block_lines[5]), parse_doubles(block_lines[6]));
  }
  const geometry_msgs::msg::Pose world_pose = compose_pose(base_pose, local_pose);

  shape_msgs::msg::SolidPrimitive primitive;
  if (type == "box") {
    if (dimensions.size() != 3) {
      throw std::runtime_error("Dimensions invalides pour une box: " + raw_name);
    }
    primitive.type = shape_msgs::msg::SolidPrimitive::BOX;
    primitive.dimensions = {
      dimensions[shape_msgs::msg::SolidPrimitive::BOX_X],
      dimensions[shape_msgs::msg::SolidPrimitive::BOX_Y],
      dimensions[shape_msgs::msg::SolidPrimitive::BOX_Z]};
  } else if (type == "cylinder") {
    if (dimensions.size() != 2) {
      throw std::runtime_error("Dimensions invalides pour un cylindre: " + raw_name);
    }
    primitive.type = shape_msgs::msg::SolidPrimitive::CYLINDER;
    primitive.dimensions.resize(2);
    primitive.dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_HEIGHT] = dimensions[1];
    primitive.dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_RADIUS] = dimensions[0];
  } else if (type == "sphere") {
    if (dimensions.size() != 1) {
      throw std::runtime_error("Dimensions invalides pour une sphere: " + raw_name);
    }
    primitive.type = shape_msgs::msg::SolidPrimitive::SPHERE;
    primitive.dimensions = {dimensions[0]};
  } else {
    RCLCPP_WARN(
      logger, "Type de primitive non supporte dans la scene: %s (%s)",
      raw_name.c_str(), type.c_str());
    return std::nullopt;
  }

  moveit_msgs::msg::CollisionObject object;
  object.header.frame_id = frame_id;
  object.id = sanitize_id(raw_name);
  object.primitives.push_back(primitive);
  object.primitive_poses.push_back(world_pose);
  object.operation = moveit_msgs::msg::CollisionObject::ADD;
  return object;
}

std::vector<moveit_msgs::msg::CollisionObject> load_scene_objects(
  const std::string & scene_file,
  const std::string & frame_id,
  const rclcpp::Logger & logger)
{
  const auto lines = read_data_lines(scene_file);
  if (lines.empty()) {
    throw std::runtime_error("Le fichier scene est vide: " + scene_file);
  }

  std::vector<moveit_msgs::msg::CollisionObject> objects;
  for (std::size_t index = 1; index < lines.size();) {
    const auto & line = lines[index];
    if (line == ".") {
      break;
    }
    if (!starts_with(line, "*")) {
      throw std::runtime_error("Bloc scene inattendu: " + line);
    }

    const std::string name = trim(line.substr(1));
    ++index;

    std::vector<std::string> block_lines;
    while (index < lines.size() && !starts_with(lines[index], "*") && lines[index] != ".") {
      block_lines.push_back(lines[index]);
      ++index;
    }

    if (auto object = parse_scene_object(name, block_lines, frame_id, logger)) {
      objects.push_back(*object);
    }
  }

  return objects;
}

std::vector<WaypointSpec> parse_waypoint_lines(
  const std::vector<std::string> & waypoint_lines,
  const std::string & source_name,
  const GripperDefaults & gripper_defaults)
{
  std::vector<WaypointSpec> waypoints;
  waypoints.reserve(waypoint_lines.size());

  for (const auto & line : waypoint_lines) {
    const auto lower_line = to_lower(line);
    if (starts_with(lower_line, "pause ") || starts_with(lower_line, "wait ")) {
      if (waypoints.empty()) {
        throw std::runtime_error(
                "Une pause doit suivre un waypoint dans " + source_name + ": " + line);
      }

      const auto pause_values = parse_doubles(trim(line.substr(line.find(' ') + 1)));
      if (pause_values.size() != 1 || pause_values.front() < 0.0) {
        throw std::runtime_error(
                "Une pause doit contenir une seule valeur positive ou nulle dans " + source_name +
                ": " + line);
      }

      waypoints.back().pause_after_sec = pause_values.front();
      continue;
    }

    if (starts_with(lower_line, "gripper ")) {
      const std::string command_spec = trim(line.substr(line.find(' ') + 1));
      const std::string lower_command_spec = to_lower(command_spec);

      WaypointSpec waypoint;
      waypoint.type = WaypointType::GripperCommand;
      if (lower_command_spec == "open" || lower_command_spec == "ouvrir") {
        waypoint.gripper_width_mm = clamp_gripper_width_mm(gripper_defaults.open_width_mm);
        waypoint.gripper_force_n = clamp_gripper_force_n(gripper_defaults.open_force_n);
        waypoint.description = "open";
      } else if (lower_command_spec == "close" || lower_command_spec == "fermer") {
        waypoint.gripper_width_mm = clamp_gripper_width_mm(gripper_defaults.close_width_mm);
        waypoint.gripper_force_n = clamp_gripper_force_n(gripper_defaults.close_force_n);
        waypoint.description = "close";
      } else {
        const auto values = parse_doubles(command_spec);
        if (values.size() != 2) {
          throw std::runtime_error(
                  "Une commande pince doit etre 'gripper open', 'gripper close' ou "
                  "'gripper <largeur_mm> <force_n>' dans " + source_name + ": " + line);
        }
        waypoint.gripper_width_mm = clamp_gripper_width_mm(values[0]);
        waypoint.gripper_force_n = clamp_gripper_force_n(values[1]);
        waypoint.description = "custom";
      }
      waypoints.push_back(waypoint);
      continue;
    }

    if (starts_with(lower_line, "joints ") || starts_with(lower_line, "joint ")) {
      const auto values = parse_doubles(trim(line.substr(line.find(' ') + 1)));
      if (values.size() != 6) {
        throw std::runtime_error(
                "Un waypoint articulaire doit contenir 6 valeurs dans " + source_name + ": " +
                line);
      }

      WaypointSpec waypoint;
      waypoint.joint_positions = values;
      waypoint.type = WaypointType::JointTarget;
      waypoints.push_back(waypoint);
      continue;
    }

    const auto values = parse_doubles(line);
    if (values.size() != 3 && values.size() != 7) {
      throw std::runtime_error(
              "Chaque waypoint doit contenir 3 ou 7 valeurs, 'joint(s) <6 valeurs>', "
              "'gripper open', 'gripper close', 'gripper <largeur_mm> <force_n>', ou une "
              "ligne 'pause <sec>' dans " + source_name + ": " + line);
    }

    WaypointSpec waypoint;
    waypoint.pose.position.x = values[0];
    waypoint.pose.position.y = values[1];
    waypoint.pose.position.z = values[2];
    if (values.size() == 7) {
      waypoint.pose.orientation.x = values[3];
      waypoint.pose.orientation.y = values[4];
      waypoint.pose.orientation.z = values[5];
      waypoint.pose.orientation.w = values[6];
      waypoint.pose.orientation = normalized_or_identity(waypoint.pose.orientation);
      waypoint.has_orientation = true;
    }
    waypoints.push_back(waypoint);
  }

  return waypoints;
}

std::vector<WaypointSpec> load_waypoint_specs(
  const std::string & waypoints_file,
  const std::vector<std::string> & waypoint_parameters,
  const GripperDefaults & gripper_defaults)
{
  if (!waypoints_file.empty()) {
    return parse_waypoint_lines(read_data_lines(waypoints_file), waypoints_file, gripper_defaults);
  }

  if (!waypoint_parameters.empty()) {
    return parse_waypoint_lines(waypoint_parameters, "parametre waypoints", gripper_defaults);
  }

  throw std::runtime_error("Aucun waypoint fourni.");
}

std::vector<WaypointSpec> resolve_waypoints(
  const std::vector<WaypointSpec> & waypoint_specs,
  const geometry_msgs::msg::Pose & current_pose)
{
  std::vector<WaypointSpec> resolved;
  resolved.reserve(waypoint_specs.size());

  auto current_orientation = normalized_or_identity(current_pose.orientation);
  for (const auto & waypoint_spec : waypoint_specs) {
    WaypointSpec resolved_waypoint = waypoint_spec;
    if (waypoint_spec.type != WaypointType::PoseTarget) {
      resolved.push_back(resolved_waypoint);
      continue;
    }

    if (!waypoint_spec.has_orientation) {
      resolved_waypoint.pose.orientation = current_orientation;
    } else {
      current_orientation = waypoint_spec.pose.orientation;
    }
    resolved_waypoint.has_orientation = true;
    resolved.push_back(resolved_waypoint);
  }

  return resolved;
}

bool execute_sequential_waypoints(
  const rclcpp::Client<moveit_msgs::srv::GetPositionIK>::SharedPtr & ik_client,
  const rclcpp::Client<moveit_msgs::srv::GetMotionPlan>::SharedPtr & motion_plan_client,
  moveit::planning_interface::MoveGroupInterface & move_group,
  const std::vector<WaypointSpec> & waypoints,
  GripperCommandRunner * gripper_runner,
  const std::string & planning_group,
  const std::string & pose_link,
  const std::string & scene_frame,
  const planning_scene::PlanningScenePtr & planning_scene,
  double ik_timeout,
  double planning_time,
  int num_planning_attempts,
  double velocity_scaling,
  double acceleration_scaling,
  double gripper_command_timeout_sec,
  double gripper_width_tolerance_mm,
  double post_execute_settle_sec,
  bool execute_motion,
  const rclcpp::Logger & logger)
{
  const auto * joint_model_group =
    move_group.getRobotModel()->getJointModelGroup(planning_group);
  if (joint_model_group == nullptr) {
    RCLCPP_ERROR(
      logger, "Groupe de planification introuvable pour l'IK: %s",
      planning_group.c_str());
    return false;
  }

  std::optional<std::vector<double>> simulated_group_positions;

  for (std::size_t index = 0; index < waypoints.size(); ++index) {
    if (waypoints[index].type == WaypointType::GripperCommand) {
      if (gripper_runner == nullptr) {
        RCLCPP_ERROR(logger, "La pince n'est pas configuree pour le step %zu.", index + 1);
        return false;
      }

      if (!gripper_runner->execute_command(
          waypoints[index],
          gripper_command_timeout_sec,
          gripper_width_tolerance_mm,
          execute_motion,
          logger))
      {
        RCLCPP_ERROR(
          logger, "Echec d'execution de la commande pince pour le step %zu.", index + 1);
        return false;
      }

      if (waypoints[index].pause_after_sec > 0.0) {
        RCLCPP_INFO(
          logger, "Pause de %.3f s apres le step %zu.",
          waypoints[index].pause_after_sec, index + 1);
        rclcpp::sleep_for(std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::duration<double>(waypoints[index].pause_after_sec)));
      }
      continue;
    }

    move_group.setStartStateToCurrentState();

    const auto current_state = move_group.getCurrentState(2.0);
    if (!current_state) {
      RCLCPP_ERROR(logger, "Impossible de lire l'etat courant avant le waypoint %zu.", index + 1);
      return false;
    }

    std::vector<double> current_group_positions;
    moveit::core::RobotState planning_start_state(*current_state);
    if (simulated_group_positions) {
      planning_start_state.setJointGroupPositions(
        joint_model_group, *simulated_group_positions);
      planning_start_state.update();
    }
    planning_start_state.copyJointGroupPositions(joint_model_group, current_group_positions);
    planning_scene->setCurrentState(planning_start_state);

    std::vector<double> joint_target;
    if (waypoints[index].type == WaypointType::JointTarget) {
      if (waypoints[index].joint_positions.size() != joint_model_group->getVariableCount()) {
        RCLCPP_ERROR(
          logger,
          "Le waypoint articulaire %zu ne contient pas %u joints.",
          index + 1,
          joint_model_group->getVariableCount());
        return false;
      }
      joint_target = waypoints[index].joint_positions;
      moveit::core::RobotState goal_state(planning_start_state);
      goal_state.setJointGroupPositions(joint_model_group, joint_target);
      goal_state.update();
      if (planning_scene->isStateColliding(goal_state, planning_group, false)) {
        RCLCPP_ERROR(
          logger,
          "Le waypoint articulaire %zu est en collision.",
          index + 1);
        return false;
      }
    } else {
      if (!ik_client->wait_for_service(std::chrono::duration<double>(ik_timeout + 1.0))) {
        RCLCPP_ERROR(logger, "Service /compute_ik indisponible.");
        return false;
      }

      auto request = std::make_shared<moveit_msgs::srv::GetPositionIK::Request>();
      auto & ik_request = request->ik_request;
      ik_request.group_name = planning_group;
      ik_request.robot_state.joint_state.header.frame_id = "base_link";
      ik_request.robot_state.joint_state.name = joint_model_group->getVariableNames();
      ik_request.robot_state.joint_state.position = current_group_positions;
      ik_request.avoid_collisions = true;
      ik_request.ik_link_name = pose_link;
      ik_request.pose_stamped.header.frame_id = scene_frame;
      ik_request.pose_stamped.pose = waypoints[index].pose;
      ik_request.timeout = static_cast<builtin_interfaces::msg::Duration>(
        rclcpp::Duration::from_seconds(ik_timeout));

      auto response_future = ik_client->async_send_request(request);
      if (response_future.wait_for(std::chrono::duration<double>(ik_timeout + 1.0)) !=
        std::future_status::ready)
      {
        RCLCPP_ERROR(logger, "Timeout sur /compute_ik pour le waypoint %zu.", index + 1);
        return false;
      }

      const auto response = response_future.get();
      if (!response ||
        response->error_code.val != moveit_msgs::msg::MoveItErrorCodes::SUCCESS)
      {
        RCLCPP_ERROR(
          logger,
          "Aucune IK sans collision trouvee pour le waypoint %zu.",
          index + 1);
        return false;
      }

      moveit::core::RobotState ik_state(move_group.getRobotModel());
      if (!moveit::core::robotStateMsgToRobotState(response->solution, ik_state, true)) {
        RCLCPP_ERROR(
          logger, "Impossible de convertir la solution IK pour le waypoint %zu.",
          index + 1);
        return false;
      }
      ik_state.update();
      if (planning_scene->isStateColliding(ik_state, planning_group, false)) {
        RCLCPP_ERROR(
          logger,
          "Le waypoint %zu reste en collision apres calcul IK.",
          index + 1);
        return false;
      }

      ik_state.copyJointGroupPositions(joint_model_group, joint_target);
    }

    if (!motion_plan_client->wait_for_service(std::chrono::duration<double>(planning_time + 1.0))) {
      RCLCPP_ERROR(logger, "Service /plan_kinematic_path indisponible.");
      return false;
    }

    auto plan_request = std::make_shared<moveit_msgs::srv::GetMotionPlan::Request>();
    auto & motion_request = plan_request->motion_plan_request;
    motion_request.group_name = planning_group;
    motion_request.start_state.joint_state.header.frame_id = "base_link";
    motion_request.start_state.joint_state.name = joint_model_group->getVariableNames();
    motion_request.start_state.joint_state.position = current_group_positions;
    moveit_msgs::msg::Constraints goal_constraints;
    const auto & joint_names = joint_model_group->getVariableNames();
    goal_constraints.joint_constraints.reserve(joint_names.size());
    for (std::size_t joint_index = 0; joint_index < joint_names.size(); ++joint_index) {
      moveit_msgs::msg::JointConstraint joint_constraint;
      joint_constraint.joint_name = joint_names[joint_index];
      joint_constraint.position = joint_target[joint_index];
      joint_constraint.tolerance_above = 1e-3;
      joint_constraint.tolerance_below = 1e-3;
      joint_constraint.weight = 1.0;
      goal_constraints.joint_constraints.push_back(joint_constraint);
    }
    motion_request.goal_constraints.push_back(goal_constraints);
    motion_request.num_planning_attempts = num_planning_attempts;
    motion_request.allowed_planning_time = planning_time;
    motion_request.max_velocity_scaling_factor = velocity_scaling;
    motion_request.max_acceleration_scaling_factor = acceleration_scaling;

    auto motion_plan_future = motion_plan_client->async_send_request(plan_request);
    if (motion_plan_future.wait_for(std::chrono::duration<double>(planning_time + 1.0)) !=
      std::future_status::ready)
    {
      RCLCPP_ERROR(logger, "Timeout sur /plan_kinematic_path pour le waypoint %zu.", index + 1);
      return false;
    }

    const auto motion_plan_response = motion_plan_future.get();
    if (!motion_plan_response ||
      motion_plan_response->motion_plan_response.error_code.val !=
      moveit_msgs::msg::MoveItErrorCodes::SUCCESS)
    {
      RCLCPP_ERROR(
        logger, "Echec de planification pour le waypoint %zu.", index + 1);
      return false;
    }

    RCLCPP_INFO(
      logger, "Waypoint %zu planifie. Joints cible: %s",
      index + 1, format_joint_positions(joint_target).c_str());
    if (execute_motion) {
      const auto execution_result = move_group.execute(
        motion_plan_response->motion_plan_response.trajectory);
      if (execution_result != moveit::core::MoveItErrorCode::SUCCESS) {
        move_group.clearPoseTargets();
        RCLCPP_ERROR(
          logger, "Echec d'execution pour le waypoint %zu.", index + 1);
        return false;
      }
      RCLCPP_INFO(logger, "Waypoint %zu execute.", index + 1);
      if (post_execute_settle_sec > 0.0) {
        rclcpp::sleep_for(std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::duration<double>(post_execute_settle_sec)));
      }
      if (waypoints[index].pause_after_sec > 0.0) {
        RCLCPP_INFO(
          logger, "Pause de %.3f s apres le waypoint %zu.",
          waypoints[index].pause_after_sec, index + 1);
        rclcpp::sleep_for(std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::duration<double>(waypoints[index].pause_after_sec)));
      }
    } else {
      simulated_group_positions = joint_target;
    }

    move_group.clearPoseTargets();
  }

  return true;
}

}  // namespace

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);

  auto node = std::make_shared<rclcpp::Node>("scene_waypoint_runner");
  const auto logger = node->get_logger();

  const std::string package_share =
    ament_index_cpp::get_package_share_directory("earth_robot_moveit_config");
  const std::string default_scene_file = package_share + "/config/empty.scene";
  const std::string default_waypoints_file = package_share + "/config/waypoints_example.txt";

  const auto scene_file = node->declare_parameter<std::string>("scene_file", default_scene_file);
  const auto waypoints_file = node->declare_parameter<std::string>(
    "waypoints_file", default_waypoints_file);
  const auto inline_waypoints = node->declare_parameter<std::vector<std::string>>(
    "waypoints", std::vector<std::string>{});
  const auto planning_group = node->declare_parameter<std::string>("planning_group", "arm");
  const auto pose_link = node->declare_parameter<std::string>("pose_link", "tool0");
  const auto scene_frame = node->declare_parameter<std::string>("scene_frame", "world");
  const auto cartesian_mode = node->declare_parameter<bool>("cartesian_mode", true);
  const auto fallback_to_sequential = node->declare_parameter<bool>("fallback_to_sequential", true);
  const auto execute_motion = node->declare_parameter<bool>("execute", true);
  const auto validate_inputs_only = node->declare_parameter<bool>("validate_inputs_only", false);
  const auto eef_step = node->declare_parameter<double>("eef_step", 0.01);
  const auto min_fraction = node->declare_parameter<double>("min_fraction", 0.99);
  const auto planning_time = node->declare_parameter<double>("planning_time", 5.0);
  const auto num_planning_attempts = node->declare_parameter<int>("num_planning_attempts", 1);
  const auto velocity_scaling = node->declare_parameter<double>("velocity_scaling", 0.1);
  const auto acceleration_scaling = node->declare_parameter<double>("acceleration_scaling", 0.1);
  const auto post_execute_settle_sec =
    node->declare_parameter<double>("post_execute_settle_sec", 0.5);
  const auto gripper_command_topic =
    node->declare_parameter<std::string>("gripper_command_topic", "OnRobotRGOutput");
  const auto gripper_status_topic =
    node->declare_parameter<std::string>("gripper_status_topic", "OnRobotRGInput");
  const auto gripper_open_width_mm =
    node->declare_parameter<double>("gripper_open_width_mm", 47.3);
  const auto gripper_open_force_n =
    node->declare_parameter<double>("gripper_open_force_n", 10.0);
  const auto gripper_close_width_mm =
    node->declare_parameter<double>("gripper_close_width_mm", 0.0);
  const auto gripper_close_force_n =
    node->declare_parameter<double>("gripper_close_force_n", 40.0);
  const auto gripper_command_timeout_sec =
    node->declare_parameter<double>("gripper_command_timeout_sec", 10.0);
  const auto gripper_width_tolerance_mm =
    node->declare_parameter<double>("gripper_width_tolerance_mm", 2.0);
  const auto state_lookup_timeout = node->declare_parameter<double>("state_lookup_timeout", 3.0);
  const auto planning_pipeline = node->declare_parameter<std::string>("planning_pipeline", "");
  const auto planner_id = node->declare_parameter<std::string>("planner_id", "");

  try {
    const GripperDefaults gripper_defaults{
      clamp_gripper_width_mm(gripper_open_width_mm),
      clamp_gripper_force_n(gripper_open_force_n),
      clamp_gripper_width_mm(gripper_close_width_mm),
      clamp_gripper_force_n(gripper_close_force_n)};
    const auto collision_objects = load_scene_objects(scene_file, scene_frame, logger);
    const auto waypoint_specs = load_waypoint_specs(
      waypoints_file, inline_waypoints, gripper_defaults);

    RCLCPP_INFO(
      logger, "Scene chargee: %zu objets depuis %s",
      collision_objects.size(), scene_file.c_str());
    RCLCPP_INFO(
      logger, "Waypoints charges: %zu depuis %s",
      waypoint_specs.size(),
      waypoints_file.empty() ? "parametres inline" : waypoints_file.c_str());

    if (validate_inputs_only) {
      RCLCPP_INFO(logger, "Validation terminee, aucune planification demandee.");
      rclcpp::shutdown();
      return 0;
    }

    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(node);
    std::thread spinner([&executor]() { executor.spin(); });
    auto ik_client = node->create_client<moveit_msgs::srv::GetPositionIK>("/compute_ik");
    auto motion_plan_client = node->create_client<moveit_msgs::srv::GetMotionPlan>(
      "/plan_kinematic_path");

    int exit_code = 0;
    try {
      moveit::planning_interface::PlanningSceneInterface planning_scene_interface;
      const bool scene_applied = planning_scene_interface.applyCollisionObjects(collision_objects);
      if (!scene_applied) {
        throw std::runtime_error("Impossible d'appliquer les objets de collision a MoveIt.");
      }

      rclcpp::sleep_for(std::chrono::milliseconds(500));

      moveit::planning_interface::MoveGroupInterface move_group(node, planning_group);
      move_group.setPoseReferenceFrame(scene_frame);
      move_group.setPlanningTime(planning_time);
      move_group.setNumPlanningAttempts(num_planning_attempts);
      move_group.setMaxVelocityScalingFactor(velocity_scaling);
      move_group.setMaxAccelerationScalingFactor(acceleration_scaling);
      if (!planning_pipeline.empty()) {
        move_group.setPlanningPipelineId(planning_pipeline);
      }
      if (!planner_id.empty()) {
        move_group.setPlannerId(planner_id);
      }

      auto local_planning_scene =
        std::make_shared<planning_scene::PlanningScene>(move_group.getRobotModel());
      for (const auto & collision_object : collision_objects) {
        if (!local_planning_scene->processCollisionObjectMsg(collision_object)) {
          throw std::runtime_error(
                  "Impossible d'appliquer un objet de collision dans la scene locale: " +
                  collision_object.id);
        }
      }

      move_group.startStateMonitor(state_lookup_timeout);
      move_group.setStartStateToCurrentState();

      tf2_ros::Buffer tf_buffer(node->get_clock());
      tf2_ros::TransformListener tf_listener(tf_buffer, node, true);
      const auto transform = tf_buffer.lookupTransform(
        scene_frame,
        pose_link,
        tf2::TimePointZero,
        tf2::durationFromSec(state_lookup_timeout));
      const auto resolved_waypoints = resolve_waypoints(
        waypoint_specs, transform_to_pose(transform));

      if (resolved_waypoints.empty()) {
        throw std::runtime_error("La liste de waypoints resolus est vide.");
      }

      std::unique_ptr<GripperCommandRunner> gripper_runner;
      const bool has_gripper_commands = std::any_of(
        resolved_waypoints.begin(), resolved_waypoints.end(),
        [](const auto & waypoint) { return waypoint.type == WaypointType::GripperCommand; });
      if (has_gripper_commands) {
        gripper_runner = std::make_unique<GripperCommandRunner>(
          node.get(),
          gripper_command_topic,
          gripper_status_topic);
      }

      const bool requires_sequential_execution = std::any_of(
        resolved_waypoints.begin(), resolved_waypoints.end(),
        [](const auto & waypoint) {
          return waypoint.pause_after_sec > 0.0 || waypoint.type != WaypointType::PoseTarget;
        });

      std::vector<geometry_msgs::msg::Pose> cartesian_waypoints;
      cartesian_waypoints.reserve(resolved_waypoints.size());
      for (const auto & waypoint : resolved_waypoints) {
        if (waypoint.type == WaypointType::PoseTarget) {
          cartesian_waypoints.push_back(waypoint.pose);
        }
      }

      bool success = false;
      if (cartesian_mode && !requires_sequential_execution) {
        moveit_msgs::msg::RobotTrajectory trajectory;
        moveit_msgs::msg::MoveItErrorCodes error_code;
        const double fraction = move_group.computeCartesianPath(
          cartesian_waypoints, eef_step, trajectory, true, &error_code);

        RCLCPP_INFO(
          logger, "Fraction cartesian path: %.3f", fraction);
        if (fraction >= min_fraction) {
          success = true;
          if (execute_motion) {
            const auto execution_result = move_group.execute(trajectory);
            success = execution_result == moveit::core::MoveItErrorCode::SUCCESS;
            if (!success) {
              RCLCPP_ERROR(logger, "Execution de la trajectoire cartesienne en echec.");
            }
          }
        } else {
          RCLCPP_WARN(
            logger,
            "Le chemin cartesien n'atteint que %.1f%% des waypoints (min %.1f%%).",
            fraction * 100.0, min_fraction * 100.0);
        }
      } else if (cartesian_mode && requires_sequential_execution) {
        RCLCPP_INFO(
          logger,
          "Des pauses sont definies entre les waypoints, execution sequentielle imposee.");
      }

      if (!success && fallback_to_sequential) {
        RCLCPP_INFO(logger, "Fallback vers une planification waypoint par waypoint.");
        success = execute_sequential_waypoints(
          ik_client,
          motion_plan_client,
          move_group,
          resolved_waypoints,
          gripper_runner.get(),
          planning_group,
          pose_link,
          scene_frame,
          local_planning_scene,
          std::max(0.1, std::min(planning_time, 2.0)),
          planning_time,
          num_planning_attempts,
          velocity_scaling,
          acceleration_scaling,
          gripper_command_timeout_sec,
          gripper_width_tolerance_mm,
          post_execute_settle_sec,
          execute_motion,
          logger);
      }

      exit_code = success ? 0 : 1;
    } catch (const std::exception & exception) {
      RCLCPP_ERROR(logger, "%s", exception.what());
      exit_code = 1;
    }

    executor.cancel();
    spinner.join();
    rclcpp::shutdown();
    return exit_code;
  } catch (const std::exception & exception) {
    RCLCPP_ERROR(logger, "%s", exception.what());
    rclcpp::shutdown();
    return 1;
  }
}
