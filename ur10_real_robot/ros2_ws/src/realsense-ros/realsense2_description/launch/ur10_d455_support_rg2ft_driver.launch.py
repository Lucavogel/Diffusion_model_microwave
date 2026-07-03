from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_ip = LaunchConfiguration("robot_ip")
    ur_type = LaunchConfiguration("ur_type")
    launch_rviz = LaunchConfiguration("launch_rviz")
    headless_mode = LaunchConfiguration("headless_mode")
    activate_joint_controller_on_startup = LaunchConfiguration(
        "activate_joint_controller_on_startup"
    )

    driver_launch = PathJoinSubstitution(
        [FindPackageShare("ur_robot_driver_cb2"), "launch", "ur_control.launch.py"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_ip", default_value="192.168.21.128"),
            DeclareLaunchArgument("ur_type", default_value="ur10"),
            DeclareLaunchArgument("launch_rviz", default_value="true"),
            DeclareLaunchArgument("headless_mode", default_value="false"),
            DeclareLaunchArgument(
                "activate_joint_controller_on_startup", default_value="false"
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(driver_launch),
                launch_arguments={
                    "robot_ip": robot_ip,
                    "ur_type": ur_type,
                    "launch_rviz": launch_rviz,
                    "headless_mode": headless_mode,
                    "activate_joint_controller_on_startup": activate_joint_controller_on_startup,
                    "runtime_config_package": "ur_robot_driver_cb2",
                    "description_package": "realsense2_description",
                    "description_file": "ur10_d455_support_rg2ft_driver.urdf.xacro",
                }.items(),
            ),
        ]
    )
