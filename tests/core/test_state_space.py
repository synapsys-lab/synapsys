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

    def test_to_transfer_function(self):
        sys = self._first_order()
        tf = sys.to_transfer_function()
        # G(s) = 1/(s+1): step should reach 1.0
        _, y = tf.step()
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-3)
