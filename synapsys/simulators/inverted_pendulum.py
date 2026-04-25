"""Inverted pendulum on a fixed pivot (no cart).

State:  x = [θ, θ̇]
  θ  — angle from UPRIGHT vertical (rad).  θ=0 → balanced (unstable).
  θ̇  — angular velocity (rad/s).

Input:  u = [τ]   torque at pivot (N·m).

Output: y = [θ]   — angle only (angular velocity is latent).

Equation of motion (point mass m at tip, pivot friction b):
  m·l²·θ̈ = τ − b·θ̇ + m·g·l·sin(θ)

  (gravity term +sin(θ): positive θ → gravity pulls further away from upright)

State-space (nonlinear):
  ẋ₁ = x₂
  ẋ₂ = (g/l)·sin(x₁) − (b/(m·l²))·x₂ + τ/(m·l²)

Analytical linearisation at upright equilibrium (θ=0, τ=0):
  A = [[0,          1       ],
       [g/l,  −b/(m·l²)    ]]

  B = [[      0     ],
       [1/(m·l²)    ]]

  C = [[1, 0]]
  D = [[0]]

Eigenvalues of A (b=0): ±√(g/l) → system is inherently unstable.
"""

from __future__ import annotations

import threading
from typing import Any, Literal

import numpy as np
from numpy import ndarray

from .base import SimulatorBase


class InvertedPendulumSim(SimulatorBase):
    """Inverted pendulum on a fixed pivot.

    Args:
        m: Point mass at pole tip (kg).
        l: Pole length (m).
        g: Gravitational acceleration (m/s²).
        b: Viscous friction at pivot (N·m·s/rad).  Default 0 (frictionless).
        integrator: 'euler', 'rk4' (default) or 'rk45'.
        noise_std: Std-dev of Gaussian noise added to angle output.
        disturbance_std: Std-dev of Gaussian disturbance added to torque.
    """

    def __init__(
        self,
        m: float = 1.0,
        l: float = 1.0,
        g: float = 9.81,
        b: float = 0.0,
        integrator: Literal["euler", "rk4", "rk45"] = "rk4",
        noise_std: float = 0.0,
        disturbance_std: float = 0.0,
    ) -> None:
        self._m = float(m)
        self._l = float(l)
        self._g = float(g)
        self._b = float(b)
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
            m, l, g, b = self._m, self._l, self._g, self._b

        theta, theta_dot = x
        tau = u[0]
        I = m * l**2
        theta_ddot = (g / l) * np.sin(theta) - (b / I) * theta_dot + tau / I
        return np.array([theta_dot, theta_ddot])

    def output(self, x: ndarray) -> ndarray:
        return np.array([x[0]])

    def failed(self, x: ndarray) -> bool:
        return bool(abs(x[0]) > np.pi / 2)

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

        Accepted keys: m, l, g, b.
        """
        valid = {"m", "l", "g", "b"}
        unknown = set(kwargs) - valid
        if unknown:
            raise ValueError(f"Unknown parameters: {unknown}. Valid: {valid}")
        with self._params_lock:
            if "m" in kwargs:
                self._m = float(kwargs["m"])
            if "l" in kwargs:
                self._l = float(kwargs["l"])
            if "g" in kwargs:
                self._g = float(kwargs["g"])
            if "b" in kwargs:
                self._b = float(kwargs["b"])

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def params(self) -> dict[str, float]:
        with self._params_lock:
            return dict(m=self._m, l=self._l, g=self._g, b=self._b)

    def unstable_pole(self) -> float:
        """Open-loop unstable eigenvalue: +√(g/l) (rad/s)."""
        with self._params_lock:
            return float(np.sqrt(self._g / self._l))
