---
id: custom-controller
title: Connecting Your Controller
sidebar_label: Custom Controller
sidebar_position: 3
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Connecting Your Controller

Any Python callable can be used as a controller in the 3D views.
Simply pass your function to the `controller=` parameter:

```python
CartPoleView(controller=my_function).run()
```

---

## Expected signature

```python
controller(x: np.ndarray) -> np.ndarray | float
```

| Argument | Type | Description |
|---|---|---|
| `x` | `np.ndarray` shape `(n,)` | full state vector at the current time step |
| return | `np.ndarray` shape `(m,)` or `float` | control action (converted to array internally) |

The controller is called every `dt` seconds on the **UI thread**.
For heavy models (> 5 ms inference time), see the [Thread-safety](#thread-safety) section.

:::tip
When `controller=None` (default), the lib automatically designs an LQR
via `sim.linearize()` + `lqr(Q, R)`. A custom controller **replaces** the LQR.
Interactive perturbations from the buttons are added **after** your controller's return value.
:::

---

## Examples

<Tabs>
  <TabItem value="lqr" label="Manual LQR">

Design the LQR outside the lib and pass the gain K as a controller:

```python
import numpy as np
from synapsys.viz import CartPoleView
from synapsys.simulators import CartPoleSim
from synapsys.algorithms.lqr import lqr

# 1. Get the linearized model
sim = CartPoleSim(m_c=1.0, m_p=0.1, l=0.5)
sim.reset()
ss = sim.linearize(np.zeros(4), np.zeros(1))

# 2. Design LQR with custom weights
Q = np.diag([5.0, 0.1, 500.0, 50.0])  # penalize angle more
R = 0.001 * np.eye(1)                  # allow larger forces
K, _ = lqr(ss.A, ss.B, Q, R)

# 3. Pass to the view
CartPoleView(
    controller=lambda x: np.clip(-K @ x, -100, 100)
).run()
```

  </TabItem>
  <TabItem value="pid" label="PID">

A PID controller for the pendulum (controls only the angle θ):

```python
import numpy as np
from synapsys.viz import PendulumView
from synapsys.algorithms.pid import PID

pid = PID(kp=80.0, ki=5.0, kd=8.0, dt=0.01,
          u_min=-30.0, u_max=30.0)

def pid_ctrl(x: np.ndarray) -> np.ndarray:
    theta = x[0]            # angle (rad)
    tau = pid.compute(setpoint=0.0, measurement=theta)
    return np.array([tau])

PendulumView(controller=pid_ctrl).run()
```

  </TabItem>
  <TabItem value="pytorch" label="PyTorch">

A neural policy trained with PyTorch:

```python
import numpy as np
import torch
from synapsys.viz import CartPoleView

# Load pre-trained model
model = torch.load("cartpole_policy.pt", map_location="cpu")
model.eval()

def neural_ctrl(x: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        t = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
        u = model(t).squeeze(0).numpy()
    return np.clip(u, -80, 80)

CartPoleView(controller=neural_ctrl).run()
```

> **Tip:** if the model was trained with state normalization,
> apply the same scaler before passing `x` to the model.

  </TabItem>
  <TabItem value="sb3" label="Stable-Baselines3 (RL)">

An RL agent trained with Stable-Baselines3:

```python
import numpy as np
from stable_baselines3 import SAC
from synapsys.viz import CartPoleView

agent = SAC.load("cartpole_sac_trained")

def rl_ctrl(x: np.ndarray) -> np.ndarray:
    action, _ = agent.predict(x, deterministic=True)
    return action

CartPoleView(controller=rl_ctrl).run()
```

  </TabItem>
  <TabItem value="residual" label="Neural-LQR residual">

Residual architecture: LQR guarantees stability, the network learns the residual.
Same architecture as the Quadcopter MIMO example in the lib:

```python
import numpy as np
import torch
import torch.nn as nn
from synapsys.viz import PendulumView
from synapsys.simulators import InvertedPendulumSim
from synapsys.algorithms.lqr import lqr

# Base LQR
sim = InvertedPendulumSim()
sim.reset()
ss = sim.linearize(np.zeros(2), np.zeros(1))
K, _ = lqr(ss.A, ss.B, np.diag([80, 5]), np.eye(1))

# Residual network (initialized to zero → behavior = pure LQR)
class ResidualMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(),
            nn.Linear(32, 1),
        )
        # Initialize last layer to zero
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

mlp = ResidualMLP().eval()

def residual_lqr(x: np.ndarray) -> np.ndarray:
    u_lqr = float((-K @ x).ravel()[0])
    with torch.no_grad():
        t = torch.tensor(x, dtype=torch.float32)
        delta_u = mlp(t).item()
    return np.array([np.clip(u_lqr + delta_u, -30, 30)])

PendulumView(controller=residual_lqr).run()
```

  </TabItem>
</Tabs>

---

## Thread-safety

The controller runs on the **main UI thread** (same thread as Qt).
This means:

- **Fast models (< 2 ms):** no problem, use directly.
- **Medium models (2–10 ms):** animation will be slightly slow but functional.
- **Slow models (> 10 ms):** the UI will freeze. Use a separate thread with a queue:

```python
import threading
import queue
import numpy as np
from synapsys.viz import CartPoleView

# Queue for inter-thread communication
action_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=1)
state_queue:  queue.Queue[np.ndarray] = queue.Queue(maxsize=1)

def slow_model_thread():
    while True:
        x = state_queue.get()
        u = my_slow_model(x)          # may take time
        try:
            action_queue.put_nowait(u)
        except queue.Full:
            pass

last_u = np.zeros(1)

def controller(x: np.ndarray) -> np.ndarray:
    global last_u
    try:
        state_queue.put_nowait(x)
        last_u = action_queue.get_nowait()
    except (queue.Full, queue.Empty):
        pass
    return last_u

threading.Thread(target=slow_model_thread, daemon=True).start()
CartPoleView(controller=controller).run()
```

---

## Verifying the controller before running

Before passing a controller to the view, you can test it directly
with the simulator:

```python
import numpy as np
from synapsys.simulators import CartPoleSim

sim = CartPoleSim()
sim.reset(x0=np.array([0, 0, 0.2, 0]))

x = sim.state
u = my_controller(x)
print("u =", u, "shape =", np.asarray(u).shape)   # should be (1,)

y, info = sim.step(np.asarray(u).ravel(), dt=0.02)
print("next state:", info["x"])
```
