"""Tests for SimulatorBase contract.

Uses a DoubleIntegrator (ẋ₁=x₂, ẋ₂=u, y=[x₁,x₂]) as the concrete fixture
because its exact solution and analytical Jacobian are known.
"""

from __future__ import annotations

import threading
from typing import Any

import numpy as np
import pytest

from synapsys.core.state_space import StateSpace
from synapsys.simulators import SimulatorBase

# ── Concrete fixture ──────────────────────────────────────────────────────────


class DoubleIntegrator(SimulatorBase):
    """ẋ = [x₂, u]  y = [x₁, x₂]  — exact Jacobians known analytically."""

    @property
    def state_dim(self) -> int:
        return 2

    @property
    def input_dim(self) -> int:
        return 1

    @property
    def output_dim(self) -> int:
        return 2

    def dynamics(self, x, u):
        return np.array([x[1], u[0]])

    def output(self, x):
        return x.copy()

    def reset(self, x0=None, **kwargs):
        self._x = np.asarray(x0, dtype=float) if x0 is not None else np.zeros(2)
        return self.output(self._x)

    def set_params(self, **kwargs: Any) -> None:
        pass


@pytest.fixture()
def sim():
    s = DoubleIntegrator(integrator="rk4")
    s.reset()
    return s


# ── Construction ──────────────────────────────────────────────────────────────


class TestConstruction:
    def test_invalid_integrator_raises(self):
        with pytest.raises(ValueError, match="integrator"):
            DoubleIntegrator(integrator="bogus")

    def test_default_integrator_is_rk4(self):
        s = DoubleIntegrator()
        assert s._integrate.__name__ == "rk4"

    def test_euler_integrator_accepted(self):
        s = DoubleIntegrator(integrator="euler")
        assert s._integrate.__name__ == "euler"

    def test_rk45_integrator_accepted(self):
        s = DoubleIntegrator(integrator="rk45")
        assert s._integrate.__name__ == "rk45"

    def test_noise_std_stored(self):
        s = DoubleIntegrator(noise_std=0.5)
        assert s._noise_std == pytest.approx(0.5)

    def test_disturbance_std_stored(self):
        s = DoubleIntegrator(disturbance_std=0.3)
        assert s._disturbance_std == pytest.approx(0.3)

    def test_disturbance_applied_during_step(self):
        np.random.seed(0)
        s = DoubleIntegrator(disturbance_std=1e6)
        s.reset()
        y, _ = s.step(np.zeros(1), dt=0.01)
        assert abs(y[0]) > 1.0


# ── state property ────────────────────────────────────────────────────────────


class TestStateProperty:
    def test_returns_copy_not_reference(self, sim):
        s1 = sim.state
        s1[0] = 999.0
        assert sim.state[0] != 999.0

    def test_initial_state_is_zeros(self, sim):
        np.testing.assert_array_equal(sim.state, np.zeros(2))

    def test_reset_sets_state(self, sim):
        sim.reset(x0=np.array([1.0, 2.0]))
        np.testing.assert_array_equal(sim.state, [1.0, 2.0])


# ── step ──────────────────────────────────────────────────────────────────────


class TestStep:
    def test_position_after_unit_force_for_one_second(self, sim):
        u = np.array([1.0])
        for _ in range(100):
            y, _ = sim.step(u, dt=0.01)
        assert y[0] == pytest.approx(0.5, rel=1e-5)
        assert y[1] == pytest.approx(1.0, rel=1e-5)

    def test_returns_y_and_info_dict(self, sim):
        y, info = sim.step(np.array([0.0]), dt=0.1)
        assert isinstance(y, np.ndarray)
        assert "x" in info
        assert "t_step" in info
        assert info["t_step"] == pytest.approx(0.1)

    def test_info_x_matches_state(self, sim):
        _, info = sim.step(np.array([1.0]), dt=0.1)
        np.testing.assert_array_equal(info["x"], sim.state)

    def test_info_x_is_copy(self, sim):
        _, info = sim.step(np.array([0.0]), dt=0.1)
        info["x"][0] = 999.0
        assert sim.state[0] != 999.0

    def test_wrong_input_dim_raises(self, sim):
        with pytest.raises(ValueError, match="input_dim"):
            sim.step(np.array([1.0, 2.0]), dt=0.1)

    def test_output_shape(self, sim):
        y, _ = sim.step(np.array([0.0]), dt=0.1)
        assert y.shape == (sim.output_dim,)

    def test_zero_input_state_unchanged(self, sim):
        for _ in range(10):
            y, _ = sim.step(np.array([0.0]), dt=0.1)
        np.testing.assert_array_almost_equal(y, np.zeros(2))

    def test_noise_perturbs_output(self):
        s = DoubleIntegrator(noise_std=1.0)
        s.reset()
        ys = [s.step(np.zeros(1), dt=0.1)[0] for _ in range(100)]
        vals = np.stack(ys)
        assert vals.std(axis=0).max() > 0.1

    def test_noiseless_output_is_deterministic(self, sim):
        sim.reset(x0=np.array([1.0, 0.5]))
        y1, _ = sim.step(np.array([0.5]), dt=0.05)
        sim.reset(x0=np.array([1.0, 0.5]))
        y2, _ = sim.step(np.array([0.5]), dt=0.05)
        np.testing.assert_array_equal(y1, y2)


# ── linearize ────────────────────────────────────────────────────────────────


class TestLinearize:
    def test_returns_state_space(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        assert isinstance(ss, StateSpace)

    def test_continuous_time(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        assert ss.dt == pytest.approx(0.0)

    def test_A_matrix_double_integrator(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        expected_A = np.array([[0.0, 1.0], [0.0, 0.0]])
        np.testing.assert_allclose(ss.A, expected_A, atol=1e-6)

    def test_B_matrix_double_integrator(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        expected_B = np.array([[0.0], [1.0]])
        np.testing.assert_allclose(ss.B, expected_B, atol=1e-6)

    def test_C_matrix_full_state_output(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.C, np.eye(2), atol=1e-6)

    def test_D_matrix_is_zero(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.D, np.zeros((2, 1)), atol=1e-10)

    def test_matrix_shapes(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        assert ss.A.shape == (2, 2)
        assert ss.B.shape == (2, 1)
        assert ss.C.shape == (2, 2)
        assert ss.D.shape == (2, 1)

    def test_linearize_does_not_mutate_state(self, sim):
        sim.reset(x0=np.array([1.0, 2.0]))
        before = sim.state.copy()
        sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_array_equal(sim.state, before)


# ── thread safety ─────────────────────────────────────────────────────────────


class TestThreadSafety:
    def test_concurrent_steps_do_not_crash(self):
        """Multiple threads stepping the same simulator must not raise."""
        s = DoubleIntegrator()
        s.reset()
        errors: list[Exception] = []

        def worker():
            try:
                for _ in range(50):
                    s.step(np.array([0.1]), dt=0.01)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"


# ── ABC enforcement ───────────────────────────────────────────────────────────


class TestAbstractEnforcement:
    def test_cannot_instantiate_base_directly(self):
        with pytest.raises(TypeError):
            SimulatorBase()  # type: ignore[abstract]

    def test_missing_dynamics_raises(self):
        class Incomplete(SimulatorBase):
            state_dim = property(lambda self: 1)
            input_dim = property(lambda self: 1)
            output_dim = property(lambda self: 1)

            def output(self, x):
                return x

            def reset(self, **kw): ...
            def set_params(self, **kw): ...

        with pytest.raises(TypeError):
            Incomplete()
