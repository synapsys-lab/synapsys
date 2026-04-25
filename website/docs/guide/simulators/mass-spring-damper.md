---
id: simulators-msd
title: Mass-Spring-Damper Simulator
sidebar_label: Mass-Spring-Damper
sidebar_position: 2
---

# Mass-Spring-Damper Simulator

`MassSpringDamperSim` is the simplest second-order simulator — a 1-DOF linear
mass-spring-damper. It is always stable for positive parameters and serves as the
entry point for understanding `SimulatorBase`.

---

## Physics model

**States:** `x = [q, q̇]`
- `q` — displacement from rest (m)
- `q̇` — velocity (m/s)

**Input:** `u = [F]` — applied force (N)

**Output:** `y = [q]` — position only

**Dynamics:**

```
m·q̈ + c·q̇ + k·q = F
```

---

## Construction

```python
from synapsys.simulators import MassSpringDamperSim

sim = MassSpringDamperSim(
    m=1.0,              # mass (kg)
    c=0.5,              # damping coefficient (N·s/m)
    k=2.0,              # spring stiffness (N/m)
    integrator="rk4",
    noise_std=0.0,
    disturbance_std=0.0,
)
```

---

## Step response

```python
import numpy as np

sim = MassSpringDamperSim()
sim.reset()

history = []
for _ in range(300):
    y, _ = sim.step(np.array([1.0]), dt=0.05)  # constant force
    history.append(y[0])

# steady-state displacement = F / k = 1.0 / 2.0 = 0.5 m
print(f"Steady state: {history[-1]:.4f} m")
```

---

## Linearisation validation

Because MSD is already linear, `linearize()` must return the known analytical matrices:

```python
ss = sim.linearize(np.zeros(2), np.zeros(1))
# A = [[0, 1], [-k/m, -c/m]]
# B = [[0], [1/m]]
# C = [[1, 0]]
# D = [[0]]
```

---

## Thread-safe parameter updates

```python
sim.set_params(m=2.0, k=5.0)   # accepted: m, c, k
```
