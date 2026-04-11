---
id: shared-memory
title: Shared Memory Transport
sidebar_position: 2
---

# Shared Memory Transport

`SharedMemoryTransport` uses the **OS shared-memory mechanism** (`multiprocessing.shared_memory`) for **zero-copy** communication between processes on the same machine.

Data is written directly to physical RAM addresses mapped as NumPy arrays. No serialisation, no copying, no kernel bypass — just a pointer to the same address.

## How it works

```
Process A (plant)             Physical RAM              Process B (controller)
─────────────────────    ┌──────────────────────┐    ──────────────────────────
bus._buf -> array  ─────▶│  [y0, y1, ..., u0]  │◀────── bus._buf -> array
                          └──────────────────────┘
                               "ctrl_bus" (OS name)
```

## Usage

```python
from synapsys.transport import SharedMemoryTransport
import numpy as np

CHANNELS = {
    "y": 2,    # plant output — 2 floats
    "u": 1,    # control signal — 1 float
}

# Owner process: creates the block (create=True)
owner = SharedMemoryTransport("ctrl_bus", CHANNELS, create=True)
owner.write("y", np.array([0.0, 0.0]))
owner.write("u", np.array([0.0]))

# Other processes: connect by name (create=False, default)
client = SharedMemoryTransport("ctrl_bus", CHANNELS)
y = client.read("y")
```

:::warning[Owner is responsible for unlink]
Only the `create=True` process releases memory in the OS on close.
Clients call only `close()` — not `unlink()`.
:::

## Multiple agents on the same block

```python
# Each agent needs its own Python object
# (even if they point to the same RAM block)
t_plant = SharedMemoryTransport("ctrl_bus", CHANNELS)   # plant agent handle
t_ctrl  = SharedMemoryTransport("ctrl_bus", CHANNELS)   # controller agent handle

plant_agent = PlantAgent(..., transport=t_plant, ...)
ctrl_agent  = ControllerAgent(..., transport=t_ctrl, ...)
```

:::danger[Race conditions]
There is no mutex in the current implementation. If two processes write to the same channel simultaneously, corruption may occur. Architect your channels so that each process is the sole writer of its channel.
:::

## API Reference

See the full reference at [synapsys.transport — SharedMemoryTransport](../../api/transport#synapsystransportshared_memorysharedmemorytransport).
