---
id: simulators-cartpole
title: Cart-Pole Simulator
sidebar_label: Cart-Pole
sidebar_position: 4
---

# Cart-Pole Simulator

`CartPoleSim` implements the classic Lagrangian cart-pole: a cart sliding on a
frictionless track with an inverted pendulum attached at the pivot.

---

## Physics model

**States:** `x = [p, ṗ, θ, θ̇]`
- `p` — cart position (m)
- `ṗ` — cart velocity (m/s)
- `θ` — pole angle from upright (rad, θ=0 → balanced)
- `θ̇` — pole angular velocity (rad/s)

**Input:** `u = [F]` — horizontal force on cart (N)

**Output:** `y = [p, θ]` — partial observation (no velocities)

**Nonlinear dynamics (Lagrangian):**

```
Δ  = m_c + m_p · sin²(θ)
p̈  = [F + m_p · sin(θ) · (l · θ̇² − g · cos(θ))] / Δ
θ̈  = [g · sin(θ) − p̈ · cos(θ)] / l
```

---

## Construction

```python
from synapsys.simulators import CartPoleSim

sim = CartPoleSim(
    m_c=1.0,            # cart mass (kg)
    m_p=0.1,            # pole tip mass (kg)
    l=0.5,              # pole length (m)
    g=9.81,             # gravity (m/s²)
    integrator="rk4",   # "euler", "rk4", or "rk45"
    noise_std=0.0,       # sensor noise
    disturbance_std=0.0, # input disturbance
    linearised=False,    # True → use linearised dynamics
)
```

---

## Linearised mode

For small angles the nonlinear dynamics simplifies to a linear system.
Pass `linearised=True` to use this approximation:

```python
sim_nl = CartPoleSim(linearised=False)   # full nonlinear
sim_l  = CartPoleSim(linearised=True)    # linear approximation

# Near θ=0 both behave identically (atol ≈ 1e-4 for dt=0.01 s)
```

---

## LQR stabilisation

```python
import numpy as np
from synapsys.algorithms.lqr import lqr

sim = CartPoleSim()
sim.reset()
ss = sim.linearize(np.zeros(4), np.zeros(1))

Q = np.diag([1.0, 0.1, 100.0, 10.0])   # penalise angle heavily
R = np.eye(1) * 0.01
K, _ = lqr(ss.A, ss.B, Q, R)

sim.reset(x0=np.array([0.0, 0.0, 0.15, 0.0]))
for _ in range(500):
    x = sim.state
    u = np.clip(-K @ x, -50, 50)
    y, info = sim.step(u, dt=0.02)
    if info["failed"]:
        break
```

---

## 2D matplotlib animation

```python
from synapsys.viz import CartPole2DView

# Auto-LQR
CartPole2DView().run()

# Custom controller
CartPole2DView(controller=lambda x: np.clip(-K @ x, -50, 50)).run()

# Simulate only (no display)
hist = CartPole2DView(dt=0.02, duration=5.0).simulate()
print(hist["angle"][-1])   # final pole angle (rad)

# Save animation
view = CartPole2DView()
anim = view.animate(save="cartpole.gif")
```

---

## Failure detection

The simulator flags failure when the system leaves the safe region:

| Condition | Value |
|---|---|
| Cart out of bounds | `\|p\| > 4.8 m` |
| Pole fell | `\|θ\| > π/3 rad (≈ 60°)` |

```python
y, info = sim.step(u, dt)
if info["failed"]:
    print("Episode ended — resetting")
    sim.reset()
```

---

## Thread-safe parameter updates

```python
import threading

def slow_controller():
    while True:
        sim.set_params(m_c=2.0)   # safe from any thread

t = threading.Thread(target=slow_controller, daemon=True)
t.start()
```

Accepted keys: `m_c`, `m_p`, `l`, `g`.
