"""
Distributed simulation via ZeroMQ — Controller process.

The controller subscribes to plant/y from tcp://localhost:5555 (SUB)
and publishes plant/u on tcp://0.0.0.0:5556 (PUB).

Can run on a different machine from plant_zmq.py.
Change PLANT_HOST to the plant's IP address if remote.

Usage:
    python examples/distributed/02_zmq/controller_zmq.py
"""
import numpy as np

from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.broker import MessageBroker, Topic
from synapsys.broker.backends.zmq import ZMQBrokerBackend

PLANT_HOST = "localhost"
DT         = 0.025      # 40 Hz — 2× plant rate
SETPOINT   = 5.0
Y_ADDR     = f"tcp://{PLANT_HOST}:5555"
U_ADDR     = "tcp://0.0.0.0:5556"

# ── Broker: subscribes y, publishes u ────────────────────────────────────────
topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)

broker.add_backend(ZMQBrokerBackend(Y_ADDR, subscribe_topics=[topic_y]))
broker.add_backend(ZMQBrokerBackend(U_ADDR, publish_topics=[topic_u]))

# ── Control law ───────────────────────────────────────────────────────────────
pid = PID(Kp=3.0, Ki=0.5, dt=DT, u_min=-20.0, u_max=20.0)
law = lambda y: np.array([pid.compute(setpoint=SETPOINT, measurement=y[0])])

import time; time.sleep(0.5)  # let plant start first

print(f"Controller: subscribing plant/y from {Y_ADDR}")
print(f"Controller: publishing plant/u on {U_ADDR}")
print(f"Setpoint = {SETPOINT}")

sync  = SyncEngine(SyncMode.WALL_CLOCK, dt=DT)
agent = ControllerAgent(
    "ctrl", law, None, sync,
    channel_y="plant/y", channel_u="plant/u",
    broker=broker,
)

try:
    agent.start(blocking=True)
except KeyboardInterrupt:
    print("\nController: stopped.")
finally:
    broker.close()
