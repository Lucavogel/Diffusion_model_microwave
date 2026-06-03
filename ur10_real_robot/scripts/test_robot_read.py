from ur10_real_robot.backends import UR10UrxBackend



def main():

    ROBOT_IP = "192.168.0.60"

    robot = UR10UrxBackend(ROBOT_IP,enable_motion = False)

    try:
        robot.connect()

        state = robot.get_state()
        
        print(f"the robot is at joint position : {state['joint_positions']} rads")
        print(f"the robot is at joint velocity : {state['joint_velocities']} rad/s")
        print(f"the robot is at cartesian position : {state['eef_pos']} m")
        print(f"the robot is at cartesian orientation : {state['eef_quat']} (w,x,y,z)")
        print(f"the robot gripper is at position : {state['gripper_qpos']} rads")
    except Exception:
        raise RuntimeError("Not able to connect to the robot")



    finally:
        robot.close()
        print("connection to the robot was closed")


if __name__ == "__main__":
    main()