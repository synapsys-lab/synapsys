"""Tests for synapsys.viz.simview — CartPoleView, PendulumView, MassSpringDamperView.

These tests cover the pure-Python layer of each view (no Qt/PyVista/matplotlib
required): instantiation, simulator creation, initial conditions, LQR weights,
history keys, ctrl-label inference, and MSD setpoint logic.
"""

from __future__ import annotations

import collections

import numpy as np
import pytest

pytest.importorskip(
    "matplotlib.backends.backend_qtagg",
    reason="Qt backend not available — skip SimView tests",
    exc_type=ImportError,
)

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import CartPoleSim, InvertedPendulumSim, MassSpringDamperSim
from synapsys.viz.simview.cartpole import _TRACK_HW, CartPoleView
from synapsys.viz.simview.cartpole import _X0 as _CP_X0
from synapsys.viz.simview.msd import (
    _DEFAULT_SETPOINTS,
    MassSpringDamperView,
)
from synapsys.viz.simview.msd import (
    _X0 as _MSD_X0,
)
from synapsys.viz.simview.pendulum import _X0 as _PD_X0
from synapsys.viz.simview.pendulum import PendulumView

# ── helpers ────────────────────────────────────────────────────────────────────


def _make_hist(view) -> dict:
    """Build a minimal history dict for a view (replicates _build_all logic)."""
    keys = ["t"] + view._extra_hist_keys()
    return {k: collections.deque(maxlen=view._hist_len) for k in keys}


def _setup_lqr(view) -> None:
    """Design and inject the LQR gain into a view without running Qt."""
    sim = view._make_sim()
    sim.reset()
    Q, R = view._lqr_weights()
    ss = sim.linearize(view._equilibrium(), np.zeros(sim.input_dim))
    view._K, _ = lqr(ss.A, ss.B, Q, R)
    view._sim = sim
    view._hist = _make_hist(view)


# ── instantiation ──────────────────────────────────────────────────────────────


class TestInstantiation:
    def test_cartpole_no_controller(self):
        v = CartPoleView()
        assert v._controller_fn is None
        assert v._ctrl_label == "LQR (auto)"
        assert v._paused is False

    def test_cartpole_custom_controller(self):
        def my_ctrl(x):
            return np.zeros(1)

        v = CartPoleView(controller=my_ctrl)
        assert v._controller_fn is my_ctrl

    def test_pendulum_no_controller(self):
        v = PendulumView()
        assert v._controller_fn is None

    def test_msd_no_controller(self):
        v = MassSpringDamperView()
        assert v._controller_fn is None
        assert v._setpoint == _DEFAULT_SETPOINTS[0][1]

    def test_all_views_independent(self):
        # Instantiating multiple views must not share state
        v1 = CartPoleView()
        v2 = CartPoleView()
        v1._paused = True
        assert v2._paused is False


# ── simulator creation ─────────────────────────────────────────────────────────


class TestSimulatorCreation:
    def test_cartpole_default_params(self):
        v = CartPoleView()
        sim = v._make_sim()
        assert isinstance(sim, CartPoleSim)
        assert sim._m_c == pytest.approx(1.0)
        assert sim._m_p == pytest.approx(0.1)
        assert sim._l == pytest.approx(0.5)

    def test_cartpole_custom_params(self):
        v = CartPoleView(m_c=2.0, m_p=0.3, l=0.8, g=9.0)
        sim = v._make_sim()
        assert sim._m_c == pytest.approx(2.0)
        assert sim._m_p == pytest.approx(0.3)
        assert sim._l == pytest.approx(0.8)

    def test_pendulum_default_params(self):
        v = PendulumView()
        sim = v._make_sim()
        assert isinstance(sim, InvertedPendulumSim)
        assert sim._m == pytest.approx(1.0)
        assert sim._l == pytest.approx(1.0)

    def test_pendulum_custom_params(self):
        v = PendulumView(m=0.5, l=1.5, b=0.2)
        sim = v._make_sim()
        assert sim._m == pytest.approx(0.5)
        assert sim._l == pytest.approx(1.5)

    def test_msd_default_params(self):
        v = MassSpringDamperView()
        sim = v._make_sim()
        assert isinstance(sim, MassSpringDamperSim)
        assert sim._m == pytest.approx(1.0)
        assert sim._c == pytest.approx(0.5)
        assert sim._k == pytest.approx(2.0)

    def test_msd_custom_params(self):
        v = MassSpringDamperView(m=2.0, c=1.0, k=5.0)
        sim = v._make_sim()
        assert sim._m == pytest.approx(2.0)
        assert sim._c == pytest.approx(1.0)
        assert sim._k == pytest.approx(5.0)


