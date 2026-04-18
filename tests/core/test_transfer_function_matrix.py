"""Tests for TransferFunctionMatrix — driven before any production code."""
import numpy as np
import pytest

from synapsys.core.transfer_function import TransferFunction
from synapsys.core.transfer_function_matrix import TransferFunctionMatrix

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def _2x2() -> TransferFunctionMatrix:
    """G = [[1/(s+1), 2/(s+2)], [3/(s+3), 4/(s+4)]]"""
    return TransferFunctionMatrix([
        [TransferFunction([1], [1, 1]), TransferFunction([2], [1, 2])],
        [TransferFunction([3], [1, 3]), TransferFunction([4], [1, 4])],
    ])


def _1x1() -> TransferFunctionMatrix:
    return TransferFunctionMatrix([[TransferFunction([1], [1, 1])]])


def _diagonal_2x2() -> TransferFunctionMatrix:
    """G = diag(1/(s+1), 1/(s+2)) — useful for step/evolve checks."""
    return TransferFunctionMatrix([
        [TransferFunction([1], [1, 1]), TransferFunction([0], [1])],
        [TransferFunction([0], [1]), TransferFunction([1], [1, 2])],
    ])


# ---------------------------------------------------------------------------
# Construction and dimensions
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_dimensions_2x2(self):
        G = _2x2()
        assert G.n_outputs == 2
        assert G.n_inputs == 2

    def test_dimensions_1x1(self):
        G = _1x1()
        assert G.n_outputs == 1
        assert G.n_inputs == 1

    def test_dimensions_1x3(self):
        G = TransferFunctionMatrix([[
            TransferFunction([1], [1, 1]),
            TransferFunction([1], [1, 2]),
            TransferFunction([1], [1, 3]),
        ]])
        assert G.n_outputs == 1
        assert G.n_inputs == 3

    def test_n_states_is_sum_of_element_orders(self):
        # Each 1/(s+k) is order-1; 2x2 has 4 elements → 4 states
        G = _2x2()
        assert G.n_states == 4

    def test_n_states_skips_zero_numerator_elements(self):
        # Zero-gain TFs ([0]/den) contribute 0 states to the SS realisation
        G = _diagonal_2x2()  # [[1/(s+1), 0], [0, 1/(s+2)]]
        # TF property len(den)-1: [1,0,0,0] = 2 active + 0+0 skipped = 2
        assert G.n_states == G.to_state_space().n_states

    def test_n_states_matches_statespace_realisation(self):
        # Explicit: 2 non-zero + 2 zero-numerator elements → 2 real states
        G = _diagonal_2x2()
        assert G.n_states == 2

    def test_n_states_zero_num_nontrivial_den(self):
        # TransferFunction([0], [1, 2]) has TF.n_states=1 but contributes 0
        # states to the SS realisation (zero-numerator skip)
        G = TransferFunctionMatrix([[
            TransferFunction([1], [1, 1]),
            TransferFunction([0], [1, 2]),  # zero num, non-trivial den
        ]])
        assert G.n_states == G.to_state_space().n_states

    def test_jagged_rows_raises(self):
        with pytest.raises(ValueError, match="same number"):
            TransferFunctionMatrix([
                [TransferFunction([1], [1, 1])],
                [TransferFunction([1], [1, 1]), TransferFunction([1], [1, 2])],
            ])

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            TransferFunctionMatrix([])

    def test_mixed_dt_raises(self):
        with pytest.raises(ValueError, match="dt"):
            TransferFunctionMatrix([
                [TransferFunction([1], [1, 1], dt=0.0),
                 TransferFunction([1], [1, 2], dt=0.1)],
            ])


# ---------------------------------------------------------------------------
# from_arrays factory
# ---------------------------------------------------------------------------

