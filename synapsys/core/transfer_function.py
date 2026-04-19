from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy import signal

from .lti import LTIModel

if TYPE_CHECKING:
    from .state_space import StateSpace


class TransferFunction(LTIModel):
    """
    SISO transfer function.

    Continuous (dt=0):  G(s) = num(s) / den(s)
    Discrete   (dt>0):  H(z) = num(z) / den(z)

    Args:
        dt: Sample period in seconds.  0 (default) → continuous-time.
    """

    def __init__(self, num: object, den: object, dt: float = 0.0):
        self._num = LTIModel._as_1d(num)
        self._den = LTIModel._as_1d(den)
        self._dt = float(dt)
        if self._den.size == 0:
            raise ValueError("Denominator cannot be empty.")
        if self._den[0] == 0:
            raise ValueError("Leading denominator coefficient cannot be zero.")
        if self._dt < 0:
            raise ValueError(f"dt must be >= 0, got {self._dt}")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def num(self) -> np.ndarray:
        return self._num

    @property
    def den(self) -> np.ndarray:
        return self._den

    @property
    def dt(self) -> float:
        return self._dt

    @property
    def is_discrete(self) -> bool:
        return self._dt > 0.0

    @property
    def n_states(self) -> int:
        return len(self._den) - 1

    @property
    def n_inputs(self) -> int:
        return 1

    @property
    def n_outputs(self) -> int:
        return 1

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def poles(self) -> np.ndarray:
        return np.roots(self._den)

    def zeros(self) -> np.ndarray:
        return np.roots(self._num) if len(self._num) > 1 else np.array([])

    def is_stable(self) -> bool:
        p = self.poles()
        if self.is_discrete:
            return bool(np.all(np.abs(p) < 1.0))
        return bool(np.all(np.real(p) < 0.0))

    def evaluate(self, s: complex) -> complex:
        """Evaluate G(s) or H(z) at a point in the complex plane."""
        return complex(np.polyval(self._num, s) / np.polyval(self._den, s))

    # ------------------------------------------------------------------
    # Conversions
    # ------------------------------------------------------------------

    def to_transfer_function(self) -> TransferFunction:
        return self

    def to_state_space(self) -> StateSpace:
        from .state_space import StateSpace

        if self.is_discrete:
            sys = signal.dlti(self._num, self._den, dt=self._dt)
            ss = sys.to_ss()
        else:
            sys = signal.TransferFunction(self._num, self._den)
            ss = sys.to_ss()
        return StateSpace(ss.A, ss.B, ss.C, ss.D, dt=self._dt)

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def step(
        self,
        t: np.ndarray | None = None,
        n: int = 200,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Step response.  For discrete systems, n sets the number of samples."""
        if self.is_discrete:
            sys = signal.dlti(self._num, self._den, dt=self._dt)
            t_out, y_seqs = signal.dstep(sys, n=n)
            return t_out, np.squeeze(y_seqs[0])
        sys = signal.TransferFunction(self._num, self._den)
        t_out, y_out = signal.step(sys, T=t)
        return t_out, y_out

    def evolve(self, x: np.ndarray, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Advance one discrete step.

        Delegates to the equivalent ``StateSpace`` representation.
        The state vector ``x`` must match the order of the converted state space
        (i.e. the controllable canonical form used by ``to_state_space()``).

        Returns
        -------
        x_next, y : np.ndarray
        """
        return self.to_state_space().evolve(x, u)

    def simulate(
        self,
        t: np.ndarray,
        u: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Simulate response to arbitrary input signal ``u`` over time ``t``.

        Delegates to ``StateSpace.simulate`` after converting internally.

        Returns
        -------
        t_out, y_out : np.ndarray
        """
        return self.to_state_space().simulate(t, u)

    def bode(
        self, omega: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bode diagram. Returns (omega [rad/s], magnitude [dB], phase [deg])."""
        if self.is_discrete:
            sys = signal.dlti(self._num, self._den, dt=self._dt)
            w, mag, phase = signal.dbode(sys, w=omega)
        else:
            sys = signal.TransferFunction(self._num, self._den)
            w, mag, phase = signal.bode(sys, w=omega)
        return w, mag, phase

    # ------------------------------------------------------------------
    # Algebra (operator overloading)
    # ------------------------------------------------------------------

    def _check_compatible(self, other: TransferFunction) -> None:
        if self._dt != other._dt:
            raise ValueError(
                f"Cannot combine systems with different sample times "
                f"({self._dt} vs {other._dt})."
            )

    def __add__(self, other: TransferFunction) -> TransferFunction:
        """Parallel connection."""
        if not isinstance(other, TransferFunction):
            other = other.to_transfer_function()
        self._check_compatible(other)
        num = np.polyadd(
            np.polymul(self._num, other._den),
            np.polymul(other._num, self._den),
        )
        den = np.polymul(self._den, other._den)
        return TransferFunction(num, den, dt=self._dt)

    def __mul__(self, other: TransferFunction) -> TransferFunction:
        """Series connection."""
        if not isinstance(other, TransferFunction):
            other = other.to_transfer_function()
        self._check_compatible(other)
        return TransferFunction(
            np.polymul(self._num, other._num),
            np.polymul(self._den, other._den),
            dt=self._dt,
        )

    def __truediv__(self, other: TransferFunction) -> TransferFunction:
        if not isinstance(other, TransferFunction):
            other = other.to_transfer_function()
        self._check_compatible(other)
        return TransferFunction(
            np.polymul(self._num, other._den),
            np.polymul(self._den, other._num),
            dt=self._dt,
        )

    def __neg__(self) -> TransferFunction:
        return TransferFunction(-self._num, self._den, dt=self._dt)

    def feedback(self, sensor: TransferFunction | None = None) -> TransferFunction:
        """Closed-loop T = G / (1 + G*H) with negative feedback."""
        H = sensor if sensor is not None else TransferFunction([1], [1], dt=self._dt)
        # T = G / (1 + G*H) = N_G * D_H / (D_G*D_H + N_G*N_H)
        num = np.polymul(self._num, H._den)
        den = np.polyadd(
            np.polymul(self._den, H._den),
            np.polymul(self._num, H._num),
        )
        return TransferFunction(num, den, dt=self._dt)

    def __repr__(self) -> str:
        domain = f"dt={self._dt}" if self.is_discrete else "continuous"
        return (
            f"TransferFunction(num={self._num.tolist()}, "
            f"den={self._den.tolist()}, {domain})"
        )
