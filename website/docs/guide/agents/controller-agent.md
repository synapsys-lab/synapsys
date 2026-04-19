---
id: controller-agent
title: ControllerAgent
sidebar_position: 3
---

# ControllerAgent

`ControllerAgent` applies a **control law** in real time. It reads `y` from the broker, calls `control_law(y)`, and publishes `u` back.

The control law is a `Callable[[np.ndarray], np.ndarray]` — any Python callable, including PID, LQR, or an AI model.

## Examples

### With PID

```python
import numpy as np
from synapsys.algorithms import PID
from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend

pid = PID(Kp=3.0, Ki=0.5, dt=0.025, u_min=-10.0, u_max=10.0)
setpoint = 5.0

law = lambda y: np.array([pid.compute(setpoint=setpoint, measurement=y[0])])

# Broker must already be declared (e.g. by PlantAgent process)
topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend("my_simulation", [topic_y, topic_u], create=False))

sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.025)
ctrl = ControllerAgent(
    "controller", law, None, sync,
    channel_y="plant/y", channel_u="plant/u",
    broker=broker,
)
ctrl.start(blocking=False)
```

### With LQR

```python
import numpy as np
from synapsys.algorithms import lqr

K, _ = lqr(A, B, Q, R)

# LQR: u = -K @ x  (here y is the full state)
law = lambda y: -(K @ y.reshape(-1, 1)).flatten()

ctrl = ControllerAgent(
    "lqr_ctrl", law, None, sync,
    channel_y="plant/y", channel_u="plant/u",
    broker=broker,
)
```

### With any callable

```python
# Simple bang-bang control
def bang_bang(y: np.ndarray) -> np.ndarray:
    return np.array([10.0 if y[0] < setpoint else -10.0])

ctrl = ControllerAgent(
    "bang_bang", bang_bang, None, sync,
    channel_y="plant/y", channel_u="plant/u",
    broker=broker,
)
```

## API Reference

See the full reference at [synapsys.agents — ControllerAgent](../../api/agents#controlleragent).
