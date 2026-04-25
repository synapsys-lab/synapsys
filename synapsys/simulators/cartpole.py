"""Cart-pole simulator.

State:  x = [p, ṗ, θ, θ̇]
  p  — cart position (m)
  ṗ  — cart velocity (m/s)
  θ  — pole angle from upright / vertical  (rad, θ=0 → balanced)
  θ̇  — pole angular velocity (rad/s)

Input:  u = [F]   horizontal force on cart (N)

Output: y = [p, θ]   — partial observation (no velocities)

Dynamics (Lagrangian, point mass at pole tip):

  Δ  = m_c + m_p · sin²(θ)
  p̈  = [F + m_p · sin(θ) · (l · θ̇² − g · cos(θ))] / Δ
  θ̈  = [g · sin(θ) − p̈ · cos(θ)] / l

Linearised around (θ=0, θ̇=0, ṗ=0, F=0):

  A = [[0,  1,                0, 0],
       [0,  0,   -m_p·g/m_c,   0],
       [0,  0,                0, 1],
       [0,  0,  (m_c+m_p)·g/(m_c·l), 0]]

  B = [[0], [1/m_c], [0], [-1/(m_c·l)]]
  C = [[1, 0, 0, 0], [0, 0, 1, 0]]
  D = [[0], [0]]
"""

from __future__ import annotations

import threading
from typing import Any, Literal

import numpy as np
from numpy import ndarray

from .base import SimulatorBase

_DEFAULT_PARAMS = dict(m_c=1.0, m_p=0.1, l=0.5, g=9.81)


class CartPoleSim(SimulatorBase):
    """Nonlinear cart-pole simulator with configurable physical parameters.

    Args:
        m_c: Cart mass (kg).
        m_p: Pole tip mass (kg).
        l: Pole length (m).
        g: Gravitational acceleration (m/s²).
        integrator: 'euler', 'rk4' (default) or 'rk45'.
        noise_std: Std-dev of Gaussian sensor noise added to y.
        disturbance_std: Std-dev of Gaussian disturbance added to u.
    """

    def __init__(
        self,
        m_c: float = 1.0,
        m_p: float = 0.1,
        l: float = 0.5,
        g: float = 9.81,
        integrator: Literal["euler", "rk4", "rk45"] = "rk4",
        noise_std: float = 0.0,
        disturbance_std: float = 0.0,
        linearised: bool = False,
    ) -> None:
        self._m_c = float(m_c)
        self._m_p = float(m_p)
        self._l = float(l)
        self._g = float(g)
        self._linearised = bool(linearised)
        self._params_lock = threading.Lock()
        super().__init__(
            integrator=integrator, noise_std=noise_std, disturbance_std=disturbance_std
        )

    @property
    def linearised(self) -> bool:
        return self._linearised

    # ------------------------------------------------------------------
    # Abstract properties
    # ------------------------------------------------------------------

    @property
    def state_dim(self) -> int:
        return 4

    @property
    def input_dim(self) -> int:
        return 1

    @property
    def output_dim(self) -> int:
        return 2

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    def dynamics(self, x: ndarray, u: ndarray) -> ndarray:
        with self._params_lock:
            m_c, m_p, l, g = self._m_c, self._m_p, self._l, self._g

        _, p_dot, theta, theta_dot = x
        F = u[0]

        if self._linearised:
            # Linearised around (θ=0, ṗ=0, θ̇=0, F=0)
            p_ddot = F / m_c - m_p * g * theta / m_c
            theta_ddot = (m_c + m_p) * g * theta / (m_c * l) - F / (m_c * l)
            return np.array([p_dot, p_ddot, theta_dot, theta_ddot])

        sin_t = np.sin(theta)
        cos_t = np.cos(theta)
        delta = m_c + m_p * sin_t**2

        p_ddot = (F + m_p * sin_t * (l * theta_dot**2 - g * cos_t)) / delta
        theta_ddot = (g * sin_t - p_ddot * cos_t) / l

        return np.array([p_dot, p_ddot, theta_dot, theta_ddot])

    def output(self, x: ndarray) -> ndarray:
        return np.array([x[0], x[2]])

    def failed(self, x: ndarray) -> bool:
        p, _, theta, _ = x
        return bool(abs(p) > 4.8 or abs(theta) > np.pi / 3)

    def reset(self, x0: ndarray | None = None, **kwargs: Any) -> ndarray:
        if x0 is not None:
            self._x = np.asarray(x0, dtype=float).ravel()
            if self._x.shape[0] != 4:
                raise ValueError(f"x0 must have length 4, got {self._x.shape[0]}")
        else:
            self._x = np.zeros(4)
        return self.output(self._x)

    def set_params(self, **kwargs: Any) -> None:
        """Thread-safe update of physical parameters.

        Accepted keys: m_c, m_p, l, g.
        """
        valid = {"m_c", "m_p", "l", "g"}
        unknown = set(kwargs) - valid
        if unknown:
            raise ValueError(f"Unknown parameters: {unknown}. Valid: {valid}")
        with self._params_lock:
            if "m_c" in kwargs:
                self._m_c = float(kwargs["m_c"])
            if "m_p" in kwargs:
                self._m_p = float(kwargs["m_p"])
            if "l" in kwargs:
                self._l = float(kwargs["l"])
            if "g" in kwargs:
                self._g = float(kwargs["g"])

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def params(self) -> dict[str, float]:
        with self._params_lock:
            return dict(m_c=self._m_c, m_p=self._m_p, l=self._l, g=self._g)
