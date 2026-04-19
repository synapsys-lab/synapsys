---
id: controller-agent
title: ControllerAgent
sidebar_position: 3
---

# ControllerAgent

`ControllerAgent` aplica uma **lei de controle** em tempo real. Ele le `y` do transporte, chama `control_law(y)` e escreve `u` de volta.

A lei de controle e um `Callable[[np.ndarray], np.ndarray]` — qualquer callable Python, incluindo PID, LQR ou um modelo de IA.

## Exemplos

### Com PID

```python
import numpy as np
from synapsys.algorithms import PID
from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

pid = PID(Kp=3.0, Ki=0.5, dt=0.025, u_min=-10.0, u_max=10.0)
setpoint = 5.0

law = lambda y: np.array([pid.compute(setpoint=setpoint, measurement=y[0])])

transport = SharedMemoryTransport("minha_simulacao", {"y": 1, "u": 1})
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.025)

ctrl = ControllerAgent("controlador", law, transport, sync)
ctrl.start(blocking=False)
```

### Com LQR

```python
import numpy as np
from synapsys.algorithms import lqr

K, _ = lqr(A, B, Q, R)

# LQR: u = -K @ x  (aqui y e o estado completo)
law = lambda y: -(K @ y.reshape(-1, 1)).flatten()

ctrl = ControllerAgent("lqr_ctrl", law, transport, sync)
```

### Com qualquer callable

```python
def bang_bang(y: np.ndarray) -> np.ndarray:
    return np.array([10.0 if y[0] < setpoint else -10.0])

ctrl = ControllerAgent("bang_bang", bang_bang, transport, sync)
```

## Referência da API

Consulte a referência completa em [synapsys.agents — ControllerAgent](/docs/api/agents).
