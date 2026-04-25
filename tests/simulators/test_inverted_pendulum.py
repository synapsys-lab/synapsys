"""Tests for InvertedPendulumSim.

Analytical linearisation at upright equilibrium (θ=0, τ=0):

  A = [[0,         1        ],
       [g/l,  −b/(m·l²)    ]]

  B = [[     0    ],
       [1/(m·l²)  ]]

  C = [[1, 0]]
  D = [[0]]

Unstable eigenvalue (b=0): λ = +√(g/l).
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

from synapsys.simulators.inverted_pendulum import InvertedPendulumSim


@pytest.fixture()
def sim() -> InvertedPendulumSim:
    s = InvertedPendulumSim(m=1.0, l=1.0, g=9.81, b=0.0, integrator="rk4")
    s.reset()
    return s


def _analytical_matrices(m, l, g, b):
    I = m * l**2
    A = np.array([[0.0, 1.0], [g / l, -b / I]])
    B = np.array([[0.0], [1.0 / I]])
    C = np.array([[1.0, 0.0]])
    D = np.array([[0.0]])
    return A, B, C, D


# ── Construction ──────────────────────────────────────────────────────────────


class TestConstruction:
    def test_default_params(self):
        s = InvertedPendulumSim()
        p = s.params
        assert p["m"] == pytest.approx(1.0)
        assert p["l"] == pytest.approx(1.0)
        assert p["g"] == pytest.approx(9.81)
        assert p["b"] == pytest.approx(0.0)

    def test_custom_params(self):
        s = InvertedPendulumSim(m=0.5, l=0.75, g=9.8, b=0.1)
        p = s.params
        assert p["m"] == pytest.approx(0.5)
        assert p["l"] == pytest.approx(0.75)
        assert p["b"] == pytest.approx(0.1)

    def test_dimensions(self, sim):
        assert sim.state_dim == 2
        assert sim.input_dim == 1
        assert sim.output_dim == 1

    def test_unstable_pole(self):
        s = InvertedPendulumSim(m=1.0, l=1.0, g=9.81)
        assert s.unstable_pole() == pytest.approx(np.sqrt(9.81), rel=1e-9)


# ── reset ─────────────────────────────────────────────────────────────────────


class TestReset:
    def test_default_zeros(self, sim):
        y = sim.reset()
        assert y[0] == pytest.approx(0.0)
        np.testing.assert_array_equal(sim.state, np.zeros(2))

    def test_custom_x0(self, sim):
        y = sim.reset(x0=np.array([0.2, 0.0]))
        assert y[0] == pytest.approx(0.2)

    def test_wrong_x0_length_raises(self, sim):
        with pytest.raises(ValueError, match="length 2"):
            sim.reset(x0=np.array([1.0, 2.0, 3.0]))


# ── output ────────────────────────────────────────────────────────────────────


class TestOutput:
    def test_returns_angle_only(self, sim):
        x = np.array([0.5, 2.0])
        y = sim.output(x)
        assert y.shape == (1,)
        assert y[0] == pytest.approx(0.5)

    def test_angular_velocity_not_in_output(self, sim):
        x = np.array([0.0, 3.14])
        y = sim.output(x)
        assert y[0] == pytest.approx(0.0)


# ── dynamics ──────────────────────────────────────────────────────────────────


class TestDynamics:
    def test_upright_equilibrium_exact(self, sim):
        """θ=0, θ̇=0, τ=0 → all derivatives zero."""
        dx = sim.dynamics(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(dx, np.zeros(2), atol=1e-14)

    def test_small_positive_angle_falls_away(self, sim):
        """θ>0 with no torque → θ̈>0 (gravity destabilises)."""
        x = np.array([0.1, 0.0])
        dx = sim.dynamics(x, np.zeros(1))
        assert dx[0] == pytest.approx(0.0)  # θ̇ = 0
        assert dx[1] > 0  # θ̈ > 0 — falls further

    def test_positive_torque_accelerates(self, sim):
        dx = sim.dynamics(np.zeros(2), np.array([2.0]))
        assert dx[1] > 0

    def test_friction_opposes_motion(self):
        s = InvertedPendulumSim(m=1.0, l=1.0, g=0.0, b=1.0)
        x = np.array([0.0, 1.0])  # θ̇ > 0, no gravity
        dx_no_b = InvertedPendulumSim(m=1.0, l=1.0, g=0.0, b=0.0).dynamics(
            x, np.zeros(1)
        )
        dx_with_b = s.dynamics(x, np.zeros(1))
        assert dx_with_b[1] < dx_no_b[1]  # friction reduces θ̈

    def test_matches_analytical_formula(self):
        m, l, g, b = 0.5, 0.8, 9.81, 0.2
        s = InvertedPendulumSim(m=m, l=l, g=g, b=b)
        x = np.array([0.3, -0.5])
        u = np.array([1.0])
        dx = s.dynamics(x, u)
        I = m * l**2
        expected = np.array([x[1], (g / l) * np.sin(x[0]) - (b / I) * x[1] + u[0] / I])
        np.testing.assert_allclose(dx, expected, rtol=1e-12)

    def test_output_shape(self, sim):
        dx = sim.dynamics(np.zeros(2), np.zeros(1))
        assert dx.shape == (2,)


# ── step ──────────────────────────────────────────────────────────────────────


class TestStep:
    def test_upright_stays_with_zero_torque(self, sim):
        for _ in range(100):
            y, _ = sim.step(np.zeros(1), dt=0.01)
        assert y[0] == pytest.approx(0.0, abs=1e-12)

    def test_falls_without_control(self, sim):
        """Small perturbation + zero torque → angle grows."""
        sim.reset(x0=np.array([0.05, 0.0]))
        for _ in range(100):
            y, _ = sim.step(np.zeros(1), dt=0.01)
        assert abs(y[0]) > 0.05

    def test_lqr_stabilises_upright(self, sim):
        """LQR designed on linear model must hold a small perturbation."""
        from synapsys.algorithms.lqr import lqr

        A, B, _, _ = _analytical_matrices(1.0, 1.0, 9.81, 0.0)
        K, _ = lqr(A, B, np.diag([10.0, 1.0]), np.eye(1))

        sim.reset(x0=np.array([0.1, 0.0]))
        for _ in range(1000):
            x = sim.state
            u = -K @ x
            y, _ = sim.step(u, dt=0.01)

        assert abs(y[0]) < 0.01

    def test_step_output_shape(self, sim):
        y, info = sim.step(np.zeros(1), dt=0.01)
        assert y.shape == (1,)
        assert "x" in info


# ── linearize ────────────────────────────────────────────────────────────────


class TestLinearize:
    def test_A_matches_analytical_frictionless(self, sim):
        A_an, _, _, _ = _analytical_matrices(1.0, 1.0, 9.81, 0.0)
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.A, A_an, atol=1e-5)

    def test_A_matches_analytical_with_friction(self):
        m, l, g, b = 1.0, 1.0, 9.81, 0.5
        s = InvertedPendulumSim(m=m, l=l, g=g, b=b)
        s.reset()
        A_an, _, _, _ = _analytical_matrices(m, l, g, b)
        ss = s.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.A, A_an, atol=1e-5)

    def test_B_matches_analytical(self, sim):
        _, B_an, _, _ = _analytical_matrices(1.0, 1.0, 9.81, 0.0)
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.B, B_an, atol=1e-5)

    def test_C_matches_analytical(self, sim):
        _, _, C_an, _ = _analytical_matrices(1.0, 1.0, 9.81, 0.0)
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.C, C_an, atol=1e-6)

    def test_linearised_system_has_unstable_eigenvalue(self, sim):
        """Open-loop system must have at least one positive real eigenvalue."""
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        eigvals = np.linalg.eigvals(ss.A)
        assert np.any(np.real(eigvals) > 1e-3)

    def test_unstable_eigenvalue_matches_formula(self, sim):
        """Unstable pole must be ≈ +√(g/l)."""
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        pos_eig = max(np.real(np.linalg.eigvals(ss.A)))
        assert pos_eig == pytest.approx(np.sqrt(9.81 / 1.0), rel=1e-4)

    def test_does_not_mutate_state(self, sim):
        sim.reset(x0=np.array([0.3, 0.0]))
        before = sim.state.copy()
        sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_array_equal(sim.state, before)

    def test_continuous_time(self, sim):
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        assert ss.dt == pytest.approx(0.0)


# ── set_params ────────────────────────────────────────────────────────────────


class TestSetParams:
    def test_update_mass_stored(self, sim):
        sim.set_params(m=2.0)
        assert sim.params["m"] == pytest.approx(2.0)

    def test_update_gravity_stored(self, sim):
        sim.set_params(g=1.62)
        assert sim.params["g"] == pytest.approx(1.62)

    def test_unknown_param_raises(self, sim):
        with pytest.raises(ValueError, match="Unknown parameters"):
            sim.set_params(mass=2.0)

    def test_update_length_changes_unstable_pole(self, sim):
        pole_before = sim.unstable_pole()
        sim.set_params(l=0.5)
        pole_after = sim.unstable_pole()
        assert pole_after > pole_before  # shorter pole → faster divergence

    def test_friction_damps_free_motion(self):
        """Adding friction must reduce the rate of angle growth."""

        def _max_angle_after_n_steps(b, steps=50):
            s = InvertedPendulumSim(m=1.0, l=1.0, g=9.81, b=b)
            s.reset(x0=np.array([0.05, 0.0]))
            for _ in range(steps):
                y, _ = s.step(np.zeros(1), dt=0.01)
            return abs(y[0])

        assert _max_angle_after_n_steps(0.0) > _max_angle_after_n_steps(2.0)

    def test_thread_safe_update(self, sim):
        errors: list[Exception] = []

        def updater():
            try:
                for i in range(50):
                    sim.set_params(b=float(i) * 0.01)
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


# ── failure detection ─────────────────────────────────────────────────────────


class TestFailureDetection:
    def test_info_contains_failed_key(self, sim):
        _, info = sim.step(np.zeros(1), dt=0.01)
        assert "failed" in info

    def test_not_failed_near_upright(self, sim):
        _, info = sim.step(np.zeros(1), dt=0.01)
        assert info["failed"] is False

    def test_failed_when_angle_exceeds_threshold(self):
        sim = InvertedPendulumSim()
        sim.reset(x0=np.array([2.0, 0.0]))  # θ = 2.0 rad > π/2
        _, info = sim.step(np.zeros(1), dt=0.01)
        assert info["failed"] is True
