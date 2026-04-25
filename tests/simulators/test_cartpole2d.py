"""Tests for CartPole2DView — 2D matplotlib animation.

All tests use the Agg backend so no display is required.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest

from synapsys.viz.cartpole2d import CartPole2DView

# ── Construction ──────────────────────────────────────────────────────────────


class TestConstruction:
    def test_default_instantiation(self):
        view = CartPole2DView()
        assert view is not None

    def test_custom_dt_and_duration(self):
        view = CartPole2DView(dt=0.01, duration=5.0)
        assert view.dt == pytest.approx(0.01)
        assert view.duration == pytest.approx(5.0)

    def test_custom_x0(self):
        x0 = np.array([0.0, 0.0, 0.2, 0.0])
        view = CartPole2DView(x0=x0)
        np.testing.assert_array_equal(view.x0, x0)

    def test_custom_controller_stored(self):
        ctrl = lambda x: np.zeros(1)
        view = CartPole2DView(controller=ctrl)
        assert view.controller is ctrl


# ── simulate ──────────────────────────────────────────────────────────────────


class TestSimulate:
    def test_returns_history_dict(self):
        view = CartPole2DView(dt=0.02, duration=0.1)
        hist = view.simulate()
        assert isinstance(hist, dict)

    def test_history_has_expected_keys(self):
        view = CartPole2DView(dt=0.02, duration=0.1)
        hist = view.simulate()
        assert "t" in hist
        assert "pos" in hist
        assert "angle" in hist
        assert "force" in hist

    def test_history_length_matches_steps(self):
        dt, duration = 0.02, 0.2
        view = CartPole2DView(dt=dt, duration=duration)
        hist = view.simulate()
        expected_steps = int(duration / dt)
        assert len(hist["t"]) == expected_steps
        assert len(hist["pos"]) == expected_steps
        assert len(hist["angle"]) == expected_steps

    def test_lqr_stabilises_pole(self):
        """Default LQR controller must stabilise a small perturbation."""
        x0 = np.array([0.0, 0.0, 0.15, 0.0])
        view = CartPole2DView(dt=0.02, duration=5.0, x0=x0)
        hist = view.simulate()
        final_angle = hist["angle"][-1]
        assert abs(final_angle) < 0.05  # nearly upright

    def test_custom_controller_called(self):
        calls = [0]

        def counting_ctrl(x):
            calls[0] += 1
            return np.zeros(1)

        view = CartPole2DView(dt=0.02, duration=0.1, controller=counting_ctrl)
        view.simulate()
        assert calls[0] > 0

    def test_simulate_stores_history(self):
        view = CartPole2DView(dt=0.02, duration=0.1)
        hist = view.simulate()
        assert view.history is hist


# ── animate ───────────────────────────────────────────────────────────────────


class TestAnimate:
    def test_animate_returns_func_animation(self):
        from matplotlib.animation import FuncAnimation

        view = CartPole2DView(dt=0.02, duration=0.2)
        view.simulate()
        anim = view.animate()
        assert isinstance(anim, FuncAnimation)

    def test_animate_without_prior_simulate_calls_simulate(self):
        from matplotlib.animation import FuncAnimation

        view = CartPole2DView(dt=0.02, duration=0.1)
        anim = view.animate()  # must not raise; triggers simulate() internally
        assert isinstance(anim, FuncAnimation)
