from __future__ import annotations

import numpy as np


class PID:
    """Discrete-time PID controller with output saturation and anti-windup."""

    def __init__(
        self,
        Kp: float,
        Ki: float = 0.0,
        Kd: float = 0.0,
        dt: float = 0.01,
        u_min: float = -np.inf,
        u_max: float = np.inf,
    ):
        if dt <= 0.0:
            raise ValueError(f"dt must be > 0, got {dt}")
        if u_min >= u_max:
            raise ValueError(f"u_min ({u_min}) must be < u_max ({u_max})")
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt
        self.u_min = u_min
        self.u_max = u_max
        self._integral = 0.0
        self._prev_error = 0.0

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_error = 0.0

    def compute(self, setpoint: float, measurement: float) -> float:
        error = setpoint - measurement
        self._integral += error * self.dt
        derivative = (error - self._prev_error) / self.dt

        u = self.Kp * error + self.Ki * self._integral + self.Kd * derivative
        u_sat = float(np.clip(u, self.u_min, self.u_max))

        # Anti-windup: back-calculation
        if self.Ki != 0:
            self._integral += (u_sat - u) / self.Ki

        self._prev_error = error
        return u_sat

    def __repr__(self) -> str:
        from synapsys.utils._fmt import _g, box

        sat_lo = "-inf" if self.u_min == -np.inf else _g(self.u_min)
        sat_hi = "+inf" if self.u_max == np.inf else _g(self.u_max)
        lines = [
            f"Kp  : {_g(self.Kp)}",
            f"Ki  : {_g(self.Ki)}",
            f"Kd  : {_g(self.Kd)}",
            f"dt  : {_g(self.dt)} s",
            f"sat : [{sat_lo}, {sat_hi}]",
        ]
        return box("PID", lines)
