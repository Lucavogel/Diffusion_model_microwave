import mujoco

urdf_path = "ur10_mujoco.urdf"
mjcf_path = "ur10_from_urdf.xml"

model = mujoco.MjModel.from_xml_path(urdf_path)

mujoco.mj_saveLastXML(mjcf_path, model)

print(f"Saved: {mjcf_path}")
print("nq:", model.nq)
print("nv:", model.nv)
print("nu:", model.nu)
print("njnt:", model.njnt)