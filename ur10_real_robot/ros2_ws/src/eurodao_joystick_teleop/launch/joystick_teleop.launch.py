import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_dir = get_package_share_directory('eurodao_joystick_teleop')
    config_file = os.path.join(pkg_dir, 'config', 'joystick_teleop.yaml')

    teleop_node = Node(
        package='eurodao_joystick_teleop',
        executable='joystick_teleop_node',
        name='joystick_teleop',
        parameters=[config_file],
        output='screen',
    )

    return LaunchDescription([teleop_node])
