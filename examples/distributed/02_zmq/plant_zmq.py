"""
Distributed simulation via ZeroMQ — Plant process.

The plant publishes plant/y on tcp://0.0.0.0:5555 (PUB)
and subscribes to plant/u from the controller on tcp://localhost:5556 (SUB).

Can run on a different machine from controller_zmq.py.
Change CONTROLLER_HOST to the controller's IP address if remote.

Usage:
    python examples/distributed/02_zmq/plant_zmq.py
"""
import numpy as np

from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.broker import MessageBroker, Topic
from synapsys.broker.backends.zmq import ZMQBrokerBackend

CONTROLLER_HOST = "localhost"
DT              = 0.05     # 20 Hz
Y_ADDR          = "tcp://0.0.0.0:5555"
U_ADDR          = f"tcp://{CONTROLLER_HOST}:5556"

# G(s) = 1/(s+1) discretised with ZOH
plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT)

# ── Broker: publishes y, subscribes u ────────────────────────────────────────
topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)

# Two separate ZMQ backends: one PUB for y, one SUB for u
broker.add_backend(ZMQBrokerBackend(Y_ADDR, publish_topics=[topic_y]))
broker.add_backend(ZMQBrokerBackend(U_ADDR, subscribe_topics=[topic_u]))

broker.publish("plant/y", np.zeros(1))

import time; time.sleep(1.0)  # allow ZMQ sockets to bind

print(f"Plant: publishing plant/y on {Y_ADDR}")
print(f"Plant: subscribing plant/u from {U_ADDR}")

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
    print("\nPlant: done.")
finally:
    broker.close()
