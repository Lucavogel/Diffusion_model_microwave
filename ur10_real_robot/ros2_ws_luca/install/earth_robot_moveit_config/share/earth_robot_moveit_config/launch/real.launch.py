from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare

from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    robot_ip = LaunchConfiguration("robot_ip")
    ur_type = LaunchConfiguration("ur_type")
    launch_moveit_rviz = LaunchConfiguration("launch_moveit_rviz")
    headless_mode = LaunchConfiguration("headless_mode")
    launch_gripper = LaunchConfiguration("launch_gripper")
    joint_state_merger = LaunchConfiguration("joint_state_merger")
    robot_joint_states_topic = LaunchConfiguration("robot_joint_states_topic")
    merged_joint_states_topic = LaunchConfiguration("merged_joint_states_topic")
    gripper_default_force_n = LaunchConfiguration("gripper_default_force_n")
    gripper_command_max_force_n = LaunchConfiguration(
        "gripper_command_max_force_n"
    )
    activate_joint_controller_on_startup = LaunchConfiguration(
        "activate_joint_controller_on_startup"
    )

    moveit_config = MoveItConfigsBuilder(
        "ur10_d455_support_rg2ft",
        package_name="earth_robot_moveit_config",
    ).to_moveit_configs()

    driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [
                    FindPackageShare("realsense2_description"),
                    "launch",
                    "ur10_d455_support_rg2ft_driver.launch.py",
                ]
            )
        ),
        launch_arguments={
            "robot_ip": robot_ip,
            "ur_type": ur_type,
            "launch_rviz": "false",
            "headless_mode": headless_mode,
            "activate_joint_controller_on_startup": activate_joint_controller_on_startup,
        }.items(),
    )

    gripper_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("bringup_gripper"), "bringup.launch.py"]
            )
        ),
        condition=IfCondition(launch_gripper),
        launch_arguments={
            "joint_prefix": "gripper_",
            "joint_state_topic": "gripper_joint_states",
            "joint_state_merger": joint_state_merger,
            "robot_joint_states_topic": robot_joint_states_topic,
            "merged_joint_states_topic": merged_joint_states_topic,
            "gripper_command_action": "true",
            "gripper_command_action_name": "gripper_action_controller/gripper_cmd",
            "gripper_default_force_n": gripper_default_force_n,
            "gripper_command_max_force_n": gripper_command_max_force_n,
        }.items(),
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {
                "publish_robot_description_semantic": True,
            },
        ],
    )

    rviz_node = Node(
        package="rviz2",
        condition=IfCondition(launch_moveit_rviz),
        executable="rviz2",
        name="rviz2_moveit",
        output="log",
        arguments=[
            "-d",
            PathJoinSubstitution(
                [FindPackageShare("earth_robot_moveit_config"), "config", "moveit.rviz"]
            ),
        ],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_ip", default_value="192.168.21.128"),
            DeclareLaunchArgument("ur_type", default_value="ur10"),
            DeclareLaunchArgument("launch_moveit_rviz", default_value="true"),
            DeclareLaunchArgument("headless_mode", default_value="false"),
            DeclareLaunchArgument("launch_gripper", default_value="true"),
            DeclareLaunchArgument("joint_state_merger", default_value="true"),
            DeclareLaunchArgument(
                "robot_joint_states_topic",
                default_value="/joint_state_broadcaster/joint_states",
            ),
            DeclareLaunchArgument(
                "merged_joint_states_topic", default_value="/joint_states"
            ),
            DeclareLaunchArgument("gripper_default_force_n", default_value="40.0"),
            DeclareLaunchArgument(
                "gripper_command_max_force_n", default_value="40.0"
            ),
            DeclareLaunchArgument(
                "activate_joint_controller_on_startup", default_value="false"
            ),
            driver_launch,
            gripper_launch,
            TimerAction(period=3.0, actions=[move_group_node, rviz_node]),
        ]
    )
