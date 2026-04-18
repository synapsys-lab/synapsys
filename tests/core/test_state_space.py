import numpy as np
import pytest

from synapsys.core.state_space import StateSpace


class TestStateSpace:
    def _first_order(self) -> StateSpace:
        return StateSpace([[-1]], [[1]], [[1]], [[0]])

    def test_poles(self):
        A = np.diag([-1.0, -2.0])
        B = np.ones((2, 1))
        C = np.ones((1, 2))
        D = np.zeros((1, 1))
        sys = StateSpace(A, B, C, D)
        poles = np.sort(np.real(sys.poles()))
        np.testing.assert_allclose(poles, [-2.0, -1.0], atol=1e-10)

    def test_stable(self):
        assert self._first_order().is_stable()

    def test_unstable(self):
        assert not StateSpace([[1]], [[1]], [[1]], [[0]]).is_stable()

    def test_step_converges(self):
        # dx/dt = -x + u, y = x  =>  DC gain = 1
        sys = self._first_order()
        t, y = sys.step()
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-3)

    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError):
            # C has wrong number of columns
            StateSpace([[-1, 0], [0, -2]], [[1], [1]], [[1]], [[0]])

    def test_mul_series_incompatible_inner_dim_raises(self):
        # G1: 2-in 1-out; G2: 1-in 2-out → series G1*G2 ok
        # G1: 1-in 1-out; G2: 2-in 1-out → series G1*G2 fails (G1.n_inputs=1 != G2.n_outputs=1... wait)
        # Need: self.n_inputs != other.n_outputs to fail
        # G1 has n_inputs=1, G2 has n_outputs=2 → incompatible
        G1 = StateSpace([[-1]], [[1]], [[1]], [[0]])           # 1-in 1-out
        G2 = StateSpace(np.diag([-1.0, -2.0]),
                        np.ones((2, 2)), np.eye(2), np.zeros((2, 2)))  # 2-in 2-out
        # G1 * G2: G1.n_inputs=1 != G2.n_outputs=2
        with pytest.raises(ValueError, match="inner"):
            G1 * G2

    def test_to_transfer_function(self):
        sys = self._first_order()
        tf = sys.to_transfer_function()
        # G(s) = 1/(s+1): step should reach 1.0
        _, y = tf.step()
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-3)

    def test_to_transfer_function_raises_for_mimo(self):
        sys = StateSpace(
            np.diag([-1.0, -2.0]), np.eye(2), np.eye(2), np.zeros((2, 2))
        )
        with pytest.raises(ValueError, match="MIMO"):
            sys.to_transfer_function()

    # ------------------------------------------------------------------
    # zeros() — Rosenbrock system matrix (SISO + MIMO)
    # ------------------------------------------------------------------

    def test_zeros_siso_no_zeros(self):
        # G(s) = 1/(s+1): no finite zeros
        z = self._first_order().zeros()
        assert len(z) == 0

    def test_zeros_siso_with_zero(self):
        # G(s) = (s+2)/(s+1)^2 — zero at -2
        from synapsys.core.transfer_function import TransferFunction
        sys = TransferFunction([1, 2], [1, 2, 1]).to_state_space()
        z = sys.zeros()
        np.testing.assert_allclose(np.sort(np.real(z)), [-2.0], atol=1e-6)

    def test_zeros_mimo_no_transmission_zeros(self):
        # G = diag(1/(s+1), 1/(s+2)): no transmission zeros
        sys = StateSpace(
            np.diag([-1.0, -2.0]), np.eye(2), np.eye(2), np.zeros((2, 2))
        )
        z = sys.zeros()
        assert len(z) == 0

    def test_zeros_non_square_raises_descriptive(self):
        # 2-in 3-out: must raise with n_inputs/n_outputs context, not a raw scipy error
        sys = StateSpace(
            np.diag([-1.0, -2.0]),
            np.ones((2, 2)),
            np.ones((3, 2)),
            np.zeros((3, 2)),
        )
        with pytest.raises(ValueError, match="n_inputs"):
            sys.zeros()

    def test_zeros_mimo_with_transmission_zero(self):
        # G = diag((s+3)/(s+1), 1/(s+2)): transmission zero at -3
        # State-space realisation: A=diag(-1,-2), B=I, C=diag(2,1), D=diag(1,0)
        sys = StateSpace(
            np.diag([-1.0, -2.0]),
            np.eye(2),
            np.array([[2.0, 0.0], [0.0, 1.0]]),
            np.array([[1.0, 0.0], [0.0, 0.0]]),
        )
        z = sys.zeros()
        np.testing.assert_allclose(np.sort(np.real(z)), [-3.0], atol=1e-6)
