from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WatchdogStatus:
    status: str
    reason: str = ""
    age: float = 0.0
    dt: float = 0.0

    @property
    def should_stop(self) -> bool:
        return self.status == "stop"


class TouchTargetWatchdog:
    """Watch freshness of teleop targets coming from the Touch/ROS side."""

    def __init__(self, timeout: float = 0.30, enabled: bool = True) -> None:
        self.timeout = float(timeout)
        self.enabled = bool(enabled)
        self.last_target_time: float | None = None
        self.stop_active = False

    def mark_target_received(self, now: float) -> None:
        self.last_target_time = float(now)

    def reset_stop(self) -> None:
        self.stop_active = False

    def check(self, now: float) -> WatchdogStatus:
        if not self.enabled:
            return WatchdogStatus(status="ok")

        if self.last_target_time is None:
            return WatchdogStatus(status="waiting", reason="no target received yet")

        age = float(now) - self.last_target_time
        if age > self.timeout:
            self.stop_active = True
            return WatchdogStatus(
                status="stop",
                reason=f"no fresh Touch target for {age:.3f} s",
                age=age,
            )

        return WatchdogStatus(status="ok", age=age)

    def check_age(self, age: float | None) -> WatchdogStatus:
        if not self.enabled:
            return WatchdogStatus(status="ok")

        if age is None:
            return WatchdogStatus(status="waiting", reason="no target received yet")

        age = float(age)
        if age > self.timeout:
            self.stop_active = True
            return WatchdogStatus(
                status="stop",
                reason=f"no fresh Touch target for {age:.3f} s",
                age=age,
            )

        return WatchdogStatus(status="ok", age=age)


class ControlLoopWatchdog:
    """Watch whether the robot control loop is still running fast enough."""

    def __init__(
        self,
        expected_dt: float,
        warn_factor: float = 2.0,
        stop_factor: float = 5.0,
        stop_dt: float | None = None,
        enabled: bool = True,
    ) -> None:
        self.expected_dt = float(expected_dt)
        self.warn_dt = self.expected_dt * float(warn_factor)
        self.stop_dt = (
            float(stop_dt)
            if stop_dt is not None
            else self.expected_dt * float(stop_factor)
        )
        self.enabled = bool(enabled)

    def check(self, dt: float) -> WatchdogStatus:
        if not self.enabled:
            return WatchdogStatus(status="ok", dt=float(dt))

        dt = float(dt)
        if dt > self.stop_dt:
            return WatchdogStatus(
                status="stop",
                reason=f"control loop dt too high: {dt:.3f} s",
                dt=dt,
            )

        if dt > self.warn_dt:
            return WatchdogStatus(
                status="warn",
                reason=f"control loop dt warning: {dt:.3f} s",
                dt=dt,
            )

        return WatchdogStatus(status="ok", dt=dt)
