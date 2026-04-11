"""Tests for MockHardwareInterface and HardwareAgent."""

from __future__ import annotations

import time

import numpy as np

from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
from synapsys.hw import MockHardwareInterface
from synapsys.transport import SharedMemoryTransport


class TestMockHardwareInterface:
    def test_connect_disconnect(self):
        hw = MockHardwareInterface(n_inputs=1, n_outputs=1)
        hw.connect()
        assert hw._connected
        hw.disconnect()
        assert not hw._connected

    def test_context_manager(self):
        hw = MockHardwareInterface(n_inputs=2, n_outputs=3)
        with hw:
            assert hw._connected
        assert not hw._connected

    def test_n_inputs_n_outputs(self):
        hw = MockHardwareInterface(n_inputs=2, n_outputs=3)
        assert hw.n_inputs == 2
        assert hw.n_outputs == 3

    def test_default_unity_plant_fn(self):
        hw = MockHardwareInterface(n_inputs=2, n_outputs=2)
        with hw:
            hw.write_inputs(np.array([3.0, -1.0]))
            y = hw.read_outputs()
        np.testing.assert_allclose(y, [3.0, -1.0])

    def test_custom_plant_fn(self):
        def double(u: np.ndarray) -> np.ndarray:
            return u * 2.0

        hw = MockHardwareInterface(n_inputs=1, n_outputs=1, plant_fn=double)
        with hw:
            hw.write_inputs(np.array([5.0]))
            y = hw.read_outputs()
        np.testing.assert_allclose(y, [10.0])

    def test_read_before_write_returns_zeros(self):
        hw = MockHardwareInterface(n_inputs=1, n_outputs=1)
        with hw:
            y = hw.read_outputs()
        np.testing.assert_allclose(y, [0.0])

    def test_mismatched_n_inputs_n_outputs_returns_zeros(self):
        hw = MockHardwareInterface(n_inputs=2, n_outputs=3)
        with hw:
            hw.write_inputs(np.array([1.0, 2.0]))
            y = hw.read_outputs()
        assert y.shape == (3,)
        np.testing.assert_allclose(y, [0.0, 0.0, 0.0])

    def test_latency_slows_reads(self):
        hw = MockHardwareInterface(n_inputs=1, n_outputs=1, latency_ms=30.0)
        with hw:
            t0 = time.monotonic()
            hw.read_outputs()
            elapsed = time.monotonic() - t0
        assert elapsed >= 0.025   # at least 25 ms


class TestHardwareAgent:
    BUS = "hw_agent_test"

    def test_hardware_agent_pumps_data(self):
        """HardwareAgent should write hw y to transport each tick."""
        # First-order plant: y(k+1) = 0.9*y(k) + 0.1*u(k)
        state = [0.0]

        def plant_fn(u: np.ndarray) -> np.ndarray:
            state[0] = 0.9 * state[0] + 0.1 * u[0]
            return np.array([state[0]])

        hw = MockHardwareInterface(n_inputs=1, n_outputs=1, plant_fn=plant_fn)
        channels = {"y": 1, "u": 1}

        owner = SharedMemoryTransport(self.BUS, channels, create=True)
        owner.write("y", np.array([0.0]))
        owner.write("u", np.array([1.0]))   # constant control input

        t_hw = SharedMemoryTransport(self.BUS, channels)
        sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
        agent = HardwareAgent("hw", hw, t_hw, sync)

        with hw:
            agent.start(blocking=False)
            time.sleep(0.12)   # ~12 ticks at 100 Hz
            agent.stop()

        y_final = owner.read("y")[0]
        t_hw.close()
        owner.close()

        # y should have moved toward steady-state (1/(1-0.9) * 0.1 * 1.0 = 1.0)
        assert y_final > 0.1

    def test_hardware_agent_zero_on_teardown(self):
        """HardwareAgent.teardown() sends zero to hardware."""
        received_zeros: list[np.ndarray] = []
        def original_fn(u: np.ndarray) -> np.ndarray:
            return np.zeros(1)

        class TrackingMock(MockHardwareInterface):
            def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
                received_zeros.append(u.copy())
                super().write_inputs(u, timeout_ms)

        hw = TrackingMock(n_inputs=1, n_outputs=1, plant_fn=original_fn)
        channels = {"y": 1, "u": 1}
        owner = SharedMemoryTransport(self.BUS + "_td", channels, create=True)
        owner.write("y", np.array([0.0]))
        owner.write("u", np.array([0.0]))

        t_hw = SharedMemoryTransport(self.BUS + "_td", channels)
        agent = HardwareAgent("hw_td", hw, t_hw,
                              SyncEngine(SyncMode.WALL_CLOCK, dt=0.05))
        with hw:
            agent.start(blocking=False)
            time.sleep(0.06)
            agent.stop()

        t_hw.close()
        owner.close()

        # Last write in teardown must be zeros
        last = received_zeros[-1]
        np.testing.assert_allclose(last, [0.0])
