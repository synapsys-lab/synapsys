from __future__ import annotations

import time
from enum import Enum


class SyncMode(str, Enum):
    """Simulation time-advancement strategy."""
    LOCK_STEP  = "lock_step"   # wait for all peers before k -> k+1
    WALL_CLOCK = "wall_clock"  # advance in real-time; missed samples use ZOH


class SyncEngine:
    """
    Controls how simulation time advances for a single agent.

    LOCK_STEP
        The caller is responsible for external synchronisation (e.g. via a
        barrier or REQ/REP transport).  ``tick()`` simply increments k.
        Mathematically exact; speed limited by the slowest agent.

    WALL_CLOCK
        ``tick()`` sleeps as needed to pace steps at real-time ``dt``.
        If an agent is late, it catches up on the next step.
        Realistic for testing resilience and latency effects.
    """

    def __init__(self, mode: SyncMode = SyncMode.WALL_CLOCK, dt: float = 0.01):
        self.mode = mode
        self.dt = dt
        self._k: int = 0
        self._t0: float = time.monotonic()

    @property
    def k(self) -> int:
        """Current discrete step index."""
        return self._k

    @property
    def t(self) -> float:
        """Current simulation time in seconds (k * dt)."""
        return self._k * self.dt

    @property
    def elapsed(self) -> float:
        """Wall-clock seconds since this engine was created or last reset."""
        return time.monotonic() - self._t0

    def tick(self) -> float:
        """
        Advance one simulation step.  Returns the new simulation time.

        In WALL_CLOCK mode, sleeps to maintain real-time pacing.
        """
        if self.mode == SyncMode.WALL_CLOCK:
            target = self._t0 + (self._k + 1) * self.dt
            now = time.monotonic()
            if target > now:
                time.sleep(target - now)
        self._k += 1
        return self.t

    def reset(self) -> None:
        self._k = 0
        self._t0 = time.monotonic()
