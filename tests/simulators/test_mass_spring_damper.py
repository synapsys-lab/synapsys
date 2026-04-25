"""Tests for MassSpringDamperSim.

Analytical state-space (exact — system is linear):
  A = [[0, 1], [-k/m, -c/m]]
  B = [[0], [1/m]]
  C = [[1, 0]]
  D = [[0]]

Analytical step response: q(t) for underdamped system (ζ < 1):
  ωₙ = sqrt(k/m),  ζ = c / (2*sqrt(m*k)),  ωd = ωₙ * sqrt(1 - ζ²)
  q(t) = (F/k) * [1 - exp(-ζωₙt) * (cos(ωd·t) + (ζ/sqrt(1-ζ²)) * sin(ωd·t))]
"""

from __future__ import annotations

import threading

import numpy as np
import pytest

from synapsys.simulators.mass_spring_damper import MassSpringDamperSim


@pytest.fixture()
def sim() -> MassSpringDamperSim:
    s = MassSpringDamperSim(m=1.0, c=0.5, k=2.0, integrator="rk4")
    s.reset()
    return s


def _analytical_matrices(m, c, k):
    A = np.array([[0.0, 1.0], [-k / m, -c / m]])
    B = np.array([[0.0], [1.0 / m]])
    C = np.array([[1.0, 0.0]])
    D = np.array([[0.0]])
    return A, B, C, D


def _step_response_analytical(t, m, c, k, F=1.0):
    """Analytical unit-step response for underdamped MSD."""
    wn = np.sqrt(k / m)
    zeta = c / (2.0 * np.sqrt(m * k))
    wd = wn * np.sqrt(1.0 - zeta**2)
    q_ss = F / k
    envelope = np.exp(-zeta * wn * t)
    oscillation = np.cos(wd * t) + (zeta / np.sqrt(1.0 - zeta**2)) * np.sin(wd * t)
    return q_ss * (1.0 - envelope * oscillation)


# ── Construction ──────────────────────────────────────────────────────────────


class TestConstruction:
    def test_default_params(self):
        s = MassSpringDamperSim()
        p = s.params
        assert p["m"] == pytest.approx(1.0)
        assert p["c"] == pytest.approx(0.5)
        assert p["k"] == pytest.approx(2.0)

    def test_custom_params(self):
        s = MassSpringDamperSim(m=2.0, c=1.0, k=4.0)
        assert s.params["m"] == pytest.approx(2.0)

    def test_dimensions(self, sim):
        assert sim.state_dim == 2
        assert sim.input_dim == 1
        assert sim.output_dim == 1

    def test_natural_frequency(self):
        s = MassSpringDamperSim(m=1.0, k=4.0, c=0.0)
        assert s.natural_frequency() == pytest.approx(2.0)

    def test_damping_ratio_underdamped(self):
        s = MassSpringDamperSim(m=1.0, c=0.5, k=2.0)
        assert s.damping_ratio() < 1.0

    def test_damping_ratio_critically_damped(self):
        m, k = 1.0, 4.0
        c_crit = 2.0 * np.sqrt(m * k)
        s = MassSpringDamperSim(m=m, c=c_crit, k=k)
        assert s.damping_ratio() == pytest.approx(1.0, rel=1e-9)


# ── reset ─────────────────────────────────────────────────────────────────────


class TestReset:
    def test_default_zero(self, sim):
        y = sim.reset()
        assert y[0] == pytest.approx(0.0)
        np.testing.assert_array_equal(sim.state, np.zeros(2))

    def test_custom_x0(self, sim):
        y = sim.reset(x0=np.array([1.0, 0.5]))
        assert y[0] == pytest.approx(1.0)

    def test_wrong_x0_length_raises(self, sim):
        with pytest.raises(ValueError, match="length 2"):
            sim.reset(x0=np.array([1.0]))


# ── output ────────────────────────────────────────────────────────────────────


class TestOutput:
    def test_returns_position_only(self, sim):
        x = np.array([3.0, -1.5])
        y = sim.output(x)
        assert y.shape == (1,)
        assert y[0] == pytest.approx(3.0)

    def test_velocity_not_in_output(self, sim):
        x = np.array([0.0, 5.0])
        y = sim.output(x)
        assert y[0] == pytest.approx(0.0)


# ── dynamics ──────────────────────────────────────────────────────────────────


