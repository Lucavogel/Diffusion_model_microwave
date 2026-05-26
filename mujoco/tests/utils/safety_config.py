from dataclasses import dataclass
import logging
import numpy as np


@dataclass
class SafetyConfig:
    safety_velocity: float = 0.8
    safety_acceleration: float = 10.0
    jacobian_threshold: float = 700.0
    # Jacobian / condition thresholds
    
    cond_threshold_stop: float = 1000.0
    manip_threshold_stop: float = 1e-6

   
    velocity_stop_threshold: float = 1.0
    
    acceleration_stop_threshold: float = 70.0
    #TODO needs to be changed on real robot
    acceleration_emergency_threshold: float = 100.0
    acceleration_filter_window: int = 5
    acceleration_emergency_consecutive: int = 3

    # hysteresis / consecutive cycle counts
    # Increase consecutive stop count to make the checker less sensitive to short spikes
    consecutive_stop_count: int = 8
    consecutive_recover_count: int = 5
    # metrics history size
    metrics_history_size: int = 200


class SafetyChecker:
    def __init__(self, config = None, q = None):
        # use provided config or defaults
        self.config = config or SafetyConfig()

        # number of joints we expect to monitor (default to 6 for UR10e)
        self.n_joints = len(q) if q is not None else 6

        # hysteresis / consecutive counts to avoid noisy triggers
        self.consec_violations = 0
        self.hysteresis_stop_count = getattr(self.config, 'consecutive_stop_count', 3)
        self.hysteresis_recover_count = getattr(self.config, 'consecutive_recover_count', 5)

        # history buffer for short-term smoothing of metrics
        self._metrics_history = []
        self._acc_history = []
        self._acc_emergency_count = 0
        self._recover_streak = 0

        # logger
        self._logger = logging.getLogger(__name__)

        # last decision made by the checker ('ok','stop')
        self.last_decision = 'ok'

    def check_velocity(self, qvel):
        # handle missing or empty input safely
        if qvel is None:
            return True
        qvel = np.asarray(qvel)
        if qvel.size == 0:
            return True
        max_vel = float(np.max(np.abs(qvel[:self.n_joints])))
        return max_vel < float(self.config.velocity_stop_threshold)
        

    def check_acceleration(self, qacc):
        if qacc is None:
            self._acc_emergency_count = 0
            return True 
        qacc = np.asarray(qacc)
        if qacc.size == 0:
            self._acc_emergency_count = 0
            return True

        max_acc = float(np.max(np.abs(qacc[:self.n_joints])))

        # A single contact/release impulse is common in MuJoCo. Treat very high
        # spikes as emergency only if they persist across multiple cycles.
        if max_acc >= float(self.config.acceleration_emergency_threshold):
            self._acc_emergency_count += 1
            if self._acc_emergency_count >= int(getattr(self.config, "acceleration_emergency_consecutive", 3)):
                return False
        else:
            self._acc_emergency_count = 0

        self._acc_history.append(max_acc)
        window = max(1, int(getattr(self.config, "acceleration_filter_window", 5)))
        if len(self._acc_history) > window:
            self._acc_history = self._acc_history[-window:]

        filtered_acc = float(np.median(self._acc_history))
        if filtered_acc >= float(self.config.acceleration_stop_threshold):
            return False
        return True
    
    def check_jacobian(self, J):
        # returns True if jacobian condition and manipulability are OK
        if J is None:
            return True, {'cond': None, 'manip': None}

        J = np.asarray(J)
        # compute singular values (more robust than det)
        try:
            sv = np.linalg.svd(J, compute_uv=False)
        except np.linalg.LinAlgError as e:
            # numerical failure: treat as unsafe
            self._logger.warning("SVD failed on J: %s", e)
            return False, {'cond': float('inf'), 'manip': 0.0}

        if sv.size == 0:
            return False, {'cond': float('inf'), 'manip': 0.0}

        sigma_max = float(sv[0])
        sigma_min = float(sv[-1])
        # condition number (guard against zero division)
        cond = float('inf') if sigma_min == 0.0 else sigma_max / sigma_min
        # manipulability proxy: smallest singular value
        manip = sigma_min
        cond_ok = cond <= float(self.config.cond_threshold_stop)
        manip_ok = manip >= float(self.config.manip_threshold_stop)
        return (cond_ok and manip_ok), {'cond': cond, 'manip': manip}

        
    
    def check_loop(self, qvel, qacc, J):

        metrics = {}
        stop_reasons = []

        # velocity
        if qvel is None:
            vel_ok = True
            metrics["max_velocity"] = 0.0
        else:
            qvel = np.asarray(qvel)
            if qvel.size == 0:
                vel_ok = True
                metrics["max_velocity"] = 0.0
            else:
                vel_ok = self.check_velocity(qvel)
                metrics["max_velocity"] = float(np.max(np.abs(qvel[:self.n_joints])))
                if not vel_ok:
                    stop_reasons.append("velocity")
        metrics["velocity_ok"] = bool(vel_ok)

        # acceleration
        if qacc is None:
            acc_ok = True
            metrics["max_acceleration"] = 0.0
            metrics["filtered_acceleration"] = 0.0
        else:
            qacc = np.asarray(qacc)
            if qacc.size == 0:
                acc_ok = True
                metrics["max_acceleration"] = 0.0
                metrics["filtered_acceleration"] = 0.0
            else:
                acc_ok = self.check_acceleration(qacc)
                raw_acc = float(np.max(np.abs(qacc[:self.n_joints])))
                metrics["max_acceleration"] = raw_acc
                metrics["filtered_acceleration"] = float(np.median(self._acc_history)) if self._acc_history else raw_acc
                if not acc_ok:
                    stop_reasons.append("acceleration")
        metrics["acceleration_ok"] = bool(acc_ok)
        
        # jacobian (returns tuple)
        jacobian_ok, jac_metrics = self.check_jacobian(J)
        metrics["jacobian_ok"] = bool(jacobian_ok)
        if jac_metrics:
            metrics.update(jac_metrics)
            if not jacobian_ok:
                stop_reasons.append("jacobian")

        has_stop_condition = bool(stop_reasons) or (
            self._acc_emergency_count >= int(getattr(self.config, "acceleration_emergency_consecutive", 3))
        )

        if has_stop_condition:
            self.consec_violations += 1
            self._recover_streak = 0
            reason = ",".join(stop_reasons) if stop_reasons else "safety"
        else:
            self._recover_streak += 1
            if self._recover_streak >= self.hysteresis_recover_count:
                self.consec_violations = 0
                self._acc_emergency_count = 0
                self._acc_history.clear()
            reason = "ok"
        # record metrics history
        try:
            self._metrics_history.append(metrics)
            if len(self._metrics_history) > int(self.config.metrics_history_size):
                self._metrics_history.pop(0)
        except Exception:
            # never crash safety checker on metrics logging
            self._logger.exception("Failed to append metrics to history")

        if has_stop_condition and self.consec_violations >= self.hysteresis_stop_count:
            self.last_decision = 'stop'
            return {
                "status": "stop",
                "override": None,
                "reason": reason,
                "metrics": metrics
            }
        else:
            self.last_decision = 'ok'
            return {
                "status": "ok",
                "override": None,
                "reason": reason,
                "metrics": metrics
            }
            
        




                 
    