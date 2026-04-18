"""
MATLAB-compatible API layer.

Functions mirror their MATLAB counterparts so users can transition with
minimal friction.  All functions delegate to the core classes.
"""
from __future__ import annotations

import numpy as np
from scipy import signal as _signal

from ..core.state_space import StateSpace
from ..core.transfer_function import TransferFunction
from ..core.transfer_function_matrix import TransferFunctionMatrix


def tf(
    num: object, den: object, dt: float = 0.0
) -> TransferFunction | TransferFunctionMatrix:
    """Create a transfer function or MIMO transfer-function matrix.

    * 1-D ``num``  → SISO ``TransferFunction``.
    * 2-D ``num``  → MIMO ``TransferFunctionMatrix`` (mirrors MATLAB ``tf``).

    Args:
        dt: Sample period > 0 creates a discrete-time system.

    Raises:
        TypeError: if ``num`` or ``den`` is ``None``.
    """
    if num is None or den is None:
        raise TypeError(
            "tf() requires non-None num and den; "
            f"got num={num!r}, den={den!r}."
        )
    try:
        is_mimo = hasattr(num[0], "__iter__")  # type: ignore[index]
    except (TypeError, IndexError):
        is_mimo = False

    if is_mimo:
        return TransferFunctionMatrix.from_arrays(num, den, dt=dt)  # type: ignore[arg-type]
    return TransferFunction(num, den, dt=dt)


def ss(A: object, B: object, C: object, D: object, dt: float = 0.0) -> StateSpace:
    """Create a state-space model.  Mirrors ``ss()`` in MATLAB.

    Args:
        dt: Sample period > 0 creates a discrete-time system.
    """
    return StateSpace(A, B, C, D, dt=dt)


def c2d(
    sys: StateSpace | TransferFunction,
    dt: float,
    method: str = "zoh",
) -> StateSpace | TransferFunction:
    """
    Convert continuous-time system to discrete-time.  Mirrors ``c2d()`` in MATLAB.

    Args:
        sys:    Continuous-time StateSpace or TransferFunction (dt must be 0).
        dt:     Desired sample period in seconds.
        method: Discretisation method — ``'zoh'`` (default), ``'bilinear'``,
                ``'euler'``, ``'backward_diff'``.

    Returns:
        Discrete-time system of the same type as the input.
    """
    if sys.is_discrete:
        raise ValueError("System is already discrete (dt > 0).")

    if isinstance(sys, StateSpace):
        Ad, Bd, Cd, Dd, _ = _signal.cont2discrete(
            (sys.A, sys.B, sys.C, sys.D), dt, method=method
        )
        return StateSpace(Ad, Bd, Cd, Dd, dt=dt)

    if isinstance(sys, TransferFunction):
        # Route through state space for numerical stability
        ss_d = c2d(sys.to_state_space(), dt, method=method)
        return ss_d.to_transfer_function()

    raise TypeError(f"Expected StateSpace or TransferFunction, got {type(sys)}")