class TestDynamics:
    def test_equilibrium_at_origin(self, sim):
        dx = sim.dynamics(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(dx, np.zeros(2), atol=1e-14)

    def test_spring_force_restores(self, sim):
        x = np.array([1.0, 0.0])  # displaced, no velocity
        u = np.zeros(1)
        dx = sim.dynamics(x, u)
        assert dx[0] == pytest.approx(0.0)  # ẋ₁ = q̇ = 0
        assert dx[1] < 0  # ẍ < 0 — spring pulls back

    def test_positive_force_accelerates(self, sim):
        dx = sim.dynamics(np.zeros(2), np.array([10.0]))
        assert dx[1] > 0

    def test_matches_analytical_equation(self):
        m, c, k = 2.0, 1.0, 3.0
        s = MassSpringDamperSim(m=m, c=c, k=k)
        x = np.array([0.5, -0.3])
        u = np.array([1.5])
        dx = s.dynamics(x, u)
        q, q_dot = x
        F = u[0]
        expected_q_ddot = (F - c * q_dot - k * q) / m
        assert dx[0] == pytest.approx(q_dot)
        assert dx[1] == pytest.approx(expected_q_ddot)


# ── step response ─────────────────────────────────────────────────────────────


class TestStepResponse:
    def test_step_response_matches_analytical(self):
        """RK4 step response must match analytical within 0.1% over 5 s."""
        m, c, k, F = 1.0, 0.5, 2.0, 1.0
        s = MassSpringDamperSim(m=m, c=c, k=k, integrator="rk4")
        s.reset()

        dt = 0.001
        t_end = 5.0
        steps = int(t_end / dt)

        ys = []
        for _ in range(steps):
            y, _ = s.step(np.array([F]), dt=dt)
            ys.append(y[0])

        t = np.linspace(dt, t_end, steps)
        q_analytical = _step_response_analytical(t, m, c, k, F)
        np.testing.assert_allclose(np.array(ys), q_analytical, rtol=1e-3)

    def test_settles_at_static_equilibrium(self):
        """q_ss = F / k for stable system."""
        m, c, k, F = 1.0, 2.0, 4.0, 1.0  # overdamped
        s = MassSpringDamperSim(m=m, c=c, k=k)
        s.reset()
        for _ in range(5000):
            y, _ = s.step(np.array([F]), dt=0.01)
        assert y[0] == pytest.approx(F / k, rel=1e-3)

    def test_free_vibration_decays(self, sim):
        """Positive peaks must decrease monotonically (energy dissipates)."""
        sim.reset(x0=np.array([1.0, 0.0]))
        peaks = []
        prev_y, going_up = 1.0, False
        for _ in range(3000):
            y, _ = sim.step(np.zeros(1), dt=0.01)
            cur = y[0]
            if going_up and cur < prev_y and prev_y > 0:
                peaks.append(prev_y)
            going_up = cur > prev_y
            prev_y = cur
        assert len(peaks) >= 2
        assert peaks[-1] < peaks[0]


# ── linearize ────────────────────────────────────────────────────────────────


class TestLinearize:
    def test_A_matches_analytical_at_origin(self, sim):
        A_an, _, _, _ = _analytical_matrices(1.0, 0.5, 2.0)
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.A, A_an, atol=1e-6)

    def test_B_matches_analytical_at_origin(self, sim):
        _, B_an, _, _ = _analytical_matrices(1.0, 0.5, 2.0)
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.B, B_an, atol=1e-6)

    def test_C_matches_analytical(self, sim):
        _, _, C_an, _ = _analytical_matrices(1.0, 0.5, 2.0)
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_allclose(ss.C, C_an, atol=1e-6)

    def test_linearize_invariant_under_operating_point(self, sim):
        """Linear system: Jacobian must be identical at any (x0, u0)."""
        ss_origin = sim.linearize(np.zeros(2), np.zeros(1))
        ss_displaced = sim.linearize(np.array([2.5, -1.0]), np.array([5.0]))
        np.testing.assert_allclose(ss_origin.A, ss_displaced.A, atol=1e-5)
        np.testing.assert_allclose(ss_origin.B, ss_displaced.B, atol=1e-5)

    def test_closed_loop_stable_with_pd(self, sim):
        """A - B @ K must be stable for any stabilising K."""
        ss = sim.linearize(np.zeros(2), np.zeros(1))
        K = np.array([[5.0, 2.0]])  # proportional + derivative
        A_cl = ss.A - ss.B @ K
        eigvals = np.linalg.eigvals(A_cl)
        assert np.all(np.real(eigvals) < 0)

    def test_does_not_mutate_state(self, sim):
        sim.reset(x0=np.array([1.0, 0.5]))
        before = sim.state.copy()
        sim.linearize(np.zeros(2), np.zeros(1))
        np.testing.assert_array_equal(sim.state, before)


# ── set_params ────────────────────────────────────────────────────────────────


class TestSetParams:
    def test_update_stiffness_changes_equilibrium(self):
        s = MassSpringDamperSim(m=1.0, c=2.0, k=1.0)
        s.reset()
        for _ in range(5000):
            s.step(np.array([1.0]), dt=0.01)
        q_k1 = s.state[0]

        s.reset()
        s.set_params(k=4.0)
        for _ in range(5000):
            s.step(np.array([1.0]), dt=0.01)
        q_k4 = s.state[0]

        assert q_k1 == pytest.approx(1.0, rel=1e-2)
        assert q_k4 == pytest.approx(0.25, rel=1e-2)

    def test_update_mass_stored(self, sim):
        sim.set_params(m=2.0)
        assert sim.params["m"] == pytest.approx(2.0)

    def test_update_damping_stored(self, sim):
        sim.set_params(c=1.0)
        assert sim.params["c"] == pytest.approx(1.0)

    def test_unknown_param_raises(self, sim):
        with pytest.raises(ValueError, match="Unknown parameters"):
            sim.set_params(friction=0.1)

    def test_thread_safe_update(self, sim):
        errors: list[Exception] = []

        def updater():
            try:
                for i in range(50):
                    sim.set_params(k=2.0 + i * 0.01)
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
