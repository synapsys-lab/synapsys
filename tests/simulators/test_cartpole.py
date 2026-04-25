"""Tests for CartPoleSim.

Analytical linearisation at upright equilibrium (θ=0, ṗ=0, θ̇=0, F=0):

  A = [[0,  1,            0,           0],
       [0,  0,  -m_p·g/m_c,            0],
       [0,  0,            0,           1],
       [0,  0,  (m_c+m_p)·g/(m_c·l),  0]]

  B = [[0], [1/m_c], [0], [-1/(m_c·l)]]
  C = [[1, 0, 0, 0], [0, 0, 1, 0]]
  D = [[0], [0]]
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

from synapsys.simulators.cartpole import CartPoleSim


@pytest.fixture()
def sim() -> CartPoleSim:
    s = CartPoleSim(m_c=1.0, m_p=0.1, l=0.5, g=9.81, integrator="rk4")
    s.reset()
    return s


def _analytical_jacobians(m_c, m_p, l, g):
    A = np.array(
        [
            [0, 1, 0, 0],
            [0, 0, -(m_p * g) / m_c, 0],
            [0, 0, 0, 1],
            [0, 0, (m_c + m_p) * g / (m_c * l), 0],
        ]
    )
    B = np.array([[0], [1 / m_c], [0], [-1 / (m_c * l)]])
    C = np.array([[1, 0, 0, 0], [0, 0, 1, 0]])
    D = np.zeros((2, 1))
    return A, B, C, D


# ── Construction ──────────────────────────────────────────────────────────────


class TestConstruction:
    def test_default_params(self):
        s = CartPoleSim()
        p = s.params
        assert p["m_c"] == pytest.approx(1.0)
        assert p["m_p"] == pytest.approx(0.1)
        assert p["l"] == pytest.approx(0.5)
        assert p["g"] == pytest.approx(9.81)

    def test_custom_params(self):
        s = CartPoleSim(m_c=2.0, m_p=0.5, l=1.0, g=9.8)
        p = s.params
        assert p["m_c"] == pytest.approx(2.0)
        assert p["m_p"] == pytest.approx(0.5)

    def test_dimensions(self, sim):
        assert sim.state_dim == 4
        assert sim.input_dim == 1
        assert sim.output_dim == 2


# ── reset ─────────────────────────────────────────────────────────────────────


class TestReset:
    def test_default_reset_zeros(self, sim):
        y = sim.reset()
        np.testing.assert_array_equal(y, np.zeros(2))
        np.testing.assert_array_equal(sim.state, np.zeros(4))

    def test_custom_x0(self, sim):
        x0 = np.array([1.0, 0.0, 0.1, 0.0])
        y = sim.reset(x0=x0)
        assert y[0] == pytest.approx(1.0)
        assert y[1] == pytest.approx(0.1)

    def test_wrong_x0_length_raises(self, sim):
        with pytest.raises(ValueError, match="length 4"):
            sim.reset(x0=np.array([1.0, 2.0]))


# ── output ────────────────────────────────────────────────────────────────────


class TestOutput:
    def test_output_is_partial(self, sim):
        x = np.array([1.5, 2.0, 0.3, -0.1])
        y = sim.output(x)
        assert y[0] == pytest.approx(1.5)  # position
        assert y[1] == pytest.approx(0.3)  # angle
        assert y.shape == (2,)

    def test_velocities_not_in_output(self, sim):
        x = np.array([0.0, 5.0, 0.0, 7.0])
        y = sim.output(x)
        assert y[0] == pytest.approx(0.0)
        assert y[1] == pytest.approx(0.0)


# ── dynamics ──────────────────────────────────────────────────────────────────


class TestDynamics:
    def test_upright_equilibrium_no_force(self, sim):
        """At θ=0, ṗ=0, θ̇=0, F=0 → all derivatives are zero."""
        x = np.zeros(4)
        u = np.zeros(1)
        dx = sim.dynamics(x, u)
        np.testing.assert_allclose(dx, np.zeros(4), atol=1e-12)

    def test_positive_force_accelerates_cart(self, sim):
        x = np.zeros(4)
        u = np.array([5.0])
        dx = sim.dynamics(x, u)
        assert dx[1] > 0  # ṗ̈ > 0

    def test_positive_force_tips_pole_backward(self, sim):
        """F>0 pushes cart right → pole tips left (θ̈ < 0 for small θ)."""
        x = np.zeros(4)
        u = np.array([5.0])
        dx = sim.dynamics(x, u)
        assert dx[3] < 0  # θ̈ < 0

    def test_small_angle_gravity_destabilises(self, sim):
        """Small positive θ → pole falls further (θ̈ > 0) with no force."""
        x = np.array([0.0, 0.0, 0.05, 0.0])
        u = np.zeros(1)
        dx = sim.dynamics(x, u)
        assert dx[3] > 0

    def test_output_shape(self, sim):
        dx = sim.dynamics(np.zeros(4), np.zeros(1))
        assert dx.shape == (4,)


# ── step ──────────────────────────────────────────────────────────────────────


class TestStep:
    def test_step_returns_y_and_info(self, sim):
        y, info = sim.step(np.zeros(1), dt=0.01)
        assert y.shape == (2,)
        assert "x" in info and "t_step" in info

    def test_upright_stays_upright_with_no_force(self, sim):
        for _ in range(100):
            y, _ = sim.step(np.zeros(1), dt=0.01)
        np.testing.assert_allclose(y, np.zeros(2), atol=1e-12)

    def test_unstable_without_control(self, sim):
        """Small perturbation + no control → pole falls."""
        sim.reset(x0=np.array([0.0, 0.0, 0.05, 0.0]))
        for _ in range(200):
            y, _ = sim.step(np.zeros(1), dt=0.01)
        assert abs(y[1]) > 0.05  # angle grew

    def test_lqr_stabilises_pole(self, sim):
        """LQR designed on linearised model must stabilise a small perturbation."""
        from synapsys.algorithms.lqr import lqr

        m_c, m_p, l, g = 1.0, 0.1, 0.5, 9.81
        A, B, C, D = _analytical_jacobians(m_c, m_p, l, g)
        K, _ = lqr(A, B, np.diag([1.0, 1.0, 10.0, 1.0]), np.eye(1))

        sim.reset(x0=np.array([0.0, 0.0, 0.1, 0.0]))
        for _ in range(500):
            x = sim.state
            u = -K @ x
            y, _ = sim.step(u, dt=0.01)

        assert abs(y[1]) < 0.01  # pole angle ≈ 0


# ── linearize ────────────────────────────────────────────────────────────────


class TestLinearize:
    def test_A_matches_analytical(self, sim):
        A_an, _, _, _ = _analytical_jacobians(1.0, 0.1, 0.5, 9.81)
        ss = sim.linearize(np.zeros(4), np.zeros(1))
        np.testing.assert_allclose(ss.A, A_an, atol=1e-5)

    def test_B_matches_analytical(self, sim):
        _, B_an, _, _ = _analytical_jacobians(1.0, 0.1, 0.5, 9.81)
        ss = sim.linearize(np.zeros(4), np.zeros(1))
        np.testing.assert_allclose(ss.B, B_an, atol=1e-5)

    def test_C_matches_analytical(self, sim):
        _, _, C_an, _ = _analytical_jacobians(1.0, 0.1, 0.5, 9.81)
        ss = sim.linearize(np.zeros(4), np.zeros(1))
        np.testing.assert_allclose(ss.C, C_an, atol=1e-6)

    def test_D_is_zero(self, sim):
        ss = sim.linearize(np.zeros(4), np.zeros(1))
        np.testing.assert_allclose(ss.D, np.zeros((2, 1)), atol=1e-10)

    def test_linearised_system_is_unstable(self, sim):
        """Open-loop cart-pole must have at least one unstable eigenvalue."""
        ss = sim.linearize(np.zeros(4), np.zeros(1))
        eigvals = np.linalg.eigvals(ss.A)
        assert np.any(np.real(eigvals) > 1e-6)

    def test_does_not_mutate_state(self, sim):
        sim.reset(x0=np.array([0.5, 0.0, 0.2, 0.0]))
        before = sim.state.copy()
        sim.linearize(np.zeros(4), np.zeros(1))
        np.testing.assert_array_equal(sim.state, before)


# ── set_params ────────────────────────────────────────────────────────────────


class TestSetParams:
    def test_update_mass_changes_dynamics(self, sim):
        x = np.zeros(4)
        u = np.array([1.0])
        dx_before = sim.dynamics(x, u).copy()
        sim.set_params(m_c=2.0)
        dx_after = sim.dynamics(x, u)
        assert not np.allclose(dx_before, dx_after)

    def test_update_pole_mass_stored(self, sim):
        sim.set_params(m_p=0.5)
        assert sim.params["m_p"] == pytest.approx(0.5)

    def test_update_length_stored(self, sim):
        sim.set_params(l=1.0)
        assert sim.params["l"] == pytest.approx(1.0)

    def test_update_gravity_stored(self, sim):
        sim.set_params(g=1.62)
        assert sim.params["g"] == pytest.approx(1.62)

    def test_unknown_param_raises(self, sim):
        with pytest.raises(ValueError, match="Unknown parameters"):
            sim.set_params(friction=0.5)

    def test_thread_safe_update(self, sim):
        errors: list[Exception] = []

        def updater():
            try:
                for i in range(50):
                    sim.set_params(m_c=1.0 + i * 0.01)
            except Exception as exc:
                errors.append(exc)

        def stepper():
            try:
                for _ in range(50):
                    sim.step(np.zeros(1), dt=0.01)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=updater), threading.Thread(target=stepper)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []


# ── linearised mode ───────────────────────────────────────────────────────────


class TestLinearisedMode:
    def test_linearised_false_is_default(self):
        sim = CartPoleSim()
        assert sim.linearised is False

    def test_linearised_true_constructor(self):
        sim = CartPoleSim(linearised=True)
        assert sim.linearised is True

    def test_linearised_dynamics_matches_nonlinear_near_upright(self):
        x0 = np.array([0.0, 0.0, 0.01, 0.0])
        u0 = np.zeros(1)
        sim_nl = CartPoleSim(linearised=False)
        sim_l = CartPoleSim(linearised=True)
        sim_nl.reset(x0=x0)
        sim_l.reset(x0=x0)
        y_nl, _ = sim_nl.step(u0, dt=0.01)
        y_l, _ = sim_l.step(u0, dt=0.01)
        np.testing.assert_allclose(y_nl, y_l, atol=1e-4)

    def test_linearised_dynamics_differs_from_nonlinear_at_large_angle(self):
        x0 = np.array([0.0, 0.0, 0.5, 0.0])
        u0 = np.zeros(1)
        sim_nl = CartPoleSim(linearised=False)
        sim_l = CartPoleSim(linearised=True)
        sim_nl.reset(x0=x0)
        sim_l.reset(x0=x0)
        y_nl, _ = sim_nl.step(u0, dt=0.1)
        y_l, _ = sim_l.step(u0, dt=0.1)
        assert not np.allclose(y_nl, y_l, atol=1e-3)


# ── failure detection ─────────────────────────────────────────────────────────


class TestFailureDetection:
    def test_info_contains_failed_key(self, sim):
        _, info = sim.step(np.zeros(1), dt=0.01)
        assert "failed" in info

    def test_not_failed_when_pole_upright(self, sim):
        _, info = sim.step(np.zeros(1), dt=0.01)
        assert info["failed"] is False

    def test_failed_when_pole_angle_exceeds_threshold(self):
        sim = CartPoleSim()
        sim.reset(x0=np.array([0.0, 0.0, 1.2, 0.0]))  # θ = 1.2 rad > π/3
        _, info = sim.step(np.zeros(1), dt=0.01)
        assert info["failed"] is True

    def test_failed_when_cart_out_of_bounds(self):
        sim = CartPoleSim()
        sim.reset(x0=np.array([5.0, 0.0, 0.0, 0.0]))  # p = 5 m
        _, info = sim.step(np.zeros(1), dt=0.01)
        assert info["failed"] is True
