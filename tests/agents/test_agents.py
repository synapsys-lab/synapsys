import time

import numpy as np
import pytest

from synapsys.agents import ControllerAgent, PlantAgent, SyncEngine, SyncMode
from synapsys.api.matlab_compat import c2d, ss
from synapsys.transport import SharedMemoryTransport

BUS = "synapsys_test_agents"
CHANNELS = {"y": 1, "u": 1}


@pytest.fixture()
def discrete_plant():
    plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])
    return c2d(plant_c, dt=0.01)


class TestPlantAgent:
    def test_requires_discrete_plant(self):
        plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])
        # Need a valid transport just to instantiate; discard it after
        with SharedMemoryTransport(BUS, CHANNELS, create=True) as t:
            sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
            with pytest.raises(ValueError, match="discrete"):
                PlantAgent("plant", plant_c, t, sync)

    def test_plant_and_controller_converge(self, discrete_plant):
        """
        Plant and controller each hold their own transport handle to the same
        shared-memory bus.  This mirrors the real multi-process setup.
        """
        setpoint = 5.0

        # Owner allocates the block; keeps it alive for the whole test.
        owner = SharedMemoryTransport(BUS, CHANNELS, create=True)
        owner.write("u", np.array([0.0]))
        owner.write("y", np.array([0.0]))

        # Each agent gets its own client view (as they would in separate processes).
        t_plant = SharedMemoryTransport(BUS, CHANNELS, create=False)
        t_ctrl = SharedMemoryTransport(BUS, CHANNELS, create=False)

        sync_p = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
        sync_c = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)

        plant = PlantAgent("plant", discrete_plant, t_plant, sync_p)

        def law(y: np.ndarray) -> np.ndarray:
            return np.array([3.0 * (setpoint - y[0])])

        ctrl = ControllerAgent("ctrl", law, t_ctrl, sync_c)

        plant.start(blocking=False)
        ctrl.start(blocking=False)

        time.sleep(0.5)

        plant.stop()
        ctrl.stop()

        y_final = owner.read("y")[0]

        t_plant.close()
        t_ctrl.close()
        owner.close()

        # With Kp=3 and G(s)=1/(s+1) → closed-loop DC gain = 3/4 = 0.75
        # steady-state y = 0.75 * setpoint = 3.75
        assert y_final == pytest.approx(3.75, abs=0.5)


# ---------------------------------------------------------------------------
# ACLMessage — reply() and __repr__
# ---------------------------------------------------------------------------


class TestACLMessage:
    def test_reply_swaps_sender_and_receiver(self):
        from synapsys.agents.acl import ACLMessage, Performative

        msg = ACLMessage(Performative.INFORM, "agent_a", "agent_b", {"val": 1})
        reply = msg.reply(Performative.AGREE, {"ok": True})
        assert reply.sender == "agent_b"
        assert reply.receiver == "agent_a"
        assert reply.performative == Performative.AGREE

    def test_repr_contains_performative_and_agents(self):
        from synapsys.agents.acl import ACLMessage, Performative

        msg = ACLMessage(Performative.INFORM, "sender", "receiver", {})
        r = repr(msg)
        assert "inform" in r
        assert "sender" in r
        assert "receiver" in r


# ---------------------------------------------------------------------------
# BaseAgent — blocking start and unhandled exception path
# ---------------------------------------------------------------------------


class TestBaseAgentLifecycle:
    def _make_broker(self, bus_name: str):
        """Return a minimal broker with plant/y and plant/u topics."""
        import numpy as np

        from synapsys.broker import MessageBroker, SharedMemoryBackend, Topic

        topic_y = Topic("plant/y", shape=(1,))
        topic_u = Topic("plant/u", shape=(1,))
        broker = MessageBroker()
        broker.declare_topic(topic_y)
        broker.declare_topic(topic_u)
        broker.add_backend(
            SharedMemoryBackend(bus_name, [topic_y, topic_u], create=True)
        )
        broker.publish("plant/y", np.zeros(1))
        broker.publish("plant/u", np.zeros(1))
        return broker

    def test_start_blocking_runs_in_current_thread(self):
        """start(blocking=True) runs _run() synchronously — covers lifecycle.py:89."""
        from synapsys.agents import PlantAgent, SyncEngine, SyncMode
        from synapsys.api.matlab_compat import c2d, ss

        broker = self._make_broker("lifecycle_blocking_bus")
        plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=0.05)
        sync = SyncEngine(SyncMode.LOCK_STEP, dt=0.05)
        steps = [0]

        class SelfStoppingPlant(PlantAgent):
            def step(self_inner):
                steps[0] += 1
                if steps[0] >= 3:
                    self_inner._running = False

        agent = SelfStoppingPlant(
            "self_stop",
            plant_d,
            None,
            sync,
            channel_y="plant/y",
            channel_u="plant/u",
            broker=broker,
        )
        agent.start(blocking=True)  # returns only when _running becomes False
        broker.close()
        assert steps[0] >= 3

    def test_unhandled_exception_in_step_is_caught(self):
        """Exception in step() is caught by _run() — covers lifecycle.py:112-113."""
        from synapsys.agents import SyncEngine, SyncMode
        from synapsys.agents.lifecycle import BaseAgent

        class BoomAgent(BaseAgent):
            def setup(self):
                pass

            def step(self):
                raise RuntimeError("boom")

            def teardown(self):
                pass

        sync = SyncEngine(SyncMode.LOCK_STEP, dt=0.01)
        agent = BoomAgent("boom", None, sync)
        # start blocking — exception is caught internally, agent stops cleanly
        # Exception is caught — _run() returns but _running is not reset
        agent.start(blocking=True)
        # If we reach here, the exception was caught and teardown ran cleanly