# ── initial conditions ─────────────────────────────────────────────────────────


class TestInitialConditions:
    def test_cartpole_default_x0(self):
        v = CartPoleView()
        x0 = v._x0()
        assert x0.shape == (4,)
        assert np.allclose(x0, _CP_X0)

    def test_cartpole_custom_x0(self):
        custom = np.array([0.5, 0.0, 0.3, 0.0])
        v = CartPoleView(x0=custom)
        assert np.allclose(v._x0(), custom)

    def test_cartpole_x0_returns_copy(self):
        custom = np.array([0.5, 0.0, 0.3, 0.0])
        v = CartPoleView(x0=custom)
        x0 = v._x0()
        x0[0] = 999.0
        assert v._x0()[0] == pytest.approx(0.5)

    def test_pendulum_default_x0(self):
        v = PendulumView()
        x0 = v._x0()
        assert x0.shape == (2,)
        assert np.allclose(x0, _PD_X0)

    def test_pendulum_custom_x0(self):
        custom = np.array([0.4, 0.1])
        v = PendulumView(x0=custom)
        assert np.allclose(v._x0(), custom)

    def test_msd_default_x0(self):
        v = MassSpringDamperView()
        x0 = v._x0()
        assert x0.shape == (2,)
        assert np.allclose(x0, _MSD_X0)

    def test_msd_custom_x0(self):
        custom = np.array([1.0, 0.5])
        v = MassSpringDamperView(x0=custom)
        assert np.allclose(v._x0(), custom)

    def test_equilibrium_is_zeros(self):
        for view_cls, n in [
            (CartPoleView, 4),
            (PendulumView, 2),
            (MassSpringDamperView, 2),
        ]:
            eq = view_cls()._equilibrium()
            assert eq.shape == (n,)
            assert np.allclose(eq, 0.0)


# ── LQR weights ────────────────────────────────────────────────────────────────


class TestLQRWeights:
    def test_cartpole_Q_R_shapes(self):
        Q, R = CartPoleView()._lqr_weights()
        assert Q.shape == (4, 4)
        assert R.shape == (1, 1)

    def test_cartpole_Q_diagonal_positive(self):
        Q, R = CartPoleView()._lqr_weights()
        assert np.all(np.diag(Q) > 0)
        assert float(R[0, 0]) > 0

    def test_pendulum_Q_R_shapes(self):
        Q, R = PendulumView()._lqr_weights()
        assert Q.shape == (2, 2)
        assert R.shape == (1, 1)

    def test_msd_Q_R_shapes(self):
        Q, R = MassSpringDamperView()._lqr_weights()
        assert Q.shape == (2, 2)
        assert R.shape == (1, 1)

    def test_lqr_design_succeeds_for_all_views(self):
        for view_cls in (CartPoleView, PendulumView, MassSpringDamperView):
            v = view_cls()
            sim = v._make_sim()
            sim.reset()
            Q, R = v._lqr_weights()
            ss = sim.linearize(v._equilibrium(), np.zeros(sim.input_dim))
            K, P = lqr(ss.A, ss.B, Q, R)
            assert K is not None
            assert K.shape[1] == ss.A.shape[0]


# ── history keys and append ────────────────────────────────────────────────────


