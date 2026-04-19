"""Tests for edge-cases in matlab_compat API layer."""
import pytest

from synapsys.api.matlab_compat import parallel, series, tf


class TestSeriesParallel:
    def test_series_no_args_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            series()

    def test_parallel_no_args_raises(self):
        with pytest.raises(ValueError, match="at least one"):
            parallel()


class TestTfFactory:
    def test_tf_none_num_raises(self):
        with pytest.raises(TypeError):
            tf(None, [1, 1])

    def test_tf_none_den_raises(self):
        with pytest.raises(TypeError):
            tf([1], None)


import numpy as np
import pytest as _pytest

from synapsys.api.matlab_compat import bode, c2d, feedback, lsim, parallel, series, ss, tf
from synapsys.core.state_space import StateSpace
from synapsys.core.transfer_function import TransferFunction


class TestTfFactoryEdgeCases:
    def test_scalar_num_triggers_except_branch(self):
        """tf(scalar, den) falls through except (TypeError) — covers line 38-39."""
        G = tf(3.0, [1, 1])
        assert isinstance(G, TransferFunction)
        # G(s) = 3 / (s+1): step DC gain = 3
        _, y = G.step()
        np.testing.assert_allclose(y[-1], 3.0, atol=1e-2)


class TestC2dEdgeCases:
    def test_non_ss_tf_type_raises(self):
        """Passing an unknown type raises TypeError — covers matlab_compat.py:86."""
        class FakeSys:
            is_discrete = False

        with _pytest.raises(TypeError, match="Expected StateSpace or TransferFunction"):
            c2d(FakeSys(), 0.1)


class TestLsim:
    def test_lsim_with_statespace(self):
        """lsim() with a StateSpace covers matlab_compat.py:105."""
        sys = ss([[-1]], [[1]], [[1]], [[0]])
        t = np.linspace(0, 5, 200)
        u = np.ones(200)
        t_out, y_out = lsim(sys, t, u)
        np.testing.assert_allclose(y_out[-1], 1.0, atol=1e-2)

    def test_lsim_with_tf(self):
        """lsim() with a TransferFunction."""
        G = tf([1], [1, 1])
        t = np.linspace(0, 5, 200)
        u = np.ones(200)
        _, y = lsim(G, t, u)
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-2)


class TestBode:
    def test_bode_with_statespace(self):
        """bode() with a StateSpace covers matlab_compat.py:113."""
        sys = ss([[-1]], [[1]], [[1]], [[0]])
        w, mag, phase = bode(sys)
        assert len(w) > 0

    def test_bode_with_tf(self):
        """bode() with a TransferFunction."""
        G = tf([1], [1, 1])
        w, mag, phase = bode(G)
        assert len(w) > 0


class TestFeedbackEdgeCases:
    def test_tf_plant_with_ss_sensor(self):
        """G is TF, H is SS → H.to_state_space() branch — covers line 129."""
        G = tf([1], [1, 1])
        H = ss([[0]], [[0]], [[0]], [[1]])  # static gain = 1
        T = feedback(G, H)
        assert isinstance(T, TransferFunction)

    def test_ss_plant_with_dynamic_tf_sensor(self):
        """G is SS, H is dynamic TF (n_states>0) → H.to_state_space() — covers line 152."""
        G = ss([[-1]], [[1]], [[1]], [[0]])
        H = tf([1, 1], [1, 2])  # dynamic sensor, n_states=1
        T = feedback(G, H)
        assert isinstance(T, StateSpace)


class TestSeriesParallelWithArgs:
    def test_series_two_tf(self):
        """series(G1, G2) computes product — covers matlab_compat.py:209-212."""
        G1 = tf([1], [1, 1])
        G2 = tf([1], [1, 2])
        result = series(G1, G2)
        assert isinstance(result, TransferFunction)
        # Poles at -1 and -2
        poles = np.sort(np.real(result.poles()))
        np.testing.assert_allclose(poles, [-2.0, -1.0], atol=1e-8)

    def test_parallel_two_tf(self):
        """parallel(G1, G2) computes sum — covers matlab_compat.py:221-224."""
        G1 = tf([1], [1, 1])
        G2 = tf([1], [1, 1])
        result = parallel(G1, G2)
        assert isinstance(result, TransferFunction)
        # Parallel of two identical first-order TFs doubles the numerator
        assert result.num[0] == _pytest.approx(2.0, rel=1e-6)

    def test_series_single_arg(self):
        """series(G) with one argument returns it unchanged."""
        G = tf([1], [1, 1])
        assert series(G) is G

    def test_parallel_single_arg(self):
        """parallel(G) with one argument returns it unchanged."""
        G = tf([1], [1, 1])
        assert parallel(G) is G