class TestFromArrays:
    def test_shared_denominator(self):
        G = TransferFunctionMatrix.from_arrays(
            num=[[1, 2], [3, 4]],
            den=[1, 3, 2],   # shared: (s+1)(s+2)
        )
        assert G.n_outputs == 2
        assert G.n_inputs == 2
        assert G[0, 0].den.tolist() == pytest.approx([1, 3, 2])
        assert G[1, 1].den.tolist() == pytest.approx([1, 3, 2])

    def test_per_element_denominator(self):
        G = TransferFunctionMatrix.from_arrays(
            num=[[[1], [2]], [[3], [4]]],
            den=[[[1, 1], [1, 2]], [[1, 3], [1, 4]]],
        )
        assert G.n_states == 4  # four first-order elements


# ---------------------------------------------------------------------------
# Item access
# ---------------------------------------------------------------------------

class TestItemAccess:
    def test_getitem_returns_transfer_function(self):
        G = _2x2()
        assert isinstance(G[0, 0], TransferFunction)

    def test_getitem_correct_numerator(self):
        G = _2x2()
        # G[1, 0] = 3/(s+3) — num = [3]
        np.testing.assert_allclose(G[1, 0].num, [3.0])

    def test_getitem_out_of_range_raises(self):
        G = _2x2()
        with pytest.raises(IndexError):
            _ = G[2, 0]


# ---------------------------------------------------------------------------
# LTIModel properties
# ---------------------------------------------------------------------------

class TestAnalysis:
    def test_poles_contains_all_element_poles(self):
        G = _2x2()
        p = np.sort(np.real(G.poles()))
        np.testing.assert_allclose(p, [-4.0, -3.0, -2.0, -1.0], atol=1e-8)

    def test_is_stable_true_for_stable_system(self):
        assert _2x2().is_stable()

    def test_is_stable_false_when_one_element_unstable(self):
        G = TransferFunctionMatrix([
            [TransferFunction([1], [1, -1]),   # unstable pole at +1
             TransferFunction([1], [1, 2])],
        ])
        assert not G.is_stable()

    def test_zeros_returns_ndarray(self):
        z = _2x2().zeros()
        assert isinstance(z, np.ndarray)

    def test_zeros_diagonal_with_known_zero(self):
        # G = diag((s+3)/(s+1), 1/(s+2)) — transmission zero at -3
        G = TransferFunctionMatrix([
            [TransferFunction([1, 3], [1, 1]), TransferFunction([0], [1])],
            [TransferFunction([0], [1]),        TransferFunction([1], [1, 2])],
        ])
        z = G.zeros()
        np.testing.assert_allclose(np.sort(np.real(z)), [-3.0], atol=1e-6)

    def test_dt_is_zero_for_continuous(self):
        assert _2x2().dt == 0.0

    def test_is_discrete_false_for_continuous(self):
        assert not _2x2().is_discrete


# ---------------------------------------------------------------------------
# to_state_space
# ---------------------------------------------------------------------------

class TestToStateSpace:
    def test_returns_statespace(self):
        from synapsys.core.state_space import StateSpace
        assert isinstance(_2x2().to_state_space(), StateSpace)

    def test_dimensions(self):
        ss = _2x2().to_state_space()
        assert ss.n_inputs == 2
        assert ss.n_outputs == 2
        assert ss.n_states == 4

    def test_dc_gains(self):
        # DC gain of 1/(s+k) at s=0 is 1/k
        # G DC = [[1/1, 2/2], [3/3, 4/4]] = [[1, 1], [1, 1]]
        ss = _2x2().to_state_space()
        # Simulate to steady state
        t = np.linspace(0, 30, 3000)
        u = np.ones((len(t), 2))
        _, y = ss.simulate(t, u)
        np.testing.assert_allclose(y[-1], [1.0 + 1.0, 1.0 + 1.0], atol=1e-2)

    def test_1x1_to_state_space_matches_single_tf(self):
        G = _1x1()
        ss = G.to_state_space()
        _, y_ss = ss.step()
        _, y_tf = G[0, 0].step()
        np.testing.assert_allclose(y_ss[-1], y_tf[-1], atol=1e-3)


