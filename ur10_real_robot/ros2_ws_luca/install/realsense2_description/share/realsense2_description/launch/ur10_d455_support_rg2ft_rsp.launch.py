from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    robot_ip = LaunchConfiguration("robot_ip")
    ur_type = LaunchConfiguration("ur_type")
    driver_rsp_launch = PathJoinSubstitution(
        [FindPackageShare("ur_robot_driver"), "launch", "ur_rsp.launch.py"]
    )
    description_file = PathJoinSubstitution(
        [FindPackageShare("realsense2_description"), "urdf", "ur10_d455_support_rg2ft_driver.urdf.xacro"]
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("robot_ip"),
            DeclareLaunchArgument("ur_type", default_value="ur10"),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(driver_rsp_launch),
                launch_arguments={
                    "robot_ip": robot_ip,
                    "ur_type": ur_type,
                    "description_file": description_file,
                }.items(),
            ),
        ]
    )
