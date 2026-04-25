---
id: simulators-inverted-pendulum
title: Inverted Pendulum Simulator
sidebar_label: Inverted Pendulum
sidebar_position: 3
---

# Inverted Pendulum Simulator

`InvertedPendulumSim` implements a nonlinear inverted pendulum on a fixed pivot —
the simplest inherently unstable system and a classic benchmark for control design.

---

## Physics model

**States:** `x = [θ, θ̇]`
- `θ` — angle from upright (rad, θ=0 → balanced)
- `θ̇` — angular velocity (rad/s)

**Input:** `u = [τ]` — torque at pivot (N·m)

**Output:** `y = [θ]` — pole angle only

**Nonlinear dynamics:**

```
I = m · l²
θ̈ = (g/l) · sin(θ) − (b/I) · θ̇ + τ/I
```

**Unstable pole** (b=0): `λ_unstable = +√(g/l)`

---

## Construction

```python
from synapsys.simulators import InvertedPendulumSim

sim = InvertedPendulumSim(
    m=1.0,              # pendulum mass (kg)
    l=1.0,              # pendulum length (m)
    g=9.81,             # gravity (m/s²)
    b=0.0,              # friction coefficient (N·m·s/rad)
    integrator="rk4",
    noise_std=0.0,
    disturbance_std=0.0,
)
```

---

## LQR stabilisation

```python
import numpy as np
from synapsys.algorithms.lqr import lqr

sim = InvertedPendulumSim(m=1.0, l=1.0, g=9.81, b=0.1)
sim.reset()
ss = sim.linearize(np.zeros(2), np.zeros(1))

K, _ = lqr(ss.A, ss.B, np.diag([10.0, 1.0]), np.eye(1))

sim.reset(x0=np.array([0.1, 0.0]))
for _ in range(1000):
    x = sim.state
    u = -K @ x
    y, info = sim.step(u, dt=0.01)
    if info["failed"]:
        break
```

---

## Failure detection

`info["failed"]` is `True` when `|θ| > π/2 rad` (pole has fallen past horizontal).

---

## Utilities

```python
# Unstable open-loop pole (theoretical)
sim.unstable_pole()   # ≈ √(g/l)

# Thread-safe parameter update
sim.set_params(b=0.5)   # accepted: m, l, g, b
```