# ---------------------------------------------------------------------------
# PlantAgent — x0 wrong size validation
# ---------------------------------------------------------------------------


class TestPlantAgentX0:
    def test_x0_wrong_size_raises(self):
        """x0 with wrong number of elements raises ValueError."""
        import numpy as np

        from synapsys.agents import PlantAgent, SyncEngine, SyncMode
        from synapsys.api.matlab_compat import c2d, ss
        from synapsys.broker import MessageBroker, SharedMemoryBackend, Topic

        plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=0.01)
        topic_y = Topic("plant/y", shape=(1,))
        topic_u = Topic("plant/u", shape=(1,))
        broker = MessageBroker()
        broker.declare_topic(topic_y)
        broker.declare_topic(topic_u)
        broker.add_backend(
            SharedMemoryBackend("x0_test_bus", [topic_y, topic_u], create=True)
        )

        with pytest.raises(ValueError, match="x0 must have"):
            PlantAgent(
                "plant",
                plant_d,
                None,
                SyncEngine(SyncMode.LOCK_STEP, dt=0.01),
                channel_y="plant/y",
                channel_u="plant/u",
                broker=broker,
                x0=np.array([1.0, 2.0]),  # wrong: plant has 1 state
            )
        broker.close()


# ---------------------------------------------------------------------------
# HardwareAgent — TimeoutError and generic exception paths
# ---------------------------------------------------------------------------


class TestHardwareAgentTimeouts:
    BUS = "hw_timeout_cov"

    def _make_transport(self, suffix: str):
        name = self.BUS + suffix
        channels = {"y": 1, "u": 1}
        owner = SharedMemoryTransport(name, channels, create=True)
        owner.write("y", np.zeros(1))
        owner.write("u", np.zeros(1))
        t_hw = SharedMemoryTransport(name, channels)
        return owner, t_hw

    def test_step_read_timeout_is_caught(self):
        """TimeoutError from read_outputs is caught — covers hardware_agent.py:95-96."""
        from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
        from synapsys.hw import MockHardwareInterface

        class TimeoutRead(MockHardwareInterface):
            def read_outputs(self, timeout_ms: float = 100.0) -> np.ndarray:
                raise TimeoutError

        hw = TimeoutRead(n_inputs=1, n_outputs=1)
        owner, t_hw = self._make_transport("_r")
        sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.05)
        agent = HardwareAgent("hw_r", hw, t_hw, sync)
        with hw:
            agent.setup()
            agent.step()  # must not raise
        t_hw.close()
        owner.close()

    def test_step_write_timeout_is_caught(self):
        """TimeoutError from write_inputs is caught in step()."""
        from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
        from synapsys.hw import MockHardwareInterface

        class TimeoutWrite(MockHardwareInterface):
            def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
                raise TimeoutError

        hw = TimeoutWrite(n_inputs=1, n_outputs=1)
        owner, t_hw = self._make_transport("_w")
        sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.05)
        agent = HardwareAgent("hw_w", hw, t_hw, sync)
        with hw:
            agent.setup()
            agent.step()  # must not raise
        t_hw.close()
        owner.close()

    def test_teardown_timeout_is_caught(self):
        """TimeoutError from write_inputs during teardown is caught."""
        from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
        from synapsys.hw import MockHardwareInterface

        class TimeoutWrite(MockHardwareInterface):
            def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
                raise TimeoutError

        hw = TimeoutWrite(n_inputs=1, n_outputs=1)
        sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.05)
        agent = HardwareAgent("hw_td", hw, None, sync)
        agent.teardown()  # must not raise

    def test_teardown_generic_exception_is_caught(self):
        """Generic exception from write_inputs during teardown is caught."""
        from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
        from synapsys.hw import MockHardwareInterface

        class BrokenWrite(MockHardwareInterface):
            def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
                raise RuntimeError("device failure")

        hw = BrokenWrite(n_inputs=1, n_outputs=1)
        sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.05)
        agent = HardwareAgent("hw_ex", hw, None, sync)
        agent.teardown()  # must not raise


# ---------------------------------------------------------------------------
# PlantAgent — x0 correct size (success path)
# ---------------------------------------------------------------------------


class TestPlantAgentX0Valid:
    def test_x0_correct_size_sets_initial_state(self):
        """PlantAgent with valid x0 assigns it — covers plant_agent.py:69."""
        from synapsys.agents import PlantAgent, SyncEngine, SyncMode
        from synapsys.api.matlab_compat import c2d, ss

        plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=0.01)
        sync = SyncEngine(SyncMode.LOCK_STEP, dt=0.01)
        agent = PlantAgent("p", plant_d, None, sync, x0=np.array([0.5]))
        np.testing.assert_allclose(agent._x, [0.5])
