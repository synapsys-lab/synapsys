import pytest

from synapsys.algorithms.pid import PID


class TestPID:
    def test_proportional_only(self):
        pid = PID(Kp=2.0)
        u = pid.compute(setpoint=5.0, measurement=0.0)
        assert u == pytest.approx(10.0)

    def test_saturation_upper(self):
        pid = PID(Kp=100.0, u_min=-1.0, u_max=1.0)
        u = pid.compute(setpoint=10.0, measurement=0.0)
        assert u == pytest.approx(1.0)

    def test_saturation_lower(self):
        pid = PID(Kp=100.0, u_min=-1.0, u_max=1.0)
        u = pid.compute(setpoint=-10.0, measurement=0.0)
        assert u == pytest.approx(-1.0)

    def test_integral_accumulates(self):
        pid = PID(Kp=0.0, Ki=1.0, dt=0.1)
        pid.compute(1.0, 0.0)  # integral = 0.1
        u = pid.compute(1.0, 0.0)  # integral = 0.2
        assert u == pytest.approx(0.2, rel=1e-6)

    def test_derivative(self):
        pid = PID(Kp=0.0, Kd=1.0, dt=0.1)
        pid.compute(1.0, 0.0)  # prev_error = 1.0
        u = pid.compute(0.5, 0.0)  # error = 0.5, deriv = (0.5-1.0)/0.1 = -5
        assert u == pytest.approx(-5.0, rel=1e-6)

    def test_reset_clears_state(self):
        pid = PID(Kp=1.0, Ki=1.0, dt=0.1)
        pid.compute(10.0, 0.0)
        pid.reset()
        u = pid.compute(1.0, 0.0)
        # After reset: integral = 0.1, P = 1.0 => u = 1.0 + 0.1 = 1.1
        assert u == pytest.approx(1.1, rel=1e-6)

    def test_repr(self):
        pid = PID(Kp=1.0, Ki=0.5, Kd=0.1)
        assert "PID" in repr(pid)

    def test_dt_zero_raises(self):
        with pytest.raises(ValueError, match="dt must be > 0"):
            PID(Kp=1.0, dt=0.0)

    def test_dt_negative_raises(self):
        with pytest.raises(ValueError, match="dt must be > 0"):
            PID(Kp=1.0, dt=-0.01)

    def test_u_min_ge_u_max_raises(self):
        with pytest.raises(ValueError, match="u_min"):
            PID(Kp=1.0, u_min=5.0, u_max=5.0)
