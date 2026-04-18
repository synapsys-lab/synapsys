from __future__ import annotations

from functools import reduce
from typing import TYPE_CHECKING

import numpy as np
from scipy import linalg

from .lti import LTIModel
from .transfer_function import TransferFunction

if TYPE_CHECKING:
    from .state_space import StateSpace


class TransferFunctionMatrix(LTIModel):
    """
    MIMO transfer-function matrix G(s) of shape (n_outputs × n_inputs).

    Internally stores a 2-D list of SISO TransferFunction objects where
    ``tfs[i][j]`` is the transfer function from input j to output i.

    For simulation and analysis that require a state-space realisation
    (zeros, step, simulate, evolve) the class converts lazily via
    ``to_state_space()``.
    """

    def __init__(self, tfs: list[list[TransferFunction]]) -> None:
        if not tfs or not tfs[0]:
            raise ValueError("tfs must be a non-empty 2-D list of TransferFunction.")
        p = len(tfs)
        m = len(tfs[0])
        for row in tfs:
            if len(row) != m:
                raise ValueError(
                    f"All rows must have the same number of columns ({m}), "
                    f"got a row with {len(row)}."
                )
        dt = tfs[0][0].dt
        for row in tfs:
            for tf in row:
                if tf.dt != dt:
                    raise ValueError(
                        f"All elements must share the same dt "
                        f"(expected {dt}, got {tf.dt})."
                    )
        self._tfs: list[list[TransferFunction]] = tfs
        self._p = p
        self._m = m
        self._dt = dt

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_arrays(
        cls,
        num: list,
        den: object,
        dt: float = 0.0,
    ) -> TransferFunctionMatrix:
        """Build from nested coefficient lists.

        Args:
            num: 2-D list ``num[i][j]`` of polynomial coefficients for each
                 element.  A scalar or 1-D sequence is promoted to ``[value]``.
            den: Either a single 1-D sequence (shared denominator for all
                 elements) or a 2-D list ``den[i][j]`` of per-element
                 denominators.  Per-element is detected when ``den[0][0]``
                 is itself a sequence.
            dt:  Sample period (0 = continuous).
        """
        p = len(num)
        m = len(num[0])
        # Per-element: den[0] is a row and den[0][0] is a coefficient list.
        # Shared: den is a flat coefficient list (den[0] is a number).
        try:
            per_element = (
                hasattr(den[0], "__iter__")  # type: ignore[index]
                and hasattr(den[0][0], "__iter__")  # type: ignore[index]
            )
        except (TypeError, IndexError):
            per_element = False

        tfs: list[list[TransferFunction]] = []
        for i in range(p):
            row: list[TransferFunction] = []
            for j in range(m):
                n_ij = num[i][j]
                d_ij = den[i][j] if per_element else den  # type: ignore[index]
                row.append(TransferFunction(n_ij, d_ij, dt=dt))
            tfs.append(row)
        return cls(tfs)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def n_outputs(self) -> int:
        return self._p

    @property
    def n_inputs(self) -> int:
        return self._m

    @property
    def n_states(self) -> int:
        # Zero-numerator elements contribute 0 states to the SS realisation
        # (scipy would give a spurious 1-state system; to_state_space() skips them).
        return sum(
            0 if np.allclose(self._tfs[i][j].num, 0.0) else self._tfs[i][j].n_states
            for i in range(self._p)
            for j in range(self._m)
        )

    @property
    def dt(self) -> float:
        return self._dt

    @property
    def is_discrete(self) -> bool:
        return self._dt > 0.0

    # ------------------------------------------------------------------
    # Item access
    # ------------------------------------------------------------------

    def __getitem__(self, idx: tuple[int, int]) -> TransferFunction:
        i, j = idx
        if i >= self._p or j >= self._m or i < 0 or j < 0:
            raise IndexError(
                f"Index ({i}, {j}) out of range for "
                f"({self._p}×{self._m}) TransferFunctionMatrix."
            )
        return self._tfs[i][j]

    # ------------------------------------------------------------------
    # LTIModel interface
    # ------------------------------------------------------------------

    def poles(self) -> np.ndarray:
        """Element-wise union of all poles (may contain repeats).

        For a coupled (non-diagonal) MIMO plant these are **not** the
        true Smith-McMillan poles of the transfer-function matrix.
        Use ``to_state_space().poles()`` for the true system poles.
        """
        all_poles = np.concatenate([
            self._tfs[i][j].poles()
            for i in range(self._p)
            for j in range(self._m)
        ])
        return all_poles

    def zeros(self) -> np.ndarray:
        """Transmission zeros via the Rosenbrock system matrix of the SS realisation."""
        return self.to_state_space().zeros()

    def is_stable(self) -> bool:
        """True when every element is stable (element-wise check).

        For coupled MIMO plants this is a necessary but not sufficient
        condition.  Use ``to_state_space().is_stable()`` for a rigorous test.
        """
        return all(
            self._tfs[i][j].is_stable()
            for i in range(self._p)
            for j in range(self._m)
        )

    def to_state_space(self) -> StateSpace:
        """Minimal state-space realisation via independent element realisations.

        The combined state vector is ordered as
        [x_00, x_01, …, x_0m, x_10, …, x_pm].
        Each element contributes its own state block driven by the j-th
        input and feeding only the i-th output.
        """
        from .state_space import StateSpace

        p, m = self._p, self._m
        # Convert only non-zero elements — zero-numerator TFs contribute only
        # a D term and must be skipped to avoid the spurious 1-state scipy
        # realisation of G(s)=0, which would add phantom zero eigenvalues to
        # the Rosenbrock pencil used in zeros().
        ss_elems: list[list[StateSpace | None]] = [
            [
                None if np.allclose(self._tfs[i][j].num, 0.0)
                else self._tfs[i][j].to_state_space()
                for j in range(m)
            ]
            for i in range(p)
        ]
        n_total = sum(
            0 if ss_elems[i][j] is None else ss_elems[i][j].n_states  # type: ignore[union-attr]
            for i in range(p)
            for j in range(m)
        )

        A = np.zeros((n_total, n_total))
        B = np.zeros((n_total, m))
        C = np.zeros((p, n_total))
        D = np.zeros((p, m))

        idx = 0
        for i in range(p):
            for j in range(m):
                ss = ss_elems[i][j]
                if ss is None:
                    D[i, j] = 0.0
                    continue
                n = ss.n_states
                if n > 0:
                    A[idx : idx + n, idx : idx + n] = ss.A
                    B[idx : idx + n, j : j + 1] = ss.B
                    C[i : i + 1, idx : idx + n] = ss.C
                D[i, j] = float(ss.D.flat[0])
                idx += n

        return StateSpace(A, B, C, D, dt=self._dt)

    # ------------------------------------------------------------------
    # Simulation (delegates to StateSpace realisation)
    # ------------------------------------------------------------------

    def simulate(
        self, t: np.ndarray, u: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """Simulate response to input ``u`` over time ``t``. Returns ``(t, y)``."""
        return self.to_state_space().simulate(t, u)

    def step(
        self, t: np.ndarray | None = None, n: int = 200
    ) -> tuple[np.ndarray, np.ndarray]:
        """Step response.  For discrete systems ``n`` sets the number of samples."""
        return self.to_state_space().step(t, n=n)

    def bode(
        self, omega: np.ndarray | None = None
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Bode diagram.  Returns ``(omega [rad/s], mag [dB], phase [deg])``."""
        return self.to_state_space().bode(omega)

    def to_transfer_function(self) -> TransferFunction:
        if self._p != 1 or self._m != 1:
            raise ValueError(
                f"to_transfer_function() requires a SISO (1×1) matrix, "
                f"got ({self._p}×{self._m}). "
                f"Use to_state_space() for MIMO systems."
            )
        return self._tfs[0][0]

    # ------------------------------------------------------------------
    # Algebra
    # ------------------------------------------------------------------

    def __neg__(self) -> TransferFunctionMatrix:
        return TransferFunctionMatrix([
            [-self._tfs[i][j] for j in range(self._m)]
            for i in range(self._p)
        ])

    def __add__(self, other: TransferFunctionMatrix) -> TransferFunctionMatrix:
        """Parallel connection — element-wise addition."""
        if not isinstance(other, TransferFunctionMatrix):
            raise TypeError(f"Cannot add TransferFunctionMatrix and {type(other)}")
        if (self._p, self._m) != (other._p, other._m):
            raise ValueError(
                f"Incompatible shape for parallel connection: "
                f"({self._p}×{self._m}) vs ({other._p}×{other._m})."
            )
        return TransferFunctionMatrix([
            [self._tfs[i][j] + other._tfs[i][j] for j in range(self._m)]
            for i in range(self._p)
        ])

    def __mul__(self, other: TransferFunctionMatrix) -> TransferFunctionMatrix:
        """Series connection — matrix multiplication G_self @ G_other."""
        if not isinstance(other, TransferFunctionMatrix):
            raise TypeError(f"Cannot multiply TransferFunctionMatrix and {type(other)}")
        if self._m != other._p:
            raise ValueError(
                f"Incompatible inner dimensions for series connection: "
                f"({self._p}×{self._m}) * ({other._p}×{other._m})."
            )
        result: list[list[TransferFunction]] = []
        for i in range(self._p):
            row: list[TransferFunction] = []
            for k in range(other._m):
                elem = reduce(
                    lambda a, b: a + b,
                    (self._tfs[i][j] * other._tfs[j][k] for j in range(self._m)),
                )
                row.append(elem)
            result.append(row)
        return TransferFunctionMatrix(result)

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        domain = f"dt={self._dt}" if self.is_discrete else "continuous"
        return (
            f"TransferFunctionMatrix({self._p}×{self._m}, {domain})"
        )
