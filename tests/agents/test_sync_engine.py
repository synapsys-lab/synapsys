"""Tests for SyncEngine — including the new elapsed property."""

from __future__ import annotations

import time

import pytest

from synapsys.agents.sync_engine import SyncEngine, SyncMode


class TestSyncEngineElapsed:
    def test_elapsed_increases_over_time(self):
        eng = SyncEngine(SyncMode.LOCK_STEP, dt=0.01)
        t0 = eng.elapsed
        time.sleep(0.05)
        assert eng.elapsed > t0

    def test_elapsed_resets_on_reset(self):
        eng = SyncEngine(SyncMode.LOCK_STEP, dt=0.01)
        time.sleep(0.05)
        eng.reset()
        assert eng.elapsed < 0.02  # just reset, should be near zero

    def test_t_is_k_times_dt(self):
        eng = SyncEngine(SyncMode.LOCK_STEP, dt=0.1)
        eng.tick()
        eng.tick()
        assert eng.t == pytest.approx(0.2)
        assert eng.k == 2

    def test_elapsed_differs_from_t_in_lock_step(self):
        """t = k*dt (simulated time); elapsed = wall-clock — they can diverge."""
        eng = SyncEngine(SyncMode.LOCK_STEP, dt=1.0)  # large dt
        time.sleep(0.05)
        eng.tick()
        # t jumped by 1 s (dt=1.0), but elapsed is ~0.05 s
        assert eng.t == pytest.approx(1.0)
        assert eng.elapsed < 0.5
