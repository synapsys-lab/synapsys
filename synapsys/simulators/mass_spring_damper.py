"""Mass-spring-damper simulator (1-DOF, linear).

State:  x = [q, q̇]
  q  — displacement (m)
  q̇  — velocity (m/s)

Input:  u = [F]   external force (N)

Output: y = [q]   — position only (velocity is latent)

Equation of motion:
  m·q̈ + c·q̇ + k·q = F

State-space (exact — the system is linear):
  ẋ = A·x + B·u
  y = C·x

  A = [[0,    1  ],
       [-k/m, -c/m]]

  B = [[0  ],
       [1/m]]

  C = [[1, 0]]
  D = [[0]]

Because the system is linear, linearize() returns the same A, B, C, D matrices
at every operating point.
"""

from __future__ import annotations

import threading
from typing import Any, Literal

import numpy as np
from numpy import ndarray

from .base import SimulatorBase


class MassSpringDamperSim(SimulatorBase):
    """Nonlinear wrapper around the classic 1-DOF mass-spring-damper.

    Even though the dynamics are linear this simulator deliberately uses the
    nonlinear SimulatorBase path so that the numerical linearize() can be
    validated against the known analytical result.

    Args:
        m: Mass (kg).
        c: Damping coefficient (N·s/m).
        k: Spring stiffness (N/m).
        integrator: 'euler', 'rk4' (default) or 'rk45'.
        noise_std: Std-dev of Gaussian noise added to position output.
        disturbance_std: Std-dev of Gaussian disturbance added to input force.
    """

    def __init__(
        self,
        m: float = 1.0,
        c: float = 0.5,
        k: float = 2.0,
        integrator: Literal["euler", "rk4", "rk45"] = "rk4",
        noise_std: float = 0.0,
        disturbance_std: float = 0.0,
    ) -> None:
        self._m = float(m)
        self._c = float(c)
        self._k = float(k)
        self._params_lock = threading.Lock()
        super().__init__(
            integrator=integrator, noise_std=noise_std, disturbance_std=disturbance_std
        )

    # ------------------------------------------------------------------
    # Abstract properties
    # ------------------------------------------------------------------

    @property
    def state_dim(self) -> int:
        return 2

    @property
    def input_dim(self) -> int:
        return 1

    @property
    def output_dim(self) -> int:
        return 1

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    def dynamics(self, x: ndarray, u: ndarray) -> ndarray:
        with self._params_lock:
            m, c, k = self._m, self._c, self._k
        q, q_dot = x
        F = u[0]
        q_ddot = (F - c * q_dot - k * q) / m
        return np.array([q_dot, q_ddot])

    def output(self, x: ndarray) -> ndarray:
        return np.array([x[0]])

    def reset(self, x0: ndarray | None = None, **kwargs: Any) -> ndarray:
        if x0 is not None:
            self._x = np.asarray(x0, dtype=float).ravel()
            if self._x.shape[0] != 2:
                raise ValueError(f"x0 must have length 2, got {self._x.shape[0]}")
        else:
            self._x = np.zeros(2)
        return self.output(self._x)

    def set_params(self, **kwargs: Any) -> None:
        """Thread-safe update of physical parameters.

        Accepted keys: m, c, k.
        """
        valid = {"m", "c", "k"}
        unknown = set(kwargs) - valid
        if unknown:
            raise ValueError(f"Unknown parameters: {unknown}. Valid: {valid}")
        with self._params_lock:
            if "m" in kwargs:
                self._m = float(kwargs["m"])
            if "c" in kwargs:
                self._c = float(kwargs["c"])
            if "k" in kwargs:
                self._k = float(kwargs["k"])

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def params(self) -> dict[str, float]:
        with self._params_lock:
            return dict(m=self._m, c=self._c, k=self._k)

    def natural_frequency(self) -> float:
        """Undamped natural frequency ωₙ = √(k/m) (rad/s)."""
        with self._params_lock:
            return float(np.sqrt(self._k / self._m))

    def damping_ratio(self) -> float:
        """Damping ratio ζ = c / (2·√(m·k))."""
        with self._params_lock:
            return float(self._c / (2.0 * np.sqrt(self._m * self._k)))
