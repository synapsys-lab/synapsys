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
        # G1 has n_inputs=1, G2 has n_outputs=2 → incompatible inner dims
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


class TestStateSpaceValidation:
    def test_non_square_A_raises(self):
        """A must be square — covers state_space.py:38."""
        with pytest.raises(ValueError, match="square"):
            StateSpace([[1, 2]], [[1]], [[1]], [[0]])

    def test_B_row_mismatch_raises(self):
        """B rows must match A order — covers state_space.py:40."""
        with pytest.raises(ValueError, match="B rows"):
            StateSpace([[-1, 0], [0, -2]], [[1], [1], [1]], [[1, 0]], [[0]])

    def test_C_col_mismatch_raises(self):
        """C cols must match A order — covers state_space.py:49."""
        with pytest.raises(ValueError, match="C cols"):
            StateSpace([[-1]], [[1]], [[1, 0]], [[0, 0]])

    def test_D_shape_mismatch_raises(self):
        """D must be (p×m) — covers state_space.py:51."""
        with pytest.raises(ValueError, match=r"D must be"):
            StateSpace([[-1]], [[1]], [[1]], [[0, 0]])


class TestStateSpaceZerosEdge:
    def test_zeros_zero_state_system_returns_empty(self):
        """zeros() on a 0-state system returns empty array — covers state_space.py:120."""
        # Pure feedthrough: D-term only, no states
        sys = StateSpace(
            np.zeros((0, 0)),
            np.zeros((0, 1)),
            np.zeros((1, 0)),
            np.array([[1.0]]),
        )
        z = sys.zeros()
        assert len(z) == 0


class TestStateSpaceConversions:
    def test_to_state_space_returns_self(self):
        """to_state_space() returns the same object — covers state_space.py:142."""
        sys = StateSpace([[-1]], [[1]], [[1]], [[0]])
        assert sys.to_state_space() is sys


class TestStateSpaceDiscreteSimulation:
    def _discrete_plant(self):
        return StateSpace([[0.9]], [[0.1]], [[1]], [[0]], dt=0.1)

    def test_simulate_discrete(self):
        """StateSpace.simulate() on discrete system — covers state_space.py:173-174."""
        plant_d = self._discrete_plant()
        t = np.arange(0, 10, 0.1)
        u = np.ones(len(t))
        t_out, y = plant_d.simulate(t, u)
        assert len(t_out) == len(t)
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-2)

    def test_step_discrete(self):
        """StateSpace.step() on discrete system — covers state_space.py:187-189."""
        plant_d = self._discrete_plant()
        t, y = plant_d.step(n=100)
        assert len(t) == 100
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-2)


class TestStateSpaceEvolveValidation:
    def test_evolve_wrong_x_size_raises(self):
        """evolve() with wrong x size raises ValueError — covers state_space.py:222."""
        plant_d = StateSpace([[0.9]], [[0.1]], [[1]], [[0]], dt=0.1)
        with pytest.raises(ValueError, match="n_states"):
            plant_d.evolve(np.zeros(2), np.array([1.0]))

    def test_evolve_wrong_u_size_raises(self):
        """evolve() with wrong u size raises ValueError — covers state_space.py:227."""
        plant_d = StateSpace([[0.9]], [[0.1]], [[1]], [[0]], dt=0.1)
        with pytest.raises(ValueError, match="n_inputs"):
            plant_d.evolve(np.zeros(1), np.array([1.0, 2.0]))


class TestStateSpaceAlgebra:
    def _g1(self):
        return StateSpace([[-1]], [[1]], [[1]], [[0]])

    def test_check_compatible_different_dt_raises(self):
        """_check_compatible raises on dt mismatch — covers state_space.py:241."""
        sys_c = StateSpace([[-1]], [[1]], [[1]], [[0]])
        sys_d = StateSpace([[0.9]], [[0.1]], [[1]], [[0]], dt=0.1)
        with pytest.raises(ValueError, match="sample times"):
            sys_c + sys_d

    def test_add_parallel(self):
        """__add__ parallel connection — covers state_space.py:248-255."""
        G1 = self._g1()
        G2 = StateSpace([[-2]], [[1]], [[1]], [[0]])
        result = G1 + G2
        assert isinstance(result, StateSpace)
        assert result.n_states == 2
        _, y = result.step()
        # DC gains: 1/(1) + 1/(2) = 1.5
        np.testing.assert_allclose(y[-1], 1.5, atol=1e-2)

    def test_mul_series_non_ss_other(self):
        """__mul__ with non-SS other calls other.to_state_space() — covers state_space.py:260."""
        from synapsys.core.transfer_function import TransferFunction
        G_ss = self._g1()
        G_tf = TransferFunction([1], [1, 2])
        result = G_ss * G_tf  # G_tf.to_state_space() called internally
        assert isinstance(result, StateSpace)

    def test_mul_series(self):
        """__mul__ series connection — covers state_space.py:268-275."""
        G1 = self._g1()
        G2 = StateSpace([[-2]], [[1]], [[1]], [[0]])
        result = G1 * G2
        assert isinstance(result, StateSpace)
        assert result.n_states == 2
        _, y = result.step()
        # Series of 1/(s+1) and 1/(s+2): DC gain = 1/2
        np.testing.assert_allclose(y[-1], 0.5, atol=1e-2)

    def test_neg(self):
        """__neg__ negates outputs — covers state_space.py:278."""
        G = self._g1()
        neg = -G
        assert isinstance(neg, StateSpace)
        _, y = neg.step()
        np.testing.assert_allclose(y[-1], -1.0, atol=1e-2)

    def test_repr(self):
        """__repr__ returns descriptive string — covers state_space.py:281-282."""
        r = repr(self._g1())
        assert "StateSpace" in r
        assert "n_states=1" in r
        assert "continuous" in r

    def test_repr_discrete(self):
        """__repr__ for discrete system includes dt."""
        sys_d = StateSpace([[0.9]], [[0.1]], [[1]], [[0]], dt=0.1)
        r = repr(sys_d)
        assert "dt=0.1" in r

    def test_negative_dt_raises(self):
        """Negative dt raises ValueError — covers state_space.py:51."""
        with pytest.raises(ValueError, match="dt must be"):
            StateSpace([[-1]], [[1]], [[1]], [[0]], dt=-0.1)

    def test_add_with_non_ss_other(self):
        """__add__ with non-SS calls other.to_state_space() — covers state_space.py:249."""
        from synapsys.core.transfer_function import TransferFunction
        G_ss = StateSpace([[-1]], [[1]], [[1]], [[0]])
        G_tf = TransferFunction([1], [1, 2])
        result = G_ss + G_tf
        assert isinstance(result, StateSpace)
