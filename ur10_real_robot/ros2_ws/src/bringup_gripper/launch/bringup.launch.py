from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "ip", default_value="192.168.1.1",
            description="IP address for the OnRobot gripper"),
        DeclareLaunchArgument(
            "port", default_value="502",
            description="Port for the OnRobot gripper"),
        DeclareLaunchArgument(
            "gripper", default_value="rg2ft",
            description="Type of the OnRobot gripper"),
        DeclareLaunchArgument(
            "dummy", default_value="false",
            description="Dummy mode for the OnRobot gripper"),
        DeclareLaunchArgument(
            "poll_period", default_value="0.1",
            description="Status polling period in seconds"),
        DeclareLaunchArgument(
            "publish_joint_states", default_value="true",
            description="Publish sensor_msgs/JointState from measured gripper width"),
        DeclareLaunchArgument(
            "joint_state_topic", default_value="joint_states",
            description="Topic used for published JointState messages"),
        DeclareLaunchArgument(
            "joint_name", default_value="",
            description="Joint name to publish. Empty uses <joint_prefix>finger_joint"),
        DeclareLaunchArgument(
            "joint_prefix", default_value="",
            description="Optional prefix applied to finger_joint when joint_name is empty"),
        DeclareLaunchArgument(
            "joint_open_position", default_value="0.0",
            description="Joint position corresponding to fully open gripper width"),
        DeclareLaunchArgument(
            "joint_closed_position", default_value="1.18",
            description="Joint position corresponding to fully closed gripper width"),
        DeclareLaunchArgument(
            "joint_state_merger", default_value="false",
            description="Launch a node that merges robot and gripper joint states"),
        DeclareLaunchArgument(
            "gripper_command_action", default_value="true",
            description="Launch a control_msgs/GripperCommand action server for MoveIt"),
        DeclareLaunchArgument(
            "gripper_command_action_name", default_value="gripper_command",
            description="Action name exposed by the standard gripper command server"),
        DeclareLaunchArgument(
            "gripper_command_joint_mode", default_value="true",
            description="Interpret GripperCommand position as the gripper joint position for MoveIt"),
        DeclareLaunchArgument(
            "gripper_command_topic", default_value="OnRobotRGOutput",
            description="Command topic used by the gripper command action server"),
        DeclareLaunchArgument(
            "gripper_status_topic", default_value="OnRobotRGInput",
            description="Status topic used by the gripper command action server"),
        DeclareLaunchArgument(
            "gripper_default_force_n", default_value="10.0",
            description="Default force used when the GripperCommand goal max_effort is zero"),
        DeclareLaunchArgument(
            "gripper_command_max_force_n", default_value="20.0",
            description="Safety force limit applied to GripperCommand goals"),
        DeclareLaunchArgument(
            "gripper_command_stop_first", default_value="true",
            description="Stop the current motion before accepting a new GripperCommand goal"),
        DeclareLaunchArgument(
            "gripper_command_motion_timeout_sec", default_value="10.0",
            description="Timeout for a GripperCommand motion"),
        DeclareLaunchArgument(
            "gripper_command_goal_tolerance_mm", default_value="1.0",
            description="Width tolerance used to mark a GripperCommand goal as reached"),
        DeclareLaunchArgument(
            "robot_joint_states_topic",
            default_value="/joint_state_broadcaster/joint_states",
            description="Robot joint state input for the merger"),
        DeclareLaunchArgument(
            "merged_joint_states_topic", default_value="joint_states",
            description="Merged joint state output topic"),
        DeclareLaunchArgument(
            "status_listener", default_value="false",
            description="Launch a console status listener"),
        Node(
            package="bringup_gripper",
            executable="onrobot_rg_tcp_node",
            name="OnRobotRGTcpNode",
            parameters=[
                {"ip": LaunchConfiguration("ip")},
                {"port": LaunchConfiguration("port")},
                {"gripper": LaunchConfiguration("gripper")},
                {"dummy": LaunchConfiguration("dummy")},
                {"poll_period": LaunchConfiguration("poll_period")},
                {"publish_joint_states": LaunchConfiguration("publish_joint_states")},
                {"joint_state_topic": LaunchConfiguration("joint_state_topic")},
                {"joint_name": LaunchConfiguration("joint_name")},
                {"joint_prefix": LaunchConfiguration("joint_prefix")},
                {"joint_open_position": LaunchConfiguration("joint_open_position")},
                {"joint_closed_position": LaunchConfiguration("joint_closed_position")},
            ],
            output="screen",
        ),
        Node(
            package="bringup_gripper",
            executable="joint_state_merger",
            name="JointStateMerger",
            condition=IfCondition(LaunchConfiguration("joint_state_merger")),
            parameters=[
                {"robot_joint_states_topic": LaunchConfiguration("robot_joint_states_topic")},
                {"gripper_joint_states_topic": LaunchConfiguration("joint_state_topic")},
                {"output_topic": LaunchConfiguration("merged_joint_states_topic")},
            ],
            output="screen",
        ),
        Node(
            package="bringup_gripper",
            executable="onrobot_rg_gripper_command_action",
            name="OnRobotRGGripperCommandAction",
            condition=IfCondition(LaunchConfiguration("gripper_command_action")),
            parameters=[
                {"action_name": LaunchConfiguration("gripper_command_action_name")},
                {"use_joint_position_commands": LaunchConfiguration("gripper_command_joint_mode")},
                {"command_topic": LaunchConfiguration("gripper_command_topic")},
                {"status_topic": LaunchConfiguration("gripper_status_topic")},
                {"gripper": LaunchConfiguration("gripper")},
                {"joint_open_position": LaunchConfiguration("joint_open_position")},
                {"joint_closed_position": LaunchConfiguration("joint_closed_position")},
                {"default_force_n": LaunchConfiguration("gripper_default_force_n")},
                {"max_force_n": LaunchConfiguration("gripper_command_max_force_n")},
                {"stop_first": LaunchConfiguration("gripper_command_stop_first")},
                {"motion_timeout_sec": LaunchConfiguration("gripper_command_motion_timeout_sec")},
                {"goal_tolerance_mm": LaunchConfiguration("gripper_command_goal_tolerance_mm")},
            ],
            output="screen",
        ),
        Node(
            package="bringup_gripper",
            executable="onrobot_rg_status_listener",
            name="OnRobotRGStatusListener",
            condition=IfCondition(LaunchConfiguration("status_listener")),
            output="screen",
        ),
    ])
