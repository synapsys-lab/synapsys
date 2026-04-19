import numpy as np
import pytest

from synapsys.core.transfer_function import TransferFunction


class TestTransferFunction:
    def test_poles_second_order(self):
        # G(s) = 1 / (s+1)(s+2) => poles at -1, -2
        G = TransferFunction([1], [1, 3, 2])
        poles = np.sort(np.real(G.poles()))
        np.testing.assert_allclose(poles, [-2.0, -1.0], atol=1e-10)

    def test_stable(self):
        assert TransferFunction([1], [1, 3, 2]).is_stable()

    def test_unstable(self):
        assert not TransferFunction([1], [1, -1]).is_stable()

    def test_series_mul(self):
        G1 = TransferFunction([1], [1, 1])
        G2 = TransferFunction([1], [1, 2])
        G = G1 * G2
        np.testing.assert_allclose(G.den, [1, 3, 2], atol=1e-10)

    def test_parallel_add(self):
        G1 = TransferFunction([1], [1, 1])
        G2 = TransferFunction([1], [1, 1])
        G = G1 + G2
        # 2*(s+1) / (s+1)^2 — numerator leading coeff should double
        assert G.num[0] == pytest.approx(2.0, rel=1e-6)

    def test_feedback(self):
        # Unity negative feedback: T = G/(1+G)
        G = TransferFunction([10], [1, 1])
        T = G.feedback()
        # DC gain = 10/11
        w, y = T.step()
        np.testing.assert_allclose(y[-1], 10 / 11, atol=1e-3)

    def test_step_converges_to_dcgain(self):
        G = TransferFunction([1], [1, 1])
        t, y = G.step()
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-3)

    def test_empty_den_raises(self):
        with pytest.raises(ValueError):
            TransferFunction([1], [])

    def test_zero_leading_den_raises(self):
        with pytest.raises(ValueError):
            TransferFunction([1], [0, 1])

    def test_evaluate_at_zero(self):
        G = TransferFunction([2], [1, 2])  # DC gain = 1.0
        assert G.evaluate(0) == pytest.approx(1.0)

    def test_evolve_discrete(self):
        """TransferFunction.evolve() delegates to StateSpace and advances one step."""
        from synapsys.api import c2d
        # G(s) = 1/(s+1) discretised with ZOH at dt=0.1
        Gd = c2d(TransferFunction([1], [1, 1]), dt=0.1)
        x = np.zeros(Gd.n_states)
        # Apply unit step for several ticks — output should rise toward 1
        y_vals = []
        for _ in range(60):   # 6 s >> τ=1 s, so output ≈ 1 − e⁻⁶ ≈ 0.9975
            x, y = Gd.evolve(x, np.array([1.0]))
            y_vals.append(float(y[0]))
        # Discrete first-order step response converges to DC gain = 1
        assert y_vals[-1] == pytest.approx(1.0, abs=0.02)

    def test_evolve_continuous_raises(self):
        """evolve() on a continuous TF must raise RuntimeError."""
        G = TransferFunction([1], [1, 1])
        with pytest.raises(RuntimeError):
            G.evolve(np.zeros(1), np.array([1.0]))


class TestTransferFunctionEdgeCases:
    def test_negative_dt_raises(self):
        """Negative dt raises ValueError — covers transfer_function.py:34."""
        with pytest.raises(ValueError, match="dt must be"):
            TransferFunction([1], [1, 1], dt=-0.1)

    def test_zeros_constant_numerator_returns_empty(self):
        """zeros() with constant numerator returns empty — covers transfer_function.py:76."""
        G = TransferFunction([3], [1, 1])
        z = G.zeros()
        assert len(z) == 0

    def test_to_transfer_function_returns_self(self):
        """to_transfer_function() returns self — covers transfer_function.py:93."""
        G = TransferFunction([1], [1, 1])
        assert G.to_transfer_function() is G

    def test_simulate(self):
        """simulate() routes through StateSpace — covers transfer_function.py:150."""
        G = TransferFunction([1], [1, 1])
        t = np.linspace(0, 5, 200)
        u = np.ones(200)
        t_out, y = G.simulate(t, u)
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-2)

    def test_bode_continuous(self):
        """bode() on continuous TF — covers transfer_function.py:156-162."""
        G = TransferFunction([1], [1, 1])
        w, mag, phase = G.bode()
        assert len(w) > 0

    def test_bode_discrete(self):
        """bode() on discrete TF — covers the discrete branch of bode()."""
        from synapsys.api.matlab_compat import c2d
        Gd = c2d(TransferFunction([1], [1, 1]), dt=0.1)
        w, mag, phase = Gd.bode()
        assert len(w) > 0

    def test_add_with_non_tf_other(self):
        """__add__ with non-TF calls other.to_transfer_function() — covers line 178."""
        from synapsys.core.state_space import StateSpace
        G_tf = TransferFunction([1], [1, 1])
        G_ss = StateSpace([[-2]], [[1]], [[1]], [[0]])
        result = G_tf + G_ss
        assert isinstance(result, TransferFunction)

    def test_mul_with_non_tf_other(self):
        """__mul__ with non-TF calls other.to_transfer_function() — covers line 190."""
        from synapsys.core.state_space import StateSpace
        G_tf = TransferFunction([1], [1, 1])
        G_ss = StateSpace([[-2]], [[1]], [[1]], [[0]])
        result = G_tf * G_ss
        assert isinstance(result, TransferFunction)

    def test_truediv(self):
        """__truediv__ (G1 / G2) — covers transfer_function.py:199-202."""
        G1 = TransferFunction([2], [1, 1])
        G2 = TransferFunction([1], [1, 2])
        result = G1 / G2
        assert isinstance(result, TransferFunction)

    def test_repr(self):
        """__repr__ returns descriptive string — covers transfer_function.py:225-226."""
        G = TransferFunction([1], [1, 1])
        r = repr(G)
        assert "TransferFunction" in r
        assert "continuous" in r

    def test_repr_discrete(self):
        """__repr__ for discrete TF includes dt."""
        Gd = TransferFunction([1], [1, 1], dt=0.1)
        r = repr(Gd)
        assert "dt=0.1" in r

    def test_truediv_with_non_tf_other(self):
        """__truediv__ with non-TF calls other.to_transfer_function() — covers line 200."""
        from synapsys.core.state_space import StateSpace
        G_tf = TransferFunction([1], [1, 1])
        G_ss = StateSpace([[-2]], [[1]], [[1]], [[0]])
        result = G_tf / G_ss
        assert isinstance(result, TransferFunction)
