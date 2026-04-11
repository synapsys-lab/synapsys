---
id: plant-agent
title: PlantAgent
sidebar_position: 2
---

# PlantAgent

`PlantAgent` simulates a **discrete plant** (`StateSpace` with `dt > 0`) in real time, publishing `y` and consuming `u` on every tick.

## Requirements

- The plant must be discrete. Use `c2d()` to discretise a continuous plant.
- The transport must have two channels: one for `y` (output) and one for `u` (input).

## Complete example

```python
import numpy as np
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

# 1. Define and discretise the plant
plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])   # G(s) = 1/(s+1)
plant_d = c2d(plant_c, dt=0.01)                      # ZOH, 100 Hz

# 2. Create the shared-memory bus
BUS = "my_simulation"
CHANNELS = {"y": 1, "u": 1}

owner = SharedMemoryTransport(BUS, CHANNELS, create=True)
owner.write("u", np.array([0.0]))
owner.write("y", np.array([0.0]))

# 3. Each agent gets its own handle (as if in separate processes)
t_plant = SharedMemoryTransport(BUS, CHANNELS)

sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
agent = PlantAgent("plant", plant_d, t_plant, sync)

# 4. Start in background
agent.start(blocking=False)

# ... controller running in another thread/process ...

agent.stop()
t_plant.close()
owner.close()
```

## Initial state

```python
x0 = np.array([2.0])    # non-zero initial state
agent = PlantAgent("plant", plant_d, transport, sync, x0=x0)
```

## API Reference

See the full reference at [synapsys.agents — PlantAgent](../../api/agents#synapsysagentsplant_agentplantagent).
