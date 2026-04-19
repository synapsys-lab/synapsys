"""
Distributed simulation — Controller process.

Run AFTER starting plant.py in a separate terminal.

The controller reads plant/y from the shared-memory broker, computes a PID
control action, and publishes it to plant/u — without sharing any code with
the plant process.

Usage:
    python examples/distributed/01_shared_memory/controller.py
"""

import numpy as np

from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.broker import MessageBroker, SharedMemoryBackend, Topic

BUS_NAME = "synapsys_demo"
DT = 0.025  # 40 Hz — faster than the plant
SETPOINT = 5.0

# ── Broker setup (connects to existing bus — create=False) ────────────────────
topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

try:
    broker = MessageBroker()
    broker.declare_topic(topic_y)
    broker.declare_topic(topic_u)
    broker.add_backend(SharedMemoryBackend(BUS_NAME, [topic_y, topic_u], create=False))
except FileNotFoundError:
    print("Error: start plant.py first to initialise the shared-memory bus.")
    raise SystemExit(1)

# ── Control law ───────────────────────────────────────────────────────────────
pid = PID(Kp=3.0, Ki=0.5, dt=DT, u_min=-10.0, u_max=10.0)
law = lambda y: np.array([pid.compute(setpoint=SETPOINT, measurement=y[0])])

print(f"Controller: connected to '{BUS_NAME}'.  Setpoint = {SETPOINT}")

sync = SyncEngine(SyncMode.WALL_CLOCK, dt=DT)
agent = ControllerAgent(
    "ctrl",
    law,
    None,
    sync,
    channel_y="plant/y",
    channel_u="plant/u",
    broker=broker,
)

try:
    agent.start(blocking=True)
except KeyboardInterrupt:
    print("\nController: stopped.")
finally:
    broker.close()
