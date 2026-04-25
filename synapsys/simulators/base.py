from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import Any, Literal

import numpy as np
from numpy import ndarray

from synapsys.core.state_space import StateSpace

from .integrators import euler, rk4, rk45

_INTEGRATORS = {"euler": euler, "rk4": rk4, "rk45": rk45}

_EPS = 1e-5  # finite-difference step for numerical Jacobian


class SimulatorBase(ABC):
    """Abstract base for nonlinear continuous-time simulators.

    Subclasses must implement: dynamics, output, reset, set_params.
    The base provides: step (integration + noise), linearize (numerical Jacobian).
    """

    def __init__(
        self,
        integrator: Literal["euler", "rk4", "rk45"] = "rk4",
        noise_std: float = 0.0,
        disturbance_std: float = 0.0,
    ) -> None:
        if integrator not in _INTEGRATORS:
            raise ValueError(
                f"integrator must be one of {list(_INTEGRATORS)}, got '{integrator}'"
            )
        self._integrate = _INTEGRATORS[integrator]
        self._noise_std = float(noise_std)
        self._disturbance_std = float(disturbance_std)
        self._lock = threading.Lock()
        self._x: ndarray = np.zeros(self.state_dim)

    # ------------------------------------------------------------------
    # Abstract interface — subclasses must implement
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def state_dim(self) -> int:
        """Number of state variables."""

    @property
    @abstractmethod
    def input_dim(self) -> int:
        """Number of inputs (actuators)."""

    @property
    @abstractmethod
    def output_dim(self) -> int:
        """Number of outputs (sensors)."""

    @abstractmethod
    def dynamics(self, x: ndarray, u: ndarray) -> ndarray:
        """Continuous-time dynamics: ẋ = f(x, u)."""

    @abstractmethod
    def output(self, x: ndarray) -> ndarray:
        """Output map: y = h(x)."""

    @abstractmethod
    def reset(self, **kwargs: Any) -> ndarray:
        """Reset state to initial condition, return first observation y₀."""

    @abstractmethod
    def set_params(self, **kwargs: Any) -> None:
        """Thread-safe runtime parameter update (e.g. mass, length)."""

    # ------------------------------------------------------------------
    # Provided by base
    # ------------------------------------------------------------------

    @property
    def state(self) -> ndarray:
        return self._x.copy()  # type: ignore[no-any-return]

    def step(self, u: ndarray, dt: float) -> tuple[ndarray, dict]:
        """Advance simulation by dt seconds.

        Args:
            u: Control input, shape (input_dim,).
            dt: Integration step in seconds.

        Returns:
            y: Observation vector, shape (output_dim,).
            info: Dict with 'x' (full state copy) and 't_step' = dt.
        """
        u = np.asarray(u, dtype=float).ravel()
        if u.shape[0] != self.input_dim:
            raise ValueError(f"Expected input_dim={self.input_dim}, got {u.shape[0]}")

        with self._lock:
            u_eff = u.copy()
            if self._disturbance_std > 0.0:
                u_eff = u_eff + np.random.normal(
                    0.0, self._disturbance_std, u_eff.shape
                )

            self._x = self._integrate(self.dynamics, self._x, u_eff, dt)

            y = self.output(self._x)
            if self._noise_std > 0.0:
                y = y + np.random.normal(0.0, self._noise_std, y.shape)

        return y, {"x": self._x.copy(), "t_step": dt}

    def linearize(self, x0: ndarray, u0: ndarray) -> StateSpace:
        """Numerical linearization around equilibrium (x0, u0).

        Uses central finite differences to compute A, B, C, D matrices and
        returns a continuous-time Synapsys StateSpace.
        """
        x0 = np.asarray(x0, dtype=float).ravel()
        u0 = np.asarray(u0, dtype=float).ravel()
        n, m = self.state_dim, self.input_dim
        p = self.output_dim

        A = np.zeros((n, n))
        for i in range(n):
            xp, xm = x0.copy(), x0.copy()
            xp[i] += _EPS
            xm[i] -= _EPS
            A[:, i] = (self.dynamics(xp, u0) - self.dynamics(xm, u0)) / (2 * _EPS)

        B = np.zeros((n, m))
        for j in range(m):
            up, um = u0.copy(), u0.copy()
            up[j] += _EPS
            um[j] -= _EPS
            B[:, j] = (self.dynamics(x0, up) - self.dynamics(x0, um)) / (2 * _EPS)

        C = np.zeros((p, n))
        for i in range(n):
            xp, xm = x0.copy(), x0.copy()
            xp[i] += _EPS
            xm[i] -= _EPS
            C[:, i] = (self.output(xp) - self.output(xm)) / (2 * _EPS)

        D = np.zeros((p, m))

        return StateSpace(A, B, C, D, dt=0.0)
