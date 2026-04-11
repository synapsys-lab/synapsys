from __future__ import annotations

import threading
import time
from typing import Callable

import numpy as np

from .base import HardwareInterface


class MockHardwareInterface(HardwareInterface):
    """
    In-process hardware stub for testing and HIL demos without physical devices.

    The mock simulates a hardware device by running a user-supplied callable
    ``plant_fn(u) -> y`` internally.  This lets you validate the full
    ``HardwareAgent`` code-path — including ZOH, timeout handling, and
    transport wiring — without any real hardware.

    Parameters
    ----------
    n_inputs : int
        Number of actuator channels (columns of ``u``).
    n_outputs : int
        Number of sensor channels (rows of ``y``).
    plant_fn : Callable[[np.ndarray], np.ndarray] | None
        ``f(u) -> y`` called on every ``write_inputs``.
        Defaults to a unity function ``y = u`` when ``n_inputs == n_outputs``,
        or zeros otherwise.
    latency_ms : float
        Artificial round-trip delay injected on every read/write call.
        Useful for jitter tolerance testing (default 0 ms).

    Example::

        from synapsys.hw import MockHardwareInterface

        # Simulate a first-order system: y(k+1) = 0.9*y(k) + 0.1*u(k)
        state = [0.0]
        def plant_fn(u):
            state[0] = 0.9 * state[0] + 0.1 * u[0]
            return np.array([state[0]])

        hw = MockHardwareInterface(n_inputs=1, n_outputs=1, plant_fn=plant_fn)
        with hw:
            hw.write_inputs(np.array([1.0]))
            y = hw.read_outputs()   # → approx [0.1]
    """

    def __init__(
        self,
        n_inputs: int,
        n_outputs: int,
        plant_fn: Callable[[np.ndarray], np.ndarray] | None = None,
        latency_ms: float = 0.0,
    ):
        self._n_inputs = n_inputs
        self._n_outputs = n_outputs
        self._latency_s = latency_ms / 1000.0
        self._connected = False
        self._lock = threading.Lock()

        self._last_u: np.ndarray = np.zeros(n_inputs)
        self._last_y: np.ndarray = np.zeros(n_outputs)

        if plant_fn is not None:
            self._plant_fn = plant_fn
        elif n_inputs == n_outputs:
            self._plant_fn = lambda u: u.copy()
        else:
            self._plant_fn = lambda u: np.zeros(n_outputs)

    # ── metadata ──────────────────────────────────────────────────────────────

    @property
    def n_inputs(self) -> int:
        return self._n_inputs

    @property
    def n_outputs(self) -> int:
        return self._n_outputs

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def connect(self) -> None:
        self._connected = True

    def disconnect(self) -> None:
        self._connected = False

    # ── I/O ───────────────────────────────────────────────────────────────────

    def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
        """Store ``u`` and evaluate ``plant_fn`` to update the internal state."""
        if self._latency_s > 0:
            time.sleep(self._latency_s)
        with self._lock:
            self._last_u = np.asarray(u, dtype=np.float64).flatten()
            self._last_y = np.asarray(
                self._plant_fn(self._last_u), dtype=np.float64
            ).flatten()

    def read_outputs(self, timeout_ms: float = 100.0) -> np.ndarray:
        """Return the last computed ``y``."""
        if self._latency_s > 0:
            time.sleep(self._latency_s)
        with self._lock:
            return np.array(self._last_y)
