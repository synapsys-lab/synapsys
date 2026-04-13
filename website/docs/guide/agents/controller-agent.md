---
id: controller-agent
title: ControllerAgent
sidebar_position: 3
---

# ControllerAgent

`ControllerAgent` applies a **control law** in real time. It reads `y` from the transport, calls `control_law(y)`, and writes `u` back.

The control law is a `Callable[[np.ndarray], np.ndarray]` — any Python callable, including PID, LQR, or an AI model.

## Examples

### With PID

```python
import numpy as np
from synapsys.algorithms import PID
from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

pid = PID(Kp=3.0, Ki=0.5, dt=0.025, u_min=-10.0, u_max=10.0)
setpoint = 5.0

# Lambda adapting PID signature to the agent contract
law = lambda y: np.array([pid.compute(setpoint=setpoint, measurement=y[0])])

transport = SharedMemoryTransport("my_simulation", {"y": 1, "u": 1})
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.025)

ctrl = ControllerAgent("controller", law, transport, sync)
ctrl.start(blocking=False)
```

### With LQR

```python
import numpy as np
from synapsys.algorithms import lqr

K, _ = lqr(A, B, Q, R)

# LQR: u = -K @ x  (here y is the full state)
law = lambda y: -(K @ y.reshape(-1, 1)).flatten()

ctrl = ControllerAgent("lqr_ctrl", law, transport, sync)
```

### With any callable

```python
# Simple bang-bang control
def bang_bang(y: np.ndarray) -> np.ndarray:
    return np.array([10.0 if y[0] < setpoint else -10.0])

ctrl = ControllerAgent("bang_bang", bang_bang, transport, sync)
```

## API Reference

See the full reference at [synapsys.agents — ControllerAgent](../../api/agents#controlleragent).
