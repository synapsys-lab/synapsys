import numpy as np
import pytest

from synapsys.api.matlab_compat import c2d, ss, tf


class TestDiscreteTransferFunction:
    def test_c2d_zoh_poles_inside_unit_circle(self):
        G = tf([1], [1, 1])        # G(s) = 1/(s+1), pole at -1
        Gd = c2d(G, dt=0.1)
        assert Gd.is_discrete
        assert Gd.dt == pytest.approx(0.1)
        # Discrete pole = exp(-1 * 0.1) ≈ 0.905
        poles = np.abs(Gd.poles())
        assert all(p < 1.0 for p in poles)

    def test_discrete_stable(self):
        G = tf([1], [1, 1])
        Gd = c2d(G, dt=0.1)
        assert Gd.is_stable()

    def test_discrete_unstable(self):
        # Pole outside unit circle
        Gd = tf([1], [1, -1.5], dt=0.1)
        assert not Gd.is_stable()

    def test_discrete_step_steady_state(self):
        # G(s) = 1/(s+1) → steady-state step = 1.0
        G = tf([1], [1, 1])
        Gd = c2d(G, dt=0.05)
        t, y = Gd.step(n=300)
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-3)

    def test_discrete_feedback(self):
        G = tf([10], [1, 1])
        Gd = c2d(G, dt=0.01)
        Td = Gd.feedback()
        assert Td.is_stable()
        _, y = Td.step(n=500)
        np.testing.assert_allclose(y[-1], 10 / 11, atol=1e-3)

    def test_mixing_sample_times_raises(self):
        G1 = tf([1], [1, 1], dt=0.1)
        G2 = tf([1], [1, 2], dt=0.05)
        with pytest.raises(ValueError, match="sample times"):
            _ = G1 * G2

    def test_continuous_mixing_with_discrete_raises(self):
        Gc = tf([1], [1, 1])         # continuous
        Gd = tf([1], [1, 1], dt=0.1) # discrete
        with pytest.raises(ValueError):
            _ = Gc + Gd


class TestDiscreteStateSpace:
    def test_c2d_state_space_stable(self):
        plant = ss([[-2]], [[1]], [[1]], [[0]])
        plant_d = c2d(plant, dt=0.05)
        assert plant_d.is_discrete
        assert plant_d.is_stable()

    def test_evolve_single_step(self):
        # x(k+1) = 0.9*x(k) + 0.1*u(k), y = x
        plant_d = ss([[0.9]], [[0.1]], [[1]], [[0]], dt=0.1)
        x0 = np.array([0.0])
        x1, y1 = plant_d.evolve(x0, np.array([10.0]))
        np.testing.assert_allclose(x1, [0.9 * 0.0 + 0.1 * 10.0])
        np.testing.assert_allclose(y1, [0.0])  # y uses x(k) not x(k+1)

    def test_evolve_requires_discrete(self):
        plant_c = ss([[-1]], [[1]], [[1]], [[0]])
        with pytest.raises(RuntimeError, match="discrete"):
            plant_c.evolve(np.array([0.0]), np.array([1.0]))

    def test_discrete_bode_returns_arrays(self):
        plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.05)
        w, mag, phase = plant_d.bode()
        assert w.shape == mag.shape == phase.shape
        assert len(w) > 0

    def test_c2d_raises_if_already_discrete(self):
        plant_d = ss([[0.9]], [[0.1]], [[1]], [[0]], dt=0.1)
        with pytest.raises(ValueError, match="already discrete"):
            c2d(plant_d, dt=0.05)