class TestHistory:
    def test_cartpole_hist_keys(self):
        keys = CartPoleView()._extra_hist_keys()
        assert set(keys) == {"pos", "vel", "ang", "angv", "u"}

    def test_pendulum_hist_keys(self):
        keys = PendulumView()._extra_hist_keys()
        assert set(keys) == {"ang", "angv", "tau"}

    def test_msd_hist_keys(self):
        keys = MassSpringDamperView()._extra_hist_keys()
        assert set(keys) == {"q", "qdot", "u"}

    def test_cartpole_append_hist(self):
        v = CartPoleView()
        v._hist = _make_hist(v)
        x = np.array([0.1, 0.2, 0.05, 0.3])
        u = np.array([5.0])
        v._append_hist(x, u)
        assert v._hist["pos"][-1] == pytest.approx(0.1)
        assert v._hist["vel"][-1] == pytest.approx(0.2)
        assert v._hist["ang"][-1] == pytest.approx(np.degrees(0.05))
        assert v._hist["angv"][-1] == pytest.approx(np.degrees(0.3))
        assert v._hist["u"][-1] == pytest.approx(5.0)

    def test_pendulum_append_hist(self):
        v = PendulumView()
        v._hist = _make_hist(v)
        x = np.array([0.2, 1.0])
        u = np.array([3.5])
        v._append_hist(x, u)
        assert v._hist["ang"][-1] == pytest.approx(np.degrees(0.2))
        assert v._hist["angv"][-1] == pytest.approx(np.degrees(1.0))
        assert v._hist["tau"][-1] == pytest.approx(3.5)

    def test_msd_append_hist(self):
        v = MassSpringDamperView()
        v._hist = _make_hist(v)
        x = np.array([1.5, -0.3])
        u = np.array([2.0])
        v._append_hist(x, u)
        assert v._hist["q"][-1] == pytest.approx(1.5)
        assert v._hist["qdot"][-1] == pytest.approx(-0.3)
        assert v._hist["u"][-1] == pytest.approx(2.0)

    def test_hist_respects_maxlen(self):
        v = CartPoleView()
        v._hist = _make_hist(v)
        x = np.array([0.0, 0.0, 0.0, 0.0])
        u = np.array([0.0])
        for _ in range(v._hist_len + 50):
            v._append_hist(x, u)
        assert len(v._hist["pos"]) == v._hist_len


# ── ctrl label ─────────────────────────────────────────────────────────────────


class TestCtrlLabel:
    def test_default_is_lqr_auto(self):
        assert CartPoleView()._ctrl_label == "LQR (auto)"
        assert PendulumView()._ctrl_label == "LQR (auto)"
        assert MassSpringDamperView()._ctrl_label == "LQR (auto)"

    def test_named_function_label(self):
        def my_policy(x):
            return np.zeros(1)

        # Replicate the label logic from _build_all
        name = getattr(my_policy, "__name__", None)
        label = name if (name and name != "<lambda>") else "controller"
        assert label == "my_policy"

    def test_lambda_label(self):
        fn = lambda x: np.zeros(1)
        name = getattr(fn, "__name__", None)
        label = name if (name and name != "<lambda>") else "controller"
        assert label == "controller"

    def test_callable_class_label(self):
        class MyAgent:
            def __call__(self, x):
                return np.zeros(1)

        agent = MyAgent()
        name = getattr(agent, "__name__", None)
        label = name if (name and name != "<lambda>") else "controller"
        assert label == "controller"


# ── MSD setpoints ──────────────────────────────────────────────────────────────


class TestMSDSetpoints:
    def test_default_setpoints(self):
        v = MassSpringDamperView()
        assert v._setpoints == _DEFAULT_SETPOINTS

    def test_default_initial_setpoint(self):
        v = MassSpringDamperView()
        assert v._setpoint == pytest.approx(_DEFAULT_SETPOINTS[0][1])

    def test_custom_setpoints(self):
        custom = [("0", 0.0), ("+3m", 3.0), ("-3m", -3.0)]
        v = MassSpringDamperView(setpoints=custom)
        assert v._setpoints == custom
        assert v._setpoint == pytest.approx(0.0)

    def test_custom_setpoints_first_is_initial(self):
        custom = [("+2m", 2.0), ("0", 0.0)]
        v = MassSpringDamperView(setpoints=custom)
        assert v._setpoint == pytest.approx(2.0)

    def test_set_setpoint_updates_value(self):
        v = MassSpringDamperView()
        v._set_setpoint(1.5)
        assert v._setpoint == pytest.approx(1.5)

    def test_on_reset_returns_to_first_setpoint(self):
        custom = [("+1m", 1.0), ("0", 0.0)]
        v = MassSpringDamperView(setpoints=custom)
        _setup_lqr(v)
        v._set_setpoint(0.0)  # change setpoint
        v._on_reset()
        assert v._setpoint == pytest.approx(1.0)


# ── MSD LQR with setpoint tracking ────────────────────────────────────────────


