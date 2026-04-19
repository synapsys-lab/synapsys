"""Synapsys — modern Python control systems framework."""

__version__ = "0.2.2"

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
from synapsys.core.transfer_function_matrix import TransferFunctionMatrix
from synapsys.utils import StateEquations, col, mat, row
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend, ZMQBrokerBackend

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
    "TransferFunctionMatrix",
    "StateSpace",
    # Algorithms
    "PID",
    "lqr",
    # Utils
    "mat",
    "col",
    "row",
    "StateEquations",
    # Broker
    "MessageBroker",
    "Topic",
    "SharedMemoryBackend",
    "ZMQBrokerBackend",
]