def step(
    sys: TransferFunction | StateSpace,
    t: np.ndarray | None = None,
    n: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute step response.  Mirrors ``step()`` in MATLAB."""
    return sys.step(t, n=n) if sys.is_discrete else sys.step(t)


def lsim(
    sys: TransferFunction | StateSpace,
    t: np.ndarray,
    u: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate response to arbitrary input ``u`` over time ``t``.
    Mirrors ``lsim()`` in MATLAB.  Returns ``(t_out, y_out)``."""
    return sys.simulate(t, u)


def bode(
    sys: TransferFunction | StateSpace,
    omega: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Bode diagram.  Returns (omega [rad/s], mag [dB], phase [deg])."""
    return sys.bode(omega)


def feedback(
    G: TransferFunction | StateSpace | TransferFunctionMatrix,
    H: TransferFunction | StateSpace | None = None,
) -> TransferFunction | StateSpace:
    """Closed-loop T = G(I + HG)⁻¹ with negative feedback.

    * ``G`` is ``TransferFunction`` → polynomial algebra, returns ``TransferFunction``.
    * ``G`` is ``StateSpace`` or ``TransferFunctionMatrix`` → state-space
      interconnection, returns ``StateSpace``.
      Unity feedback (``H=None``) requires a square plant (n_inputs == n_outputs).
    """
    if isinstance(G, TransferFunction):
        if H is not None and not isinstance(H, TransferFunction):
            H = H.to_transfer_function()
        return G.feedback(H)

    # G is StateSpace or TransferFunctionMatrix — convert to SS
    G_ss: StateSpace = G if isinstance(G, StateSpace) else G.to_state_space()

    # Build H as a StateSpace (handling static TF to avoid scipy phantom state)
    H_ss: StateSpace | None = None
    if H is not None:
        if isinstance(H, StateSpace):
            H_ss = H
        elif isinstance(H, TransferFunction) and H.n_states == 0:
            # Static gain: build true 0-state SS directly to avoid scipy's
            # spurious 1-state realisation of a constant TF.
            gain = float(H.num[0]) / float(H.den[0])
            H_ss = StateSpace(
                np.zeros((0, 0)),
                np.zeros((0, H.n_inputs)),
                np.zeros((H.n_outputs, 0)),
                np.array([[gain]]),
                dt=H.dt,
            )
        else:
            H_ss = H.to_state_space()

    return _ss_feedback(G_ss, H_ss)


def _ss_feedback(G: StateSpace, H: StateSpace | None) -> StateSpace:
    """State-space closed-loop for negative feedback T = G(I + HG)⁻¹.

    Handles H with n_states=0 (static sensor) via block-matrix broadcasting:
    the zero-dimensional state blocks vanish from the augmented system.
    """
    Ag, Bg, Cg, Dg = G.A, G.B, G.C, G.D
    m, p = G.n_inputs, G.n_outputs

    if H is None:
        # Unity feedback: H = I (static, no sensor dynamics)
        if m != p:
            raise ValueError(
                f"Unity feedback requires a square plant "
                f"(n_inputs == n_outputs), got n_inputs={m}, n_outputs={p}."
            )
        M = np.eye(m) + Dg
        Minv = np.linalg.inv(M)
        A_cl = Ag - Bg @ Minv @ Cg
        B_cl = Bg @ Minv
        C_cl = Minv @ Cg
        D_cl = Dg @ Minv
        return StateSpace(A_cl, B_cl, C_cl, D_cl, dt=G.dt)

    # General sensor H — validate dt compatibility
    if H.dt != G.dt:
        raise ValueError(
            f"G and H must share the same sample time "
            f"(G.dt={G.dt}, H.dt={H.dt})."
        )

    # H maps plant output (p) to error signal (m): H.n_inputs=p, H.n_outputs=m
    Ah, Bh, Ch, Dh = H.A, H.B, H.C, H.D
    M = np.eye(m) + Dh @ Dg   # m×m
    Minv = np.linalg.inv(M)
    # Augmented state z = [x_g; x_h]  (x_h may be empty for static H)
    A_cl = np.block([
        [Ag - Bg @ Minv @ Dh @ Cg,  -Bg @ Minv @ Ch],
        [Bh @ (Cg - Dg @ Minv @ Dh @ Cg),  Ah - Bh @ Dg @ Minv @ Ch],
    ])
    B_cl = np.vstack([Bg @ Minv, Bh @ Dg @ Minv])
    C_cl = np.hstack([Cg - Dg @ Minv @ Dh @ Cg, -Dg @ Minv @ Ch])
    D_cl = Dg @ Minv
    return StateSpace(A_cl, B_cl, C_cl, D_cl, dt=G.dt)


def series(
    *systems: TransferFunction | StateSpace,
) -> TransferFunction | StateSpace:
    """Connect systems in series.  Mirrors ``series()`` in MATLAB."""
    if not systems:
        raise ValueError("series() requires at least one system.")
    result = systems[0]
    for sys in systems[1:]:
        result = result * sys  # type: ignore[operator]
    return result


def parallel(
    *systems: TransferFunction | StateSpace,
) -> TransferFunction | StateSpace:
    """Connect systems in parallel.  Mirrors ``parallel()`` in MATLAB."""
    if not systems:
        raise ValueError("parallel() requires at least one system.")
    result = systems[0]
    for sys in systems[1:]:
        result = result + sys  # type: ignore[operator]
    return result
