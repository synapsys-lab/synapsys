"""Tests for tf() factory — SISO vs MIMO dispatch."""

from synapsys.api.matlab_compat import tf
from synapsys.core.transfer_function import TransferFunction
from synapsys.core.transfer_function_matrix import TransferFunctionMatrix


class TestTfFactory:
    def test_1d_num_returns_transfer_function(self):
        G = tf([1], [1, 1])
        assert isinstance(G, TransferFunction)

    def test_2d_num_returns_transfer_function_matrix(self):
        G = tf([[1, 2], [3, 4]], [1, 3, 2])
        assert isinstance(G, TransferFunctionMatrix)

    def test_2d_num_correct_dimensions(self):
        G = tf([[1, 2], [3, 4]], [1, 3, 2])
        assert G.n_outputs == 2
        assert G.n_inputs == 2

    def test_2d_num_per_element_den(self):
        G = tf(
            [[[1], [2]], [[3], [4]]],
            [[[1, 1], [1, 2]], [[1, 3], [1, 4]]],
        )
        assert isinstance(G, TransferFunctionMatrix)
        assert G.n_states == 4

    def test_1x1_matrix_via_factory(self):
        G = tf([[1]], [1, 1])
        assert isinstance(G, TransferFunctionMatrix)
        assert G.n_outputs == 1
        assert G.n_inputs == 1

    def test_dt_propagated_to_matrix(self):
        G = tf([[1, 2], [3, 4]], [1, 3, 2], dt=0.1)
        assert G.dt == 0.1
        assert G.is_discrete
