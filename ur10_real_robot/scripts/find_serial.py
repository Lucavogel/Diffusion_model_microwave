
#Top down serial number : 332322072359

import pyrealsense2 as rs

ctx = rs.context()
devices = ctx.query_devices()

if len(devices) == 0:
    print("No RealSense camera detected.")

for i, dev in enumerate(devices):
    print(f"\nCamera {i}")
    print("Name:", dev.get_info(rs.camera_info.name))
    print("Serial:", dev.get_info(rs.camera_info.serial_number))



