import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/luca/Stage_Lirmm/Diffusion-model-isaacsim/ur10_real_robot/ros2_ws_luca/install/bringup_gripper'
