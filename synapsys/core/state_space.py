from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy import linalg, signal

from .lti import LTIModel

if TYPE_CHECKING:
    from .transfer_function import TransferFunction


class StateSpace(LTIModel):
    """
    State-space model: dx/dt = Ax + Bu, y = Cx + Du  (continuous, dt=0)
                       x(k+1) = Ax(k) + Bu(k)        (discrete, dt>0)

    Args:
        dt: Sample period in seconds.  0 (default) → continuous-time.
    """

    def __init__(self, A: object, B: object, C: object, D: object, dt: float = 0.0):
        self._A = LTIModel._as_2d(A)
        self._B = LTIModel._as_2d(B)
        self._C = LTIModel._as_2d(C)
        self._D = LTIModel._as_2d(D)
        self._dt = float(dt)
        self._validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate(self) -> None:
        n = self._A.shape[0]
        if self._A.shape != (n, n):
            raise ValueError(f"A must be square, got {self._A.shape}")
        if self._B.shape[0] != n:
            raise ValueError(f"B rows must match A order ({n}), got {self._B.shape[0]}")
        if self._C.shape[1] != n:
            raise ValueError(f"C cols must match A order ({n}), got {self._C.shape[1]}")
        p, m = self._C.shape[0], self._B.shape[1]
        if self._D.shape != (p, m):
            raise ValueError(f"D must be ({p}×{m}), got {self._D.shape}")
        if self._dt < 0:
            raise ValueError(f"dt must be >= 0, got {self._dt}")

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def A(self) -> np.ndarray:
        return self._A

    @property
    def B(self) -> np.ndarray:
        return self._B

    @property
    def C(self) -> np.ndarray:
        return self._C

    @property
    def D(self) -> np.ndarray:
        return self._D

    @property
    def dt(self) -> float:
        return self._dt

    @property
    def is_discrete(self) -> bool:
        return self._dt > 0.0

    @property
    def n_states(self) -> int:
        return int(self._A.shape[0])

    @property
    def n_inputs(self) -> int:
        return int(self._B.shape[1])

    @property
    def n_outputs(self) -> int:
        return int(self._C.shape[0])

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def poles(self) -> np.ndarray:
        return np.asarray(linalg.eigvals(self._A))

    def zeros(self) -> np.ndarray:
        """Transmission zeros via the Rosenbrock system matrix.

        Returns finite eigenvalues of the generalised pencil
        (A_ext, E) where A_ext = [[A, B], [C, D]] and
        E = [[I_n, 0], [0, 0]].  Works for SISO and MIMO systems.

        Requires a **square** plant (n_inputs == n_outputs) and a
        **minimal** realisation.  Non-minimal realisations may produce
        spurious zeros corresponding to uncontrollable or unobservable
        modes.
        """
        n, m, p = self.n_states, self.n_inputs, self.n_outputs
        if m != p:
            raise ValueError(
                f"zeros() requires a square plant "
                f"(n_inputs == n_outputs); "
                f"got n_inputs={m}, n_outputs={p}."
            )
        if n == 0:
            return np.array([], dtype=complex)
        A_ext = np.block([[self._A, self._B], [self._C, self._D]])
        E = np.block(
            [
                [np.eye(n), np.zeros((n, m))],
                [np.zeros((p, n)), np.zeros((p, m))],
            ]
        )
        eigs = linalg.eigvals(A_ext, E)
        return eigs[np.isfinite(eigs)]  # type: ignore[no-any-return]

    def is_stable(self) -> bool:
        p = self.poles()
        if self.is_discrete:
            return bool(np.all(np.abs(p) < 1.0))
        return bool(np.all(np.real(p) < 0.0))

    # ------------------------------------------------------------------
    # Conversions
    # ------------------------------------------------------------------

    def to_state_space(self) -> StateSpace:
        return self

    def to_transfer_function(self) -> TransferFunction:
        if self.n_inputs != 1 or self.n_outputs != 1:
            raise ValueError(
                f"to_transfer_function() requires a SISO system "
                f"(n_inputs=1, n_outputs=1); "
                f"got n_inputs={self.n_inputs}, n_outputs={self.n_outputs}. "
                f"Use StateSpace directly for MIMO systems."
            )
        from .transfer_function import TransferFunction

        if self.is_discrete:
            sys = signal.dlti(self._A, self._B, self._C, self._D, dt=self._dt)
            tf = sys.to_tf()
        else:
            sys = signal.StateSpace(self._A, self._B, self._C, self._D)
            tf = sys.to_tf()
        num = np.asarray(tf.num).flatten()
        den = np.asarray(tf.den).flatten()
        return TransferFunction(num, den, dt=self._dt)

    # ------------------------------------------------------------------
    # Simulation
    # ------------------------------------------------------------------

    def simulate(self, t: np.ndarray, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Simulate response to input u over time vector t. Returns (t, y)."""
        if self.is_discrete:
            sys = signal.dlti(self._A, self._B, self._C, self._D, dt=self._dt)
            t_out, y_out, _ = signal.dlsim(sys, u, t)
        else:
            sys = signal.StateSpace(self._A, self._B, self._C, self._D)
            t_out, y_out, _ = signal.lsim(sys, u, t)
        return t_out, y_out

    def step(
        self,
        t: np.ndarray | None = None,
        n: int = 200,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Step response.  For discrete systems, n sets the number of samples."""
        if self.is_discrete:
            sys = signal.dlti(self._A, self._B, self._C, self._D, dt=self._dt)
            t_out, y_seqs = signal.dstep(sys, n=n)
            return t_out, np.squeeze(y_seqs[0])
        sys = signal.StateSpace(self._A, self._B, self._C, self._D)
        t_out, y_out = signal.step(sys, T=t)
        return t_out, y_out

    def bode(
        self, omega: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bode diagram. Returns (omega [rad/s], magnitude [dB], phase [deg])."""
        if self.is_discrete:
            sys = signal.dlti(self._A, self._B, self._C, self._D, dt=self._dt)
            w, mag, phase = signal.dbode(sys, w=omega)
        else:
            sys = signal.StateSpace(self._A, self._B, self._C, self._D)
            w, mag, phase = signal.bode(sys, w=omega)
        return w, mag, phase

    # ------------------------------------------------------------------
    # Real-time single-step integration (used by PlantAgent)
    # ------------------------------------------------------------------

    def evolve(self, x: np.ndarray, u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Advance one discrete step.  Requires is_discrete == True.

        Returns (x_next, y) without mutating any internal state.
        Callers are responsible for storing x_next between steps.
        """
        if not self.is_discrete:
            raise RuntimeError("evolve() requires a discrete plant. Use c2d() first.")
        x = np.atleast_2d(np.asarray(x, dtype=np.float64)).reshape(-1, 1)
        u = np.atleast_2d(np.asarray(u, dtype=np.float64)).reshape(-1, 1)
        if x.shape[0] != self.n_states:
            raise ValueError(
                f"x must have {self.n_states} element(s) (n_states), got {x.shape[0]}"
            )
        if u.shape[0] != self.n_inputs:
            raise ValueError(
                f"u must have {self.n_inputs} element(s) (n_inputs), got {u.shape[0]}"
            )
        x_next = self._A @ x + self._B @ u
        y = self._C @ x + self._D @ u
        return x_next.flatten(), y.flatten()

    # ------------------------------------------------------------------
    # Algebra (operator overloading)
    # ------------------------------------------------------------------

    def _check_compatible(self, other: StateSpace) -> None:
        if self._dt != other._dt:
            raise ValueError(
                f"Cannot combine systems with different sample times "
                f"({self._dt} vs {other._dt})."
            )

    def __add__(self, other: StateSpace) -> StateSpace:
        """Parallel connection."""
        if not isinstance(other, StateSpace):
            other = other.to_state_space()
        self._check_compatible(other)
        A = linalg.block_diag(self._A, other._A)
        B = np.vstack([self._B, other._B])
        C = np.hstack([self._C, other._C])
        D = self._D + other._D
        return StateSpace(A, B, C, D, dt=self._dt)

    def __mul__(self, other: StateSpace) -> StateSpace:
        """Series connection: self feeds into other (output = self(other(u)))."""
        if not isinstance(other, StateSpace):
            other = other.to_state_space()
        self._check_compatible(other)
        if self.n_inputs != other.n_outputs:
            raise ValueError(
                f"Series connection requires compatible inner dimensions "
                f"(self.n_inputs={self.n_inputs} must equal "
                f"other.n_outputs={other.n_outputs})."
            )
        A = np.block(
            [
                [other._A, np.zeros((other.n_states, self.n_states))],
                [self._B @ other._C, self._A],
            ]
        )
        B = np.vstack([other._B, self._B @ other._D])
        C = np.hstack([self._D @ other._C, self._C])
        D = self._D @ other._D
        return StateSpace(A, B, C, D, dt=self._dt)

    def __neg__(self) -> StateSpace:
        return StateSpace(self._A, self._B, -self._C, -self._D, dt=self._dt)

    def __repr__(self) -> str:
        domain = f"dt={self._dt}" if self.is_discrete else "continuous"
        return (
            f"StateSpace(n_states={self.n_states}, "
            f"n_inputs={self.n_inputs}, n_outputs={self.n_outputs}, {domain})"
        )
