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


def tf(num: object, den: object, dt: float = 0.0) -> TransferFunction:
    """Create a transfer function.  Mirrors ``tf()`` in MATLAB.

    Args:
        dt: Sample period > 0 creates a discrete-time system.
    """
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
    G: TransferFunction | StateSpace,
    H: TransferFunction | None = None,
) -> TransferFunction:
    """Closed-loop with negative feedback.  Mirrors ``feedback()`` in MATLAB."""
    if not isinstance(G, TransferFunction):
        G = G.to_transfer_function()
    return G.feedback(H)


def series(
    *systems: TransferFunction | StateSpace,
) -> TransferFunction | StateSpace:
    """Connect systems in series.  Mirrors ``series()`` in MATLAB."""
    result = systems[0]
    for sys in systems[1:]:
        result = result * sys  # type: ignore[operator]
    return result


def parallel(
    *systems: TransferFunction | StateSpace,
) -> TransferFunction | StateSpace:
    """Connect systems in parallel.  Mirrors ``parallel()`` in MATLAB."""
    result = systems[0]
    for sys in systems[1:]:
        result = result + sys  # type: ignore[operator]
    return result
