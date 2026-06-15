#!/bin/zsh
# Script pour lancer toute la stack Mujoco + Touch 3D + ROS2

# Terminal 1 : Simulation Mujoco (téléop)

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
python3 -m ur10_real_robot.run_real_teleop
') &

# Terminal 2 : ROS2 + Touch driver + RViz

(gnome-terminal -- zsh -c '
source /opt/ros/humble/setup.zsh
source ~/venvs/mujoco_ros/bin/activate
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ros2_WS
colcon build 
source install/setup.zsh
cd /home/luca/Stage_Lirmm/Diffusion-model-isaacsim
ros2 launch touch_ros2_driver touch_rviz.launch.py
') &



wait
