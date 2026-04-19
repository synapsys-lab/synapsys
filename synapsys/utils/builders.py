"""State-space model builder from named differential equations."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["StateEquations"]


@dataclass
class StateEquations:
    """Build the A and B matrices by declaring each differential equation by name.

    Each call to :meth:`eq` sets the coefficients for the derivative of one
    state variable.  Names that appear in ``states`` go to **A**; names that
    appear in ``inputs`` go to **B**.

    Parameters
    ----------
    states:
        Ordered list of state variable names, e.g. ``["x1", "x2", "v1", "v2"]``.
    inputs:
        Ordered list of input variable names, e.g. ``["F"]``.

    Examples
    --------
    2-DOF mass–spring–damper  (m=1, c=0.1, k=2):

    >>> m, c, k = 1, 0.1, 2
    >>> eqs = (
    ...     StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    ...     .eq("x1", v1=1)
    ...     .eq("x2", v2=1)
    ...     .eq("v1", x1=-2*k/m, x2=k/m, v1=-c/m)
    ...     .eq("v2", x1=k/m, x2=-2*k/m, v2=-c/m, F=1/m)
    ... )
    >>> A = eqs.A
    >>> B = eqs.B
    >>> C = eqs.output("x1", "x2")

    The resulting system can be passed directly to :func:`synapsys.api.ss`::

        from synapsys.api import ss
        G = ss(eqs.A, eqs.B, eqs.output("x1", "x2"), 0)
    """

    states: list[str]
    inputs: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        n = len(self.states)
        m = len(self.inputs)
        self._A = np.zeros((n, n))
        self._B = np.zeros((n, m))

    # ── fluent builder ───────────────────────────────────────────────────────

    def eq(self, state: str, **coeffs: float) -> "StateEquations":
        """Set coefficients for the derivative of *state*.

        Keyword arguments whose names match a state variable are written to
        **A**; those matching an input variable are written to **B**.

        Parameters
        ----------
        state:
            The state variable whose derivative is being defined.
        **coeffs:
            ``name=value`` pairs where *name* must be a declared state or input.

        Raises
        ------
        ValueError
            If *state* or any coefficient name is not declared.
        """
        if state not in self.states:
            raise ValueError(
                f"'{state}' is not a declared state.  Declared states: {self.states}"
            )
        i = self.states.index(state)
        for name, val in coeffs.items():
            if name in self.states:
                self._A[i, self.states.index(name)] = float(val)
            elif name in self.inputs:
                self._B[i, self.inputs.index(name)] = float(val)
            else:
                raise ValueError(
                    f"'{name}' is not a declared state or input.  "
                    f"States: {self.states}  Inputs: {self.inputs}"
                )
        return self

    # ── outputs ──────────────────────────────────────────────────────────────

    def output(self, *state_names: str) -> np.ndarray:
        """Build a C matrix that selects *state_names* as outputs.

        Parameters
        ----------
        *state_names:
            Names of the states to observe, in output order.

        Returns
        -------
        np.ndarray
            Shape ``(len(state_names), len(self.states))``.
        """
        if not state_names:
            raise ValueError("Provide at least one state name.")
        C = np.zeros((len(state_names), len(self.states)))
        for row_i, name in enumerate(state_names):
            if name not in self.states:
                raise ValueError(f"'{name}' is not a declared state.")
            C[row_i, self.states.index(name)] = 1.0
        return C

    # ── read-only properties ─────────────────────────────────────────────────

    @property
    def A(self) -> np.ndarray:
        """System matrix  (n × n)."""
        return np.array(self._A)

    @property
    def B(self) -> np.ndarray:
        """Input matrix  (n × m)."""
        return np.array(self._B)

    # ── convenience ──────────────────────────────────────────────────────────

    def __repr__(self) -> str:  # pragma: no cover
        lines = [
            f"StateEquations(states={self.states}, inputs={self.inputs})",
            f"  A =\n{self._A}",
            f"  B =\n{self._B}",
        ]
        return "\n".join(lines)
