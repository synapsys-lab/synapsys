"""Tests for numerical integrators (euler, rk4, rk45)."""

from __future__ import annotations

import numpy as np
import pytest

from synapsys.simulators.integrators import euler, rk4, rk45

# ── fixture: linear ẋ = u (exact: x(t) = x0 + u*t) ──────────────────────────


def _linear(x, u):
    return u.copy()


# ── fixture: exponential decay ẋ = -x (exact: x(t) = x0 * exp(-t)) ──────────


def _decay(x, u):
    return -x


class TestEuler:
    def test_linear_dynamics_one_step(self):
        x = np.array([0.0])
        u = np.array([2.0])
        x1 = euler(_linear, x, u, dt=0.5)
        assert x1[0] == pytest.approx(1.0)

    def test_constant_input_accumulates(self):
        x = np.array([0.0])
        u = np.array([1.0])
        for _ in range(10):
            x = euler(_linear, x, u, dt=0.1)
        assert x[0] == pytest.approx(1.0, rel=1e-9)

    def test_does_not_mutate_input(self):
        x = np.array([1.0, 2.0])
        u = np.array([0.0, 0.0])
        x_orig = x.copy()
        euler(_decay, x, u, dt=0.1)
        np.testing.assert_array_equal(x, x_orig)


class TestRK4:
    def test_double_integrator_position(self):
        """x=[pos,vel], u=[accel]=1 → after 1 s: pos=0.5, vel=1."""

        def dbl(x, u):
            return np.array([x[1], u[0]])

        x = np.array([0.0, 0.0])
        u = np.array([1.0])
        for _ in range(100):
            x = rk4(dbl, x, u, dt=0.01)
        assert x[0] == pytest.approx(0.5, rel=1e-6)
        assert x[1] == pytest.approx(1.0, rel=1e-6)

    def test_exponential_decay_accuracy(self):
        """RK4 error for ẋ=-x over 1 s must be < 1e-7."""
        x = np.array([1.0])
        u = np.zeros(0)
        for _ in range(100):
            x = rk4(_decay, x, u, dt=0.01)
        exact = np.exp(-1.0)
        assert abs(x[0] - exact) < 1e-7

    def test_more_accurate_than_euler(self):
        """RK4 must have smaller error than Euler for the same dt."""
        x0 = np.array([1.0])
        u = np.zeros(0)
        dt, steps = 0.1, 10
        x_euler = x0.copy()
        x_rk4 = x0.copy()
        for _ in range(steps):
            x_euler = euler(_decay, x_euler, u, dt)
            x_rk4 = rk4(_decay, x_rk4, u, dt)
        exact = np.exp(-1.0)
        assert abs(x_rk4[0] - exact) < abs(x_euler[0] - exact)

    def test_does_not_mutate_input(self):
        x = np.array([1.0, 0.0])
        u = np.array([1.0])
        x_orig = x.copy()

        def dbl(x, u):
            return np.array([x[1], u[0]])

        rk4(dbl, x, u, dt=0.1)
        np.testing.assert_array_equal(x, x_orig)


class TestRK45:
    def test_exponential_decay_accuracy(self):
        """RK45 error for ẋ=-x over 1 s must be < 1e-9."""
        x = np.array([1.0])
        u = np.zeros(0)
        for _ in range(100):
            x = rk45(_decay, x, u, dt=0.01)
        assert abs(x[0] - np.exp(-1.0)) < 1e-9

    def test_consistent_with_rk4_on_linear(self):
        """For linear dynamics both methods must agree to < 1e-8."""

        def dbl(x, u):
            return np.array([x[1], u[0]])

        x0 = np.array([0.0, 0.0])
        u = np.array([1.0])
        x_rk4 = x0.copy()
        x_rk45 = x0.copy()
        for _ in range(100):
            x_rk4 = rk4(dbl, x_rk4, u, dt=0.01)
            x_rk45 = rk45(dbl, x_rk45, u, dt=0.01)
        np.testing.assert_allclose(x_rk4, x_rk45, atol=1e-8)
