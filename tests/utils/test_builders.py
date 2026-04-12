import numpy as np
import pytest

from synapsys.utils.builders import StateEquations


# ── fixture: 2-DOF mass-spring-damper ────────────────────────────────────────

M, C_DAMP, K = 1.0, 0.1, 2.0

STATES = ["x1", "x2", "v1", "v2"]
INPUTS = ["F"]


def make_2dof() -> StateEquations:
    return (
        StateEquations(states=STATES, inputs=INPUTS)
        .eq("x1", v1=1)
        .eq("x2", v2=1)
        .eq("v1", x1=-2 * K / M, x2=K / M, v1=-C_DAMP / M)
        .eq("v2", x1=K / M, x2=-2 * K / M, v2=-C_DAMP / M, F=K / M)
    )


EXPECTED_A = np.array([
    [0,           0,          1,          0         ],
    [0,           0,          0,          1         ],
    [-2 * K / M,  K / M,     -C_DAMP / M, 0         ],
    [K / M,      -2 * K / M,  0,         -C_DAMP / M],
])

EXPECTED_B = np.array([[0.0], [0.0], [0.0], [K / M]])


# ── A matrix ─────────────────────────────────────────────────────────────────

class TestAMatrix:
    def test_shape(self):
        eqs = make_2dof()
        assert eqs.A.shape == (4, 4)

    def test_values_match_manual(self):
        np.testing.assert_allclose(make_2dof().A, EXPECTED_A)

    def test_returns_copy(self):
        eqs = make_2dof()
        A1 = eqs.A
        A1[0, 0] = 999.0
        assert eqs.A[0, 0] != 999.0

    def test_zeros_for_unset_entries(self):
        eqs = StateEquations(states=["x", "v"], inputs=["u"]).eq("v", x=-1.0)
        assert eqs.A[0, 0] == pytest.approx(0.0)   # ẋ row never set
        assert eqs.A[1, 0] == pytest.approx(-1.0)


# ── B matrix ─────────────────────────────────────────────────────────────────

class TestBMatrix:
    def test_shape(self):
        eqs = make_2dof()
        assert eqs.B.shape == (4, 1)

    def test_values_match_manual(self):
        np.testing.assert_allclose(make_2dof().B, EXPECTED_B)

    def test_returns_copy(self):
        eqs = make_2dof()
        B1 = eqs.B
        B1[3, 0] = 999.0
        assert eqs.B[3, 0] != 999.0

    def test_no_inputs_gives_zero_B(self):
        eqs = StateEquations(states=["x", "v"]).eq("v", x=-1.0)
        assert eqs.B.shape == (2, 0)

    def test_multiple_inputs(self):
        eqs = (
            StateEquations(states=["x"], inputs=["u1", "u2"])
            .eq("x", u1=2.0, u2=-1.0)
        )
        assert eqs.B.shape == (1, 2)
        np.testing.assert_allclose(eqs.B, [[2.0, -1.0]])


# ── output (C matrix) ─────────────────────────────────────────────────────────

class TestOutput:
    def test_shape(self):
        C = make_2dof().output("x1", "x2")
        assert C.shape == (2, 4)

    def test_selects_correct_rows(self):
        C = make_2dof().output("x1", "x2")
        np.testing.assert_array_equal(C, [[1, 0, 0, 0], [0, 1, 0, 0]])

    def test_single_output(self):
        C = make_2dof().output("v1")
        assert C.shape == (1, 4)
        np.testing.assert_array_equal(C[0], [0, 0, 1, 0])

    def test_all_states_as_outputs(self):
        eqs = make_2dof()
        C = eqs.output(*STATES)
        np.testing.assert_array_equal(C, np.eye(4))

    def test_output_order_respected(self):
        C1 = make_2dof().output("x1", "x2")
        C2 = make_2dof().output("x2", "x1")
        np.testing.assert_array_equal(C1[0], C2[1])
        np.testing.assert_array_equal(C1[1], C2[0])

    def test_no_states_raises(self):
        with pytest.raises(ValueError):
            make_2dof().output()

    def test_unknown_state_raises(self):
        with pytest.raises(ValueError, match="'z'"):
            make_2dof().output("z")


# ── eq() validation ───────────────────────────────────────────────────────────

class TestEqValidation:
    def test_unknown_state_raises(self):
        with pytest.raises(ValueError, match="'z'"):
            StateEquations(states=["x"], inputs=["u"]).eq("z", x=1.0)

    def test_unknown_coefficient_raises(self):
        with pytest.raises(ValueError, match="'q'"):
            StateEquations(states=["x"], inputs=["u"]).eq("x", q=1.0)

    def test_fluent_returns_self(self):
        eqs = StateEquations(states=["x", "v"], inputs=["u"])
        result = eqs.eq("v", x=-1.0)
        assert result is eqs


# ── fluent chaining ───────────────────────────────────────────────────────────

class TestFluentChaining:
    def test_chain_overwrites_coefficient(self):
        eqs = (
            StateEquations(states=["x", "v"], inputs=["u"])
            .eq("v", x=-1.0)
            .eq("v", x=-5.0)   # override
        )
        assert eqs.A[1, 0] == pytest.approx(-5.0)

    def test_first_order_system(self):
        # ẋ = -2x + 3u  →  A=[-2], B=[3]
        eqs = StateEquations(states=["x"], inputs=["u"]).eq("x", x=-2.0, u=3.0)
        assert eqs.A[0, 0] == pytest.approx(-2.0)
        assert eqs.B[0, 0] == pytest.approx(3.0)


# ── integration: build StateSpace ────────────────────────────────────────────

class TestIntegrationWithSS:
    def test_builds_stable_system(self):
        from synapsys.api import ss

        eqs = make_2dof()
        C = eqs.output("x1", "x2")
        D = np.zeros((2, 1))
        G = ss(eqs.A, eqs.B, C, D)

        assert G.n_states == 4
        assert G.is_stable()

    def test_step_response_converges(self):
        from synapsys.api import ss, step

        # Simple stable 1st-order: ẋ = -x + u, y = x  →  DC gain = 1
        eqs = StateEquations(states=["x"], inputs=["u"]).eq("x", x=-1.0, u=1.0)
        G = ss(eqs.A, eqs.B, eqs.output("x"), np.zeros((1, 1)))
        _, y = step(G)
        np.testing.assert_allclose(y[-1], 1.0, atol=1e-3)
