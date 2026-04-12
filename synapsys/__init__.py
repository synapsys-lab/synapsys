"""Synapsys — modern Python control systems framework."""

__version__ = "0.1.0"

# ── Convenience re-exports ────────────────────────────────────────────────────
# Users can write `from synapsys import tf` instead of `from synapsys.api import tf`
from synapsys.algorithms.lqr import lqr
from synapsys.algorithms.pid import PID
from synapsys.api.matlab_compat import (
    bode,
    c2d,
    feedback,
    lsim,
    parallel,
    series,
    ss,
    step,
    tf,
)
from synapsys.core.state_space import StateSpace
from synapsys.core.transfer_function import TransferFunction

__all__ = [
    "__version__",
    # MATLAB-compatible API
    "tf",
    "ss",
    "step",
    "bode",
    "lsim",
    "feedback",
    "series",
    "parallel",
    "c2d",
    # Core classes
    "TransferFunction",
    "StateSpace",
    # Algorithms
    "PID",
    "lqr",
]
