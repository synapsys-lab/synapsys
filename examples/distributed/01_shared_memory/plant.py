"""
Distributed simulation — Plant process.

Run this FIRST, then start controller.py in a separate terminal.

The plant exposes its state on a MessageBroker backed by shared memory.
Two topics are declared:
    plant/y  — plant output (scalar)
    plant/u  — control input (scalar, written by the controller)

Usage:
    python examples/distributed/01_shared_memory/plant.py
"""
import numpy as np

from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend

BUS_NAME = "synapsys_demo"
DT       = 0.05   # 20 Hz

# G(s) = 1/(s+1) discretised with ZOH
plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT)

# ── Broker setup ──────────────────────────────────────────────────────────────
topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend(BUS_NAME, [topic_y, topic_u], create=True))

broker.publish("plant/y", np.zeros(1))
broker.publish("plant/u", np.zeros(1))

print(f"Plant: bus '{BUS_NAME}' ready.  Starting in 2 s — launch controller.py now.")
import time; time.sleep(2.0)

# ── Agent ─────────────────────────────────────────────────────────────────────
sync  = SyncEngine(SyncMode.WALL_CLOCK, dt=DT)
agent = PlantAgent(
    "plant", plant_d, None, sync,
    channel_y="plant/y", channel_u="plant/u",
    broker=broker,
)

print("Plant running.  Press Ctrl+C to stop.")
try:
    agent.start(blocking=True)
except KeyboardInterrupt:
    print("\nPlant: stopped.")
finally:
    broker.close()
