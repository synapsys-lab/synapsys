"""
Integration tests: agents wired through MessageBroker.

Scenario A: PlantAgent + ControllerAgent converge (broker replaces transport).
Scenario B: 3-agent — ReconfigAgent publishes new gains; ControllerAgent reacts.
"""
import time

import numpy as np
import pytest

from synapsys.api import ss, c2d
from synapsys.agents import ControllerAgent, PlantAgent, SyncEngine, SyncMode
from synapsys.agents.lifecycle import BaseAgent
from synapsys.algorithms import PID
from synapsys.broker.backends.shared_memory import SharedMemoryBackend
from synapsys.broker.broker import MessageBroker
from synapsys.broker.topic import Topic


def _build_broker(bus_name: str, topics: list[Topic]) -> MessageBroker:
    broker = MessageBroker()
    for t in topics:
        broker.declare_topic(t)
    backend = SharedMemoryBackend(bus_name, topics, create=True)
    broker.add_backend(backend)
    return broker


# ── Scenario A ────────────────────────────────────────────────────────────────

class TestBrokerConvergence:
    """Plant+Controller via broker converges the same as via transport."""

    def test_closed_loop_converges_to_setpoint(self):
        plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])
        plant_d = c2d(plant_c, dt=0.05)

        topic_y = Topic("A/y", shape=(1,))
        topic_u = Topic("A/u", shape=(1,))
        broker = _build_broker("broker_integ_A", [topic_y, topic_u])

        setpoint = 3.0
        pid = PID(Kp=4.0, Ki=1.0, dt=0.05)
        law = lambda y: np.array([pid.compute(setpoint=setpoint, measurement=y[0])])

        broker.publish("A/y", np.zeros(1))
        broker.publish("A/u", np.zeros(1))

        sync_p = SyncEngine(SyncMode.LOCK_STEP, dt=0.05)
        sync_c = SyncEngine(SyncMode.LOCK_STEP, dt=0.05)

        plant = PlantAgent("plant", plant_d, None, sync_p,
                           channel_y="A/y", channel_u="A/u", broker=broker)
        ctrl = ControllerAgent("ctrl", law, None, sync_c,
                               channel_y="A/y", channel_u="A/u", broker=broker)

        plant.setup()
        for _ in range(400):
            ctrl.step()
            plant.step()

        y_final = broker.read("A/y")[0]
        assert abs(y_final - setpoint) < 0.15, f"Did not converge: y={y_final}"
        broker.close()


# ── Scenario B ────────────────────────────────────────────────────────────────

class _ReconfigAgent(BaseAgent):
    """Publishes new PID setpoint after a configurable delay."""

    def __init__(self, broker: MessageBroker, delay_steps: int):
        sync = SyncEngine(SyncMode.LOCK_STEP, dt=0.05)
        super().__init__("reconfig", None, sync, broker=broker)
        self._delay = delay_steps
        self._k = 0
        self.published = False

    def setup(self) -> None:
        pass

    def step(self) -> None:
        self._k += 1
        if self._k == self._delay:
            self._write("ctrl/config", np.array([10.0]))  # new setpoint
            self.published = True

    def teardown(self) -> None:
        pass


class TestThreeAgentReconfig:
    """ReconfigAgent changes setpoint; ControllerAgent adapts."""

    def test_reconfig_agent_changes_setpoint_mid_simulation(self):
        plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])
        plant_d = c2d(plant_c, dt=0.05)

        topic_y = Topic("B/y", shape=(1,))
        topic_u = Topic("B/u", shape=(1,))
        topic_cfg = Topic("ctrl/config", shape=(1,))
        broker = _build_broker("broker_integ_B", [topic_y, topic_u, topic_cfg])

        broker.publish("B/y", np.zeros(1))
        broker.publish("B/u", np.zeros(1))
        broker.publish("ctrl/config", np.array([3.0]))  # initial setpoint

        pid = PID(Kp=4.0, Ki=1.0, dt=0.05)

        def law(y: np.ndarray) -> np.ndarray:
            cfg = broker.read("ctrl/config")
            return np.array([pid.compute(setpoint=cfg[0], measurement=y[0])])

        sync_p = SyncEngine(SyncMode.LOCK_STEP, dt=0.05)
        sync_c = SyncEngine(SyncMode.LOCK_STEP, dt=0.05)

        plant = PlantAgent("plant", plant_d, None, sync_p,
                           channel_y="B/y", channel_u="B/u", broker=broker)
        ctrl = ControllerAgent("ctrl", law, None, sync_c,
                               channel_y="B/y", channel_u="B/u", broker=broker)
        reconfig = _ReconfigAgent(broker, delay_steps=100)

        for _ in range(200):
            reconfig.step()
            ctrl.step()
            plant.step()

        assert reconfig.published, "ReconfigAgent never published"

        y_final = broker.read("B/y")[0]
        assert abs(y_final - 10.0) < 0.5, f"Did not converge to new setpoint: y={y_final}"
        broker.close()