# ---------------------------------------------------------------------------
# to_transfer_function
# ---------------------------------------------------------------------------

class TestToTransferFunction:
    def test_1x1_returns_transfer_function(self):
        G = _1x1()
        tf = G.to_transfer_function()
        assert isinstance(tf, TransferFunction)

    def test_mimo_raises(self):
        with pytest.raises(ValueError, match="SISO"):
            _2x2().to_transfer_function()


# ---------------------------------------------------------------------------
# Algebra
# ---------------------------------------------------------------------------

class TestAlgebra:
    def test_neg_flips_numerator_sign(self):
        G = _1x1()
        neg = -G
        np.testing.assert_allclose(neg[0, 0].num, -G[0, 0].num)

    def test_add_parallel_dimensions(self):
        G = _2x2()
        result = G + G
        assert result.n_inputs == 2
        assert result.n_outputs == 2

    def test_add_parallel_doubles_dc_gain(self):
        # G[0,0] = 1/(s+1); (G+G)[0,0] has DC gain = 2
        G = _2x2()
        result = G + G
        dc = result[0, 0].num[0] / result[0, 0].den[-1]
        np.testing.assert_allclose(dc, 2.0, atol=1e-8)

    def test_add_incompatible_shapes_raises(self):
        G1 = _2x2()
        G2 = TransferFunctionMatrix([[TransferFunction([1], [1, 1])]])
        with pytest.raises(ValueError, match="shape"):
            G1 + G2

    def test_mul_series_dimensions(self):
        # (2×2) * (2×2) → (2×2)
        G = _2x2()
        result = G * G
        assert result.n_inputs == 2
        assert result.n_outputs == 2

    def test_mul_series_incompatible_raises(self):
        G1 = _2x2()
        G3 = TransferFunctionMatrix([
            [TransferFunction([1], [1, 1])],
            [TransferFunction([1], [1, 2])],
            [TransferFunction([1], [1, 3])],
        ])
        with pytest.raises(ValueError, match="inner"):
            G1 * G3


# ---------------------------------------------------------------------------
# Simulation (delegates to StateSpace)
# ---------------------------------------------------------------------------

class TestSimulation:
    def test_step_returns_arrays(self):
        G = _1x1()  # step() delegates to SS, only well-defined for SISO/single-input
        t, y = G.step()
        assert t.ndim == 1
        assert y.ndim >= 1

    def test_simulate_via_tfm(self):
        G = _diagonal_2x2()
        t = np.linspace(0, 10, 500)
        u = np.ones((len(t), 2))
        t_out, y = G.simulate(t, u)
        assert y.shape[1] == 2

    def test_bode_returns_three_arrays(self):
        G = _1x1()  # bode() delegates to SS; only well-defined for single-channel
        w, mag, phase = G.bode()
        assert w.ndim == 1 and mag.ndim >= 1

    def test_evolve_returns_correct_shapes(self):
        Gd = _diagonal_2x2().to_state_space()
        from synapsys.api.matlab_compat import c2d
        Gd_disc = c2d(Gd, dt=0.1)
        x = np.zeros(Gd_disc.n_states)
        u = np.array([1.0, 1.0])
        x_next, y = Gd_disc.evolve(x, u)
        assert x_next.shape == (Gd_disc.n_states,)
        assert y.shape == (2,)

    def test_simulate_dc_gain(self):
        G = _diagonal_2x2().to_state_space()
        t = np.linspace(0, 20, 2000)
        u = np.ones((len(t), 2))
        _, y = G.simulate(t, u)
        # DC gain: 1/(s+1)|s=0 = 1.0, 1/(s+2)|s=0 = 0.5
        np.testing.assert_allclose(y[-1, 0], 1.0, atol=1e-2)
        np.testing.assert_allclose(y[-1, 1], 0.5, atol=1e-2)
