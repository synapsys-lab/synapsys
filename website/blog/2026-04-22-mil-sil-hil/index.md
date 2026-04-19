---
slug: mil-sil-hil-control-deployment
title: "From Model to Hardware: MIL → SIL → HIL in Three Steps"
description: >
  A practical guide to the MIL/SIL/HIL development workflow with Synapsys —
  swap from simulation to real hardware by changing one line, keeping your
  control algorithm untouched.
authors: [oseias]
tags: [tutorial, sil, hil, simulation, python, control-theory]
hide_table_of_contents: false
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<div align="center">

![SIL Neural-LQR](https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/examples/03_sil_ai_controller.gif)

</div>

**MIL → SIL → HIL** is the standard V-model progression for embedded control:
simulate everything first, then replace the plant model with real hardware one
layer at a time. In most frameworks this requires rewriting large parts of the
control loop. In Synapsys the transition is a **one-line swap** because the
transport layer is fully abstracted from the algorithm.

{/* truncate */}

## The three stages

| Stage | Plant | Controller | Transport | Purpose |
|-------|-------|------------|-----------|---------|
| **MIL** — Model-in-the-Loop | Simulated (`StateSpace`) | Algorithm code | Shared memory | Rapid iteration, unit tests |
| **SIL** — Software-in-the-Loop | Simulated | Compiled binary / external process | ZeroMQ | Integration tests, latency profiling |
| **HIL** — Hardware-in-the-Loop | Real device | Algorithm code or MCU firmware | `HardwareInterface` | Acceptance testing on real plant |

The Synapsys abstraction that makes this work:

```
Agent ──► TransportStrategy (read / write)
              │
              ├── SharedMemoryTransport   ← MIL
              ├── ZMQTransport            ← SIL
              └── HardwareInterface       ← HIL
```

The `Agent` never calls transport directly — it calls `_read()` / `_write()`.
Swap the transport, leave the agent unchanged.

---

## Stage 1 — MIL: everything in one process

```python
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import SharedMemoryTransport
import numpy as np

plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

pid = PID(Kp=4.0, Ki=1.0, dt=0.01)

def law(y: np.ndarray) -> np.ndarray:
    return np.array([pid.compute(setpoint=3.0, measurement=y[0])])

with SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True) as bus:
    bus.write("y", np.zeros(1))
    bus.write("u", np.zeros(1))
    sync = SyncEngine(SyncMode.LOCK_STEP, dt=0.01)
    PlantAgent("plant", plant_d, bus, sync).start(blocking=False)
    ControllerAgent("ctrl", law, bus, sync).start(blocking=True)
```

All in one script. Fast, deterministic, easy to unit-test.

---

## Stage 2 — SIL: two processes over ZeroMQ

Split plant and controller into separate processes. The controller algorithm
**does not change at all**:

<Tabs>
<TabItem value="plant" label="plant_process.py">

```python
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.transport import ZMQTransport

plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

pub = ZMQTransport("tcp://*:5555",      mode="pub")   # publish y
sub = ZMQTransport("tcp://localhost:5556", mode="sub") # subscribe u

# ZMQTransport wraps both sockets in a single bus-like interface
# (see ZMQReqRepTransport for request-reply pattern)
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
PlantAgent("plant", plant_d, pub, sync, sub_transport=sub).start(blocking=True)
```

</TabItem>
<TabItem value="ctrl" label="controller_process.py">

```python
from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import ZMQTransport
import numpy as np

pid = PID(Kp=4.0, Ki=1.0, dt=0.01)

def law(y: np.ndarray) -> np.ndarray:
    return np.array([pid.compute(setpoint=3.0, measurement=y[0])])

sub = ZMQTransport("tcp://localhost:5555", mode="sub")  # subscribe y
pub = ZMQTransport("tcp://*:5556",         mode="pub")  # publish u

sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
ControllerAgent("ctrl", law, sub, sync, pub_transport=pub).start(blocking=True)
```

</TabItem>
</Tabs>

The `law` function is **identical** to the MIL version. Only the transport changed.

---

## Stage 3 — HIL: real hardware

Replace the `StateSpace` plant with a `HardwareInterface` implementation for your
device. Everything else — the PID, the sync engine, the ZMQ transport — stays:

```python
from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
from synapsys.hw import HardwareInterface
from synapsys.transport import ZMQTransport
import numpy as np

class MyDAQInterface(HardwareInterface):
    """Wrapper around a USB DAQ card (e.g. NI-DAQ, Arduino, STM32)."""

    def __init__(self):
        super().__init__(n_inputs=1, n_outputs=1)
        # self.daq = ...  initialise your hardware SDK here

    def read_outputs(self, timeout_ms: float = 100.0) -> np.ndarray:
        # return np.array([self.daq.read_channel(0)])
        return np.array([0.0])   # stub

    def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
        # self.daq.write_channel(0, float(u[0]))
        pass


# Drop-in replacement: HardwareAgent instead of PlantAgent
sub = ZMQTransport("tcp://localhost:5556", mode="sub")
pub = ZMQTransport("tcp://*:5555",         mode="pub")
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)

HardwareAgent("hw", MyDAQInterface(), pub, sync, sub_transport=sub).start(blocking=True)
```

The controller process **does not change**. The swap is surgical.

---

## Common pitfalls

### Timing jitter in SIL

`WALL_CLOCK` sync relies on `time.sleep()` precision. On Linux with a standard
kernel, expect ±0.5 ms jitter at 100 Hz. For tighter requirements:

```python
# Use LOCK_STEP for in-process simulation (no timing issues)
sync = SyncEngine(SyncMode.LOCK_STEP, dt=0.01)

# Use WALL_CLOCK for cross-process / HIL
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
```

### Initial condition mismatch

Always initialise shared channels **before** starting agents:

```python
bus.write("y", np.zeros(1))   # ← do this
bus.write("u", np.zeros(1))   # ← do this
PlantAgent(...).start(blocking=False)
ControllerAgent(...).start(blocking=True)
```

A controller that reads before the first plant write will get stale zeros — fine
for ZOH semantics, but worth being explicit.

---

## Summary

The MIL → SIL → HIL transition with Synapsys is:

1. **MIL**: `SharedMemoryTransport` + `PlantAgent` + `ControllerAgent`
2. **SIL**: swap to `ZMQTransport`, split into two processes
3. **HIL**: swap `PlantAgent` for `HardwareAgent(MyDAQInterface(), ...)`

The control **algorithm never changes**. The `law` function you wrote on day one
runs unchanged on the real hardware.

See the full SIL example at
[`examples/advanced/02_sil_ai_controller/`](https://github.com/synapsys-lab/synapsys/tree/main/examples/advanced/02_sil_ai_controller).
