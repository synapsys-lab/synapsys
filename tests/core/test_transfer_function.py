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
