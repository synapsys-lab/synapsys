---
id: plant-agent
title: PlantAgent
sidebar_position: 2
---

# PlantAgent

`PlantAgent` simulates a **discrete plant** (`StateSpace` with `dt > 0`) in real time, publishing `y` and consuming `u` on every tick.

## Requirements

- The plant must be discrete. Use `c2d()` to discretise a continuous plant.
- A `MessageBroker` must have two declared topics: one for `y` (output) and one for `u` (input).

## Complete example

```python
import numpy as np
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend

# 1. Define and discretise the plant
plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])   # G(s) = 1/(s+1)
plant_d = c2d(plant_c, dt=0.01)                      # ZOH, 100 Hz

# 2. Declare topics and build broker
topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend("my_simulation", [topic_y, topic_u], create=True))

broker.publish("plant/y", np.zeros(1))
broker.publish("plant/u", np.zeros(1))

# 3. Wire agent — transport=None, broker= kwarg
sync  = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
agent = PlantAgent(
    "plant", plant_d, None, sync,
    channel_y="plant/y", channel_u="plant/u",
    broker=broker,
)

# 4. Start in background
agent.start(blocking=False)

# ... controller running in another thread/process ...

agent.stop()
broker.close()
```

## Initial state

```python
x0 = np.array([2.0])    # non-zero initial state
agent = PlantAgent(
    "plant", plant_d, None, sync,
    channel_y="plant/y", channel_u="plant/u",
    x0=x0, broker=broker,
)
```

## API Reference

See the full reference at [synapsys.agents — PlantAgent](../../api/agents#plantagent).