class TestMSDLQRu:
    @pytest.fixture
    def msd_view(self):
        v = MassSpringDamperView()
        _setup_lqr(v)
        return v

    def test_u_at_origin_no_setpoint(self, msd_view):
        msd_view._setpoint = 0.0
        u = msd_view._lqr_u(np.zeros(2))
        assert np.allclose(u, 0.0, atol=1e-10)

    def test_u_shape(self, msd_view):
        u = msd_view._lqr_u(np.zeros(2))
        assert u.shape == (1,)

    def test_u_at_setpoint_position(self, msd_view):
        sp = 1.5
        msd_view._setpoint = sp
        x_at_sp = np.array([sp, 0.0])
        u = msd_view._lqr_u(x_at_sp)
        # error term = 0, only feed-forward: u = k * sp
        expected = msd_view._k * sp
        assert float(u[0]) == pytest.approx(expected, rel=1e-6)

    def test_u_opposes_positive_error(self, msd_view):
        msd_view._setpoint = 0.0
        x_right = np.array([0.5, 0.0])  # mass to the right of target
        u = msd_view._lqr_u(x_right)
        assert float(u[0]) < 0.0  # controller pushes left

    def test_u_opposes_negative_error(self, msd_view):
        msd_view._setpoint = 0.0
        x_left = np.array([-0.5, 0.0])
        u = msd_view._lqr_u(x_left)
        assert float(u[0]) > 0.0  # controller pushes right


# ── CartPole track limit constants ────────────────────────────────────────────


class TestCartPoleTrackLimits:
    def test_track_hw_positive(self):
        assert _TRACK_HW > 0

    def test_warn_frac_lt_limit_frac(self):
        from synapsys.viz.simview.cartpole import _LIMIT_FRAC, _WARN_FRAC

        assert _WARN_FRAC < _LIMIT_FRAC
        assert _LIMIT_FRAC < 1.0

    def test_pert_vector_default(self):
        v = CartPoleView()
        v._pert = 5.0
        pv = v._pert_vector()
        assert pv.shape == (1,)
        assert float(pv[0]) == pytest.approx(5.0)

    def test_pert_vector_zero(self):
        v = CartPoleView()
        v._pert = 0.0
        assert np.allclose(v._pert_vector(), 0.0)


# ── camera presets ─────────────────────────────────────────────────────────────


class TestCameraPresets:
    def test_camera_presets_dict_exists(self):
        from synapsys.viz.simview._base import CAMERA_PRESETS

        assert isinstance(CAMERA_PRESETS, dict)

    def test_camera_presets_has_expected_keys(self):
        from synapsys.viz.simview._base import CAMERA_PRESETS

        for key in ("iso", "top", "side", "follow"):
            assert key in CAMERA_PRESETS

    def test_each_preset_is_three_tuple(self):
        from synapsys.viz.simview._base import CAMERA_PRESETS

        for name, preset in CAMERA_PRESETS.items():
            assert len(preset) == 3, f"preset {name!r} must be a 3-tuple"

    def test_set_camera_preset_updates_cam_pos(self):
        v = CartPoleView()
        v.set_camera_preset("top")
        from synapsys.viz.simview._base import CAMERA_PRESETS

        assert v._cam_pos == CAMERA_PRESETS["top"]

    def test_set_camera_preset_iso(self):
        v = CartPoleView()
        v.set_camera_preset("iso")
        from synapsys.viz.simview._base import CAMERA_PRESETS

        assert v._cam_pos == CAMERA_PRESETS["iso"]

    def test_set_camera_preset_unknown_raises(self):
        v = CartPoleView()
        with pytest.raises(KeyError):
            v.set_camera_preset("nonexistent")


# ── trajectory trail state ─────────────────────────────────────────────────────


class TestTrailState:
    def test_trail_disabled_by_default(self):
        v = CartPoleView()
        assert v._trail_enabled is False

    def test_trail_max_pts_positive(self):
        v = CartPoleView()
        assert v._trail_max_pts > 0

    def test_toggle_trail_enables(self):
        v = CartPoleView()
        v.toggle_trail()
        assert v._trail_enabled is True

    def test_toggle_trail_disables(self):
        v = CartPoleView()
        v._trail_enabled = True
        v.toggle_trail()
        assert v._trail_enabled is False

    def test_trail_positions_empty_on_init(self):
        v = CartPoleView()
        assert len(v._trail_positions) == 0

    def test_append_trail_position_stores_point(self):
        v = CartPoleView()
        v._append_trail_position(np.array([1.0, 0.0, 0.5]))
        assert len(v._trail_positions) == 1

    def test_trail_positions_respect_max_pts(self):
        v = CartPoleView()
        for i in range(v._trail_max_pts + 10):
            v._append_trail_position(np.array([float(i), 0.0, 0.0]))
        assert len(v._trail_positions) <= v._trail_max_pts
