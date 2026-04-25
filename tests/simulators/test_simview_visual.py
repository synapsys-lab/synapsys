"""Visual integration tests for synapsys.viz.simview.

These tests build and exercise the full Qt + PyVista + matplotlib stack.
They are skipped automatically when DISPLAY is not available.

Run selectively:
    pytest tests/simulators/test_simview_visual.py -v
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtWidgets import QMainWindow

from synapsys.viz.simview.cartpole import (
    _LIMIT_FRAC,
    _TRACK_HW,
    _WARN_FRAC,
    CartPoleView,
)
from synapsys.viz.simview.msd import MassSpringDamperView
from synapsys.viz.simview.pendulum import PendulumView

pytestmark = pytest.mark.visual


# ── helpers ────────────────────────────────────────────────────────────────────


def _build(qt_app, view_cls, **kwargs):
    """Instantiate, init QMainWindow, and call _build_all."""
    v = view_cls(**kwargs)
    QMainWindow.__init__(v)
    v._build_all()
    return v


def _teardown(v):
    try:
        v._timer.stop()
        v._pl.close()
        import matplotlib.pyplot as plt

        plt.close("all")
    except Exception:
        pass


def _run_ticks(v, n=10):
    for _ in range(n):
        v._on_tick()


# ── build without crash ────────────────────────────────────────────────────────


class TestBuildNoCrash:
    def test_cartpole_builds(self, qt_app):
        v = _build(qt_app, CartPoleView)
        assert v._sim is not None
        assert v._K is not None
        assert v._actors is not None
        assert v._mpl_lines is not None
        _teardown(v)

    def test_pendulum_builds(self, qt_app):
        v = _build(qt_app, PendulumView)
        assert v._sim is not None
        assert v._K is not None
        _teardown(v)

    def test_msd_builds(self, qt_app):
        v = _build(qt_app, MassSpringDamperView)
        assert v._sim is not None
        assert v._K is not None
        _teardown(v)

    def test_cartpole_custom_params_builds(self, qt_app):
        v = _build(qt_app, CartPoleView, m_c=2.0, m_p=0.3, l=0.8)
        assert v._K.shape == (1, 4)
        _teardown(v)

    def test_cartpole_custom_controller_builds(self, qt_app):
        def my_ctrl(x):
            return np.zeros(1)

        v = _build(qt_app, CartPoleView, controller=my_ctrl)
        assert v._ctrl_label == "my_ctrl"
        assert v._K is None  # LQR not designed when custom controller used
        _teardown(v)

    def test_msd_custom_setpoints_builds(self, qt_app):
        sps = [("0", 0.0), ("+2m", 2.0), ("-2m", -2.0)]
        v = _build(qt_app, MassSpringDamperView, setpoints=sps)
        btns = v._sp_group.buttons()
        assert len(btns) == 3
        assert btns[1].text() == "+2m"
        _teardown(v)


# ── tick loop ──────────────────────────────────────────────────────────────────


class TestTickLoop:
    def test_cartpole_ticks_without_error(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 20)
        assert v._t == pytest.approx(20 * v._dt)
        _teardown(v)

    def test_pendulum_ticks_without_error(self, qt_app):
        v = _build(qt_app, PendulumView)
        _run_ticks(v, 20)
        assert v._t == pytest.approx(20 * v._dt)
        _teardown(v)

    def test_msd_ticks_without_error(self, qt_app):
        v = _build(qt_app, MassSpringDamperView)
        _run_ticks(v, 20)
        assert v._t == pytest.approx(20 * v._dt)
        _teardown(v)

    def test_history_grows_during_ticks(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 15)
        assert len(v._hist["t"]) == 15
        assert len(v._hist["pos"]) == 15
        assert len(v._hist["vel"]) == 15
        _teardown(v)

    def test_tick_paused_does_not_advance_time(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 5)
        t_before = v._t
        v._paused = True
        _run_ticks(v, 10)
        assert v._t == pytest.approx(t_before)
        _teardown(v)

    def test_custom_controller_called_during_tick(self, qt_app):
        call_log = []

        def tracking_ctrl(x):
            call_log.append(x.copy())
            return np.zeros(1)

        v = _build(qt_app, CartPoleView, controller=tracking_ctrl)
        _run_ticks(v, 5)
        assert len(call_log) == 5
        assert all(c.shape == (4,) for c in call_log)
        _teardown(v)

    def test_controller_receives_current_state(self, qt_app):
        states = []

        def record(x):
            states.append(x.copy())
            return np.zeros(1)

        v = _build(qt_app, CartPoleView, controller=record)
        _run_ticks(v, 3)
        # Each state passed should differ from previous (system evolves)
        assert not np.allclose(states[0], states[-1])
        _teardown(v)


# ── LQR behaviour ─────────────────────────────────────────────────────────────


class TestLQRBehaviour:
    def test_lqr_stabilises_cartpole(self, qt_app):
        """Starting near equilibrium, LQR should keep angle small."""
        v = _build(qt_app, CartPoleView, x0=np.array([0.0, 0.0, 0.05, 0.0]))
        _run_ticks(v, 200)
        theta = abs(np.degrees(v._sim.state[2]))
        assert theta < 10.0, f"angle diverged to {theta:.1f}°"
        _teardown(v)

    def test_lqr_stabilises_pendulum(self, qt_app):
        v = _build(qt_app, PendulumView, x0=np.array([0.05, 0.0]))
        _run_ticks(v, 200)
        theta = abs(np.degrees(v._sim.state[0]))
        assert theta < 10.0, f"angle diverged to {theta:.1f}°"
        _teardown(v)

    def test_lqr_drives_msd_to_setpoint(self, qt_app):
        v = _build(qt_app, MassSpringDamperView, x0=np.array([0.0, 0.0]))
        v._set_setpoint(1.5)
        _run_ticks(v, 500)
        q = v._sim.state[0]
        assert abs(q - 1.5) < 0.15, f"position {q:.3f} far from setpoint 1.5"
        _teardown(v)


# ── reset ──────────────────────────────────────────────────────────────────────


class TestReset:
    def test_reset_clears_time(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 20)
        v._reset_sim()
        assert v._t == pytest.approx(0.0)
        _teardown(v)

    def test_reset_clears_history(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 20)
        v._reset_sim()
        assert len(v._hist["t"]) == 0
        assert len(v._hist["pos"]) == 0
        _teardown(v)

    def test_reset_clears_mpl_lines(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 20)
        v._reset_sim()
        xdata, _ = v._mpl_lines["pos"].get_data()
        assert len(xdata) == 0
        _teardown(v)

    def test_reset_restores_x0_default(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 30)
        v._reset_sim()
        state = v._sim.state
        assert state[2] == pytest.approx(0.18, abs=1e-6)  # default theta
        _teardown(v)

    def test_reset_restores_custom_x0(self, qt_app):
        x0 = np.array([0.5, 0.0, 0.3, 0.0])
        v = _build(qt_app, CartPoleView, x0=x0)
        _run_ticks(v, 30)
        v._reset_sim()
        assert np.allclose(v._sim.state, x0, atol=1e-6)
        _teardown(v)

    def test_msd_reset_returns_to_first_setpoint(self, qt_app):
        sps = [("+1m", 1.0), ("0", 0.0)]
        v = _build(qt_app, MassSpringDamperView, setpoints=sps)
        v._set_setpoint(0.0)
        v._reset_sim()
        assert v._setpoint == pytest.approx(1.0)
        _teardown(v)


# ── perturbation ──────────────────────────────────────────────────────────────


class TestPerturbation:
    def test_set_pert_applies_value(self, qt_app):
        v = _build(qt_app, CartPoleView)
        v._set_pert(25.0)
        assert v._pert == pytest.approx(25.0)
        _teardown(v)

    def test_set_pert_zero_clears(self, qt_app):
        v = _build(qt_app, CartPoleView)
        v._set_pert(25.0)
        v._set_pert(0.0)
        pv = v._pert_vector()
        assert np.allclose(pv, 0.0)
        _teardown(v)

    def test_pert_influences_simulation(self, qt_app):
        v_clean = _build(qt_app, CartPoleView)
        v_pert = _build(qt_app, CartPoleView)
        v_pert._set_pert(50.0)
        _run_ticks(v_clean, 10)
        _run_ticks(v_pert, 10)
        assert not np.allclose(v_clean._sim.state, v_pert._sim.state)
        _teardown(v_clean)
        _teardown(v_pert)

    def test_mag_slider_updates_pert_max(self, qt_app):
        v = _build(qt_app, CartPoleView)
        v._on_mag_changed(45)
        assert v._pert_max == pytest.approx(45.0)
        _teardown(v)


# ── CartPole cart color at track limits ───────────────────────────────────────


class TestCartPoleTrackColor:
    def _cart_rgb(self, v):
        p = v._actors["cart"].GetProperty()
        return (p.GetColor()[0], p.GetColor()[1], p.GetColor()[2])

    def test_normal_color_near_center(self, qt_app):
        from synapsys.viz.simview.cartpole import _CART_RGB_NORMAL

        v = _build(qt_app, CartPoleView)
        v._update_scene(v._actors, np.array([0.0, 0.0, 0.0, 0.0]), np.zeros(1))
        rgb = self._cart_rgb(v)
        assert rgb == pytest.approx(_CART_RGB_NORMAL, abs=0.01)
        _teardown(v)

    def test_warn_color_near_limit(self, qt_app):
        from synapsys.viz.simview.cartpole import _CART_RGB_WARN

        v = _build(qt_app, CartPoleView)
        x_warn = np.array([_TRACK_HW * (_WARN_FRAC + 0.02), 0.0, 0.0, 0.0])
        v._update_scene(v._actors, x_warn, np.zeros(1))
        rgb = self._cart_rgb(v)
        assert rgb == pytest.approx(_CART_RGB_WARN, abs=0.01)
        _teardown(v)

    def test_danger_color_at_limit(self, qt_app):
        from synapsys.viz.simview.cartpole import _CART_RGB_LIMIT

        v = _build(qt_app, CartPoleView)
        x_crit = np.array([_TRACK_HW * (_LIMIT_FRAC + 0.01), 0.0, 0.0, 0.0])
        v._update_scene(v._actors, x_crit, np.zeros(1))
        rgb = self._cart_rgb(v)
        assert rgb == pytest.approx(_CART_RGB_LIMIT, abs=0.01)
        _teardown(v)


# ── auto-reset at track limit ─────────────────────────────────────────────────


class TestCartPoleAutoReset:
    def test_post_tick_resets_at_limit(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 5)
        x_beyond = np.array([_TRACK_HW * _LIMIT_FRAC + 0.1, 0.0, 0.0, 0.0])
        v._post_tick(x_beyond, np.zeros(1))
        # After auto-reset, time should be 0
        assert v._t == pytest.approx(0.0)
        _teardown(v)

    def test_no_reset_within_safe_zone(self, qt_app):
        v = _build(qt_app, CartPoleView)
        _run_ticks(v, 5)
        t_before = v._t
        x_safe = np.array([_TRACK_HW * 0.5, 0.0, 0.0, 0.0])
        v._post_tick(x_safe, np.zeros(1))
        assert v._t == pytest.approx(t_before)
        _teardown(v)


# ── ctrl label after build ────────────────────────────────────────────────────


class TestCtrlLabelAfterBuild:
    def test_lqr_label_set_after_build(self, qt_app):
        v = _build(qt_app, CartPoleView)
        assert v._ctrl_label == "LQR (auto)"
        _teardown(v)

    def test_named_fn_label_set_after_build(self, qt_app):
        def cool_agent(x):
            return np.zeros(1)

        v = _build(qt_app, CartPoleView, controller=cool_agent)
        assert v._ctrl_label == "cool_agent"
        _teardown(v)

    def test_lambda_label_set_after_build(self, qt_app):
        v = _build(qt_app, CartPoleView, controller=lambda x: np.zeros(1))
        assert v._ctrl_label == "controller"
        _teardown(v)
