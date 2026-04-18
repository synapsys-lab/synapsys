import numpy as np
import pytest

from synapsys.api.matlab_compat import feedback
from synapsys.core.state_space import StateSpace
from synapsys.core.transfer_function import TransferFunction


class TestFeedback:
    # ------------------------------------------------------------------
    # Regression: existing TransferFunction SISO behaviour must be intact
    # ------------------------------------------------------------------

    def test_tf_siso_unity_feedback_dc_gain(self):
        # G = 10/(s+1), T = 10/(s+11): DC gain = 10/11
        G = TransferFunction([10], [1, 1])
        T = feedback(G)
        assert isinstance(T, TransferFunction)
        _, y = T.step()
        np.testing.assert_allclose(y[-1], 10 / 11, atol=1e-3)

    def test_tf_siso_sensor_feedback(self):
        # G = 1/(s+1), H = 2: T = G/(1+2G) = 1/(s+3): DC gain = 1/3
        G = TransferFunction([1], [1, 1])
        H = TransferFunction([2], [1])
        T = feedback(G, H)
        assert isinstance(T, TransferFunction)
        _, y = T.step()
        np.testing.assert_allclose(y[-1], 1 / 3, atol=1e-3)

    # ------------------------------------------------------------------
    # StateSpace SISO unity feedback
    # ------------------------------------------------------------------

    def test_ss_siso_unity_feedback_returns_statespace(self):
        # G(s) = 1/(s+1): T(s) = 1/(s+2)
        G = StateSpace([[-1]], [[1]], [[1]], [[0]])
        T = feedback(G)
        assert isinstance(T, StateSpace)

    def test_ss_siso_unity_feedback_pole(self):
        G = StateSpace([[-1]], [[1]], [[1]], [[0]])
        T = feedback(G)
        np.testing.assert_allclose(
            np.sort(np.real(T.poles())), [-2.0], atol=1e-8
        )

    def test_ss_siso_unity_feedback_dc_gain(self):
        # T = 1/(s+2): DC gain = 0.5
        G = StateSpace([[-1]], [[1]], [[1]], [[0]])
        T = feedback(G)
        _, y = T.step()
        np.testing.assert_allclose(y[-1], 0.5, atol=1e-3)

    # ------------------------------------------------------------------
    # StateSpace MIMO unity feedback
    # ------------------------------------------------------------------

    def test_ss_mimo_unity_feedback_dimensions(self):
        # G = diag(1/(s+1), 1/(s+2)): 2-in 2-out
        G = StateSpace(
            np.diag([-1.0, -2.0]), np.eye(2), np.eye(2), np.zeros((2, 2))
        )
        T = feedback(G)
        assert isinstance(T, StateSpace)
        assert T.n_inputs == 2
        assert T.n_outputs == 2

    def test_ss_mimo_unity_feedback_poles(self):
        # T = diag(1/(s+2), 1/(s+3)): poles at -2 and -3
        G = StateSpace(
            np.diag([-1.0, -2.0]), np.eye(2), np.eye(2), np.zeros((2, 2))
        )
        T = feedback(G)
        poles = np.sort(np.real(T.poles()))
        np.testing.assert_allclose(poles, [-3.0, -2.0], atol=1e-8)

    def test_ss_mimo_unity_feedback_nonsquare_raises(self):
        # 1-input 2-output: not square, unity feedback undefined
        G = StateSpace(
            np.diag([-1.0, -2.0]),
            np.ones((2, 1)),
            np.eye(2),
            np.zeros((2, 1)),
        )
        with pytest.raises(ValueError, match="square"):
            feedback(G)

    # ------------------------------------------------------------------
    # StateSpace MIMO with TransferFunction sensor H
    # ------------------------------------------------------------------

    def test_ss_siso_with_tf_sensor(self):
        # G = 1/(s+1), H = 2: T = G/(1+2G) = 1/(s+3): DC gain = 1/3
        G = StateSpace([[-1]], [[1]], [[1]], [[0]])
        H = TransferFunction([2], [1])
        T = feedback(G, H)
        assert isinstance(T, StateSpace)
        _, y = T.step()
        np.testing.assert_allclose(y[-1], 1 / 3, atol=1e-3)

    def test_ss_siso_with_static_tf_sensor_no_phantom_state(self):
        # Static H (n_states=0) must NOT add a phantom state via scipy quirk
        G = StateSpace([[-1.]], [[1.]], [[1.]], [[0.]])
        H = TransferFunction([2.], [1.])   # static gain 2
        T = feedback(G, H)
        assert T.n_states == 1             # only plant's state
        np.testing.assert_allclose(np.sort(np.real(T.poles())), [-3.0], atol=1e-8)

    def test_feedback_dt_mismatch_raises(self):
        G = StateSpace([[-1.]], [[1.]], [[1.]], [[0.]])
        H = StateSpace([[-2.]], [[1.]], [[1.]], [[0.]], dt=0.1)
        with pytest.raises(ValueError, match="dt"):
            feedback(G, H)

    def test_feedback_transfer_function_matrix_auto_converts(self):
        from synapsys.core.transfer_function_matrix import TransferFunctionMatrix
        G = TransferFunctionMatrix([
            [TransferFunction([1], [1, 1]), TransferFunction([0], [1])],
            [TransferFunction([0], [1]),    TransferFunction([1], [1, 2])],
        ])
        T = feedback(G)
        assert isinstance(T, StateSpace)
        assert T.n_inputs == 2
        assert T.n_outputs == 2
