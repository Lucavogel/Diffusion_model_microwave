from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'bringup_gripper'
setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='gawlinski',
    maintainer_email='gawlinski.dorian@gmail.com',
    description='RG2-FT control Package',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
             'onrobot_rg_keyboard = bringup_gripper.OnRobotRGKeyboardController:main',
             'onrobot_rg_tcp_node = bringup_gripper.OnRobotRGTcpNode:main',
             'onrobot_rg_move = bringup_gripper.OnRobotRGMove:main',
             'onrobot_rg_gripper_command_action = bringup_gripper.OnRobotRGGripperCommandAction:main',
             'onrobot_rg_status_listener = bringup_gripper.OnRobotRGStatusListener:main',
             'onrobot_rg_simple_controller = bringup_gripper.OnRobotRGSimpleController:main',
             'joint_state_merger = bringup_gripper.JointStateMerger:main',
             'pick_place_sequence = bringup_gripper.PickPlaceSequence:main',

        ],
    },
)
