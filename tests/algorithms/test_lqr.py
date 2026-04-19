"""Tests for the continuous-time LQR solver."""

from __future__ import annotations

import numpy as np
import pytest

from synapsys.algorithms.lqr import lqr


class TestLQR:
    # ── simple 1st-order system: A=-1, B=1, Q=1, R=1 ──────────────────────────
    def test_scalar_system_returns_positive_gain(self):
        A = np.array([[-1.0]])
        B = np.array([[1.0]])
        Q = np.array([[1.0]])
        R = np.array([[1.0]])
        K, P = lqr(A, B, Q, R)
        assert K.shape == (1, 1)
        assert P.shape == (1, 1)
        assert K[0, 0] > 0.0

    def test_scalar_system_closed_loop_stable(self):
        """A - B @ K must have all eigenvalues with negative real part."""
        A = np.array([[-1.0]])
        B = np.array([[1.0]])
        K, _ = lqr(A, B, np.eye(1), np.eye(1))
        A_cl = A - B @ K
        assert np.all(np.real(np.linalg.eigvals(A_cl)) < 0)

    def test_double_integrator(self):
        """Classic double integrator: A=[[0,1],[0,0]], B=[[0],[1]]."""
        A = np.array([[0.0, 1.0], [0.0, 0.0]])
        B = np.array([[0.0], [1.0]])
        Q = np.eye(2)
        R = np.eye(1)
        K, P = lqr(A, B, Q, R)
        assert K.shape == (1, 2)
        assert P.shape == (2, 2)
        # Closed-loop must be stable
        A_cl = A - B @ K
        assert np.all(np.real(np.linalg.eigvals(A_cl)) < 0)

    def test_riccati_solution_symmetric(self):
        """P must be symmetric positive definite."""
        A = np.array([[-2.0, 1.0], [0.0, -3.0]])
        B = np.array([[1.0], [1.0]])
        _, P = lqr(A, B, np.eye(2), np.eye(1))
        assert P == pytest.approx(P.T, abs=1e-10)
        # All eigenvalues of P positive
        assert np.all(np.linalg.eigvalsh(P) > 0)

    def test_gain_formula_K_equals_Rinv_Bt_P(self):
        """K must equal R⁻¹ B' P."""
        A = np.array([[-1.0, 0.5], [-0.5, -2.0]])
        B = np.array([[1.0, 0.0], [0.0, 1.0]])
        Q = np.diag([2.0, 1.0])
        R = np.diag([1.0, 0.5])
        K, P = lqr(A, B, Q, R)
        K_expected = np.linalg.solve(R, B.T @ P)
        assert K == pytest.approx(K_expected, abs=1e-10)

    def test_higher_R_reduces_control_effort(self):
        """Increasing R penalises control effort → smaller gain magnitude."""
        A = np.array([[-1.0]])
        B = np.array([[1.0]])
        Q = np.eye(1)
        K_low,  _ = lqr(A, B, Q, np.array([[1.0]]))
        K_high, _ = lqr(A, B, Q, np.array([[100.0]]))
        assert np.abs(K_low[0, 0]) > np.abs(K_high[0, 0])

    def test_list_inputs_accepted(self):
        """lqr should accept plain Python lists (not just numpy arrays)."""
        K, P = lqr([[-1.0]], [[1.0]], [[1.0]], [[1.0]])
        assert K.shape == (1, 1)

    def test_singular_R_raises(self):
        """R must be positive definite — singular R must raise ValueError."""
        A = np.array([[-1.0]])
        B = np.array([[1.0]])
        Q = np.eye(1)
        R_singular = np.array([[0.0]])  # singular (zero determinant)
        with pytest.raises(ValueError, match="positive definite"):
            lqr(A, B, Q, R_singular)

    def test_negative_R_raises(self):
        """Negative-definite R must raise ValueError."""
        A = np.array([[-1.0]])
        B = np.array([[1.0]])
        Q = np.eye(1)
        R_neg = np.array([[-1.0]])
        with pytest.raises(ValueError, match="positive definite"):
            lqr(A, B, Q, R_neg)

    def test_indefinite_Q_raises(self):
        """Indefinite Q (negative eigenvalue) must raise ValueError."""
        A = np.array([[-1.0]])
        B = np.array([[1.0]])
        Q = np.array([[-1.0]])  # negative definite
        R = np.array([[1.0]])
        with pytest.raises(ValueError, match="positive semi-definite"):
            lqr(A, B, Q, R)

    def test_positive_semidefinite_Q_accepted(self):
        """Q=0 (zero matrix) is positive semi-definite and must be accepted."""
        A = np.array([[-1.0]])
        B = np.array([[1.0]])
        Q = np.array([[0.0]])
        R = np.array([[1.0]])
        K, P = lqr(A, B, Q, R)
        assert K.shape == (1, 1)

    def test_unstabilizable_system_raises(self):
        """Unstabilizable (A,B) → ARE has no solution — covers lqr.py:52-53."""
        # A has unstable eigenvalue at +1, B=0 → uncontrollable unstable mode
        A = np.array([[1.0]])
        B = np.array([[0.0]])
        Q = np.array([[1.0]])
        R = np.array([[1.0]])
        with pytest.raises(ValueError, match="Riccati"):
            lqr(A, B, Q, R)
