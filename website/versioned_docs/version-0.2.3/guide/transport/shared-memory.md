---
id: shared-memory
title: Shared Memory Transport
sidebar_position: 2
---

# Shared Memory Transport

`SharedMemoryBackend` (via `SharedMemoryTransport` underneath) uses the **OS shared-memory mechanism** (`multiprocessing.shared_memory`) for **zero-copy** communication between processes on the same machine.

Data is written directly to physical RAM addresses mapped as NumPy arrays. No serialisation, no copying, no kernel bypass — just a pointer to the same address.

## How it works

```
Process A (plant)             Physical RAM              Process B (controller)
─────────────────────    ┌──────────────────────┐    ──────────────────────────
broker.publish(...)  ───▶│  [y0, y1, ..., u0]  │◀──── broker.read(...)
                          └──────────────────────┘
                               "ctrl_bus" (OS name)
```

## Usage with MessageBroker

```python
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend
import numpy as np

topic_y = Topic("plant/y", shape=(2,))   # plant output — 2 floats
topic_u = Topic("plant/u", shape=(1,))   # control signal — 1 float

# Owner process: creates the block (create=True)
broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend("ctrl_bus", [topic_y, topic_u], create=True))

broker.publish("plant/y", np.zeros(2))
broker.publish("plant/u", np.zeros(1))

# Other processes: connect by name (create=False)
broker2 = MessageBroker()
broker2.declare_topic(topic_y)
broker2.declare_topic(topic_u)
broker2.add_backend(SharedMemoryBackend("ctrl_bus", [topic_y, topic_u], create=False))

y = broker2.read("plant/y")
```

:::warning[Owner is responsible for unlink]
Only the `create=True` process releases memory in the OS on close.
Client processes call only `broker.close()`.
:::

## Multiple agents on the same block

With `MessageBroker`, a single broker instance is shared by all agents in the same process — no need for multiple transport handles:

```python
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode

topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend("ctrl_bus", [topic_y, topic_u], create=True))

broker.publish("plant/y", np.zeros(1))
broker.publish("plant/u", np.zeros(1))

plant_agent = PlantAgent(
    "plant", plant_d, None, SyncEngine(SyncMode.WALL_CLOCK, dt=0.01),
    channel_y="plant/y", channel_u="plant/u", broker=broker,
)
ctrl_agent = ControllerAgent(
    "ctrl", law, None, SyncEngine(SyncMode.WALL_CLOCK, dt=0.01),
    channel_y="plant/y", channel_u="plant/u", broker=broker,
)
```

:::danger[Race conditions]
There is no mutex in the current implementation. Architect your topics so that each agent is the sole writer of its topic.
:::

## API Reference

See the full reference at [synapsys.transport — SharedMemoryTransport](../../api/transport#sharedmemorytransport).
