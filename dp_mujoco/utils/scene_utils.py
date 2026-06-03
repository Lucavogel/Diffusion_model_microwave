import numpy as np
import mujoco


import numpy as np

# Cache des rgba originaux pour pouvoir restaurer l'affichage
_geom_rgba_backup_by_body = {}

def rpy_to_quat_wxyz(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr = np.cos(roll / 2.0)
    sr = np.sin(roll / 2.0)
    cp = np.cos(pitch / 2.0)
    sp = np.sin(pitch / 2.0)
    cy = np.cos(yaw / 2.0)
    sy = np.sin(yaw / 2.0)

    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy

    return np.array([w, x, y, z], dtype=float)


def set_free_body_pose(model, data, body_name: str, pos: np.ndarray, quat_wxyz: np.ndarray):
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id == -1:
        raise ValueError(f"Body '{body_name}' introuvable")

    joint_id = model.body_jntadr[body_id]
    if joint_id < 0:
        raise ValueError(f"Body '{body_name}' n'a pas de joint associé")

    qpos_adr = model.jnt_qposadr[joint_id]
    qvel_adr = model.jnt_dofadr[joint_id]

    data.qpos[qpos_adr:qpos_adr+3] = pos
    data.qpos[qpos_adr+3:qpos_adr+7] = quat_wxyz
    data.qvel[qvel_adr:qvel_adr+6] = 0.0


def randomize_microwave_objects(model, data):
    # Utiliser un générateur local non-deterministe pour éviter
    # d'être influencé par un seed global (ex. lors du chargement du modèle)
    rng = np.random.default_rng()
   
    # -----------------------------
    # Objet 1 : microwave_rectangle
    # variation sur y seulement
    # -----------------------------
    rect_y = -0.33 + rng.uniform(-0.02, 0.02)
    rect_pos = np.array([0.9, rect_y, 0.58], dtype=float)

    rect_roll_choices = [0.0, 1.57]
    rect_roll = float(rng.choice(rect_roll_choices))
    rect_quat = rpy_to_quat_wxyz(0, rect_roll, 1.57)

    set_free_body_pose(
        model, data,
        "microwave_rectangle",
        rect_pos,
        rect_quat
    )

    # -----------------------------
    # Objet 2 : microwave_transformer
    # variation sur y seulement
    # orientation : 90° ou 180°
    # -----------------------------
    transf_y = -0.20 + rng.uniform(-0.02, 0.02)
    transf_pos = np.array([0.9, transf_y, 0.60], dtype=float)

   
    transf_quat = rpy_to_quat_wxyz(0, 0, 1.57)

    set_free_body_pose(
        model, data,
        "microwave_transformer",
        transf_pos,
        transf_quat
    )

    print(
        "[Randomize] microwave_rectangle pos=",
        rect_pos,
        "quat(wxyz)=",
        rect_quat,
        "| microwave_transformer pos=",
        transf_pos,
        "quat(wxyz)=",
        transf_quat,
    )

def hide_free_body(model, data, body_name: str):
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id == -1:
        raise ValueError(f"Body '{body_name}' introuvable")

    joint_id = model.body_jntadr[body_id]
    qpos_adr = model.jnt_qposadr[joint_id]
    qvel_adr = model.jnt_dofadr[joint_id]

    # position très loin
    data.qpos[qpos_adr:qpos_adr+3] = np.array([10.0, 10.0, 10.0], dtype=float)
    # quaternion identité
    data.qpos[qpos_adr+3:qpos_adr+7] = np.array([1.0, 0.0, 0.0, 0.0], dtype=float)

    # vitesse nulle
    data.qvel[qvel_adr:qvel_adr+6] = 0.0

    # Masquer visuellement les geoms attachés au body (alpha=0)
    try:
        geom_ids = np.where(model.geom_bodyid == body_id)[0]
        if geom_ids.size > 0:
            # sauvegarder les rgba originaux si besoin
            if body_name not in _geom_rgba_backup_by_body:
                _geom_rgba_backup_by_body[body_name] = {}
            for gid in geom_ids:
                if gid not in _geom_rgba_backup_by_body[body_name]:
                    try:
                        _geom_rgba_backup_by_body[body_name][gid] = model.geom_rgba[gid].copy()
                    except Exception:
                        _geom_rgba_backup_by_body[body_name][gid] = np.array([1.0, 1.0, 1.0, 1.0], dtype=float)
                # mettre alpha à 0
                try:
                    model.geom_rgba[gid, 3] = 0.0
                except Exception:
                    pass
    except Exception:
        # Ne pas planter si l'API du modèle n'expose ces tableaux
        pass


def show_free_body(model, data, body_name: str):
    """Restaure visuellement les geoms d'un body précédemment caché.

    Cette fonction restaure les valeurs RGBA sauvegardées dans
    `_geom_rgba_backup_by_body`. Si aucune sauvegarde n'existe, le alpha est
    mis à 1.0 par défaut.
    """
    body_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, body_name)
    if body_id == -1:
        return

    try:
        geom_ids = np.where(model.geom_bodyid == body_id)[0]
        if geom_ids.size > 0:
            backups = _geom_rgba_backup_by_body.get(body_name, {})
            for gid in geom_ids:
                if gid in backups:
                    try:
                        model.geom_rgba[gid] = backups[gid]
                    except Exception:
                        pass
                else:
                    try:
                        model.geom_rgba[gid, 3] = 1.0
                    except Exception:
                        pass
            # supprimer la sauvegarde
            if body_name in _geom_rgba_backup_by_body:
                del _geom_rgba_backup_by_body[body_name]
    except Exception:
        pass