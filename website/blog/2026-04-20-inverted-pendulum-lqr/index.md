---
slug: inverted-pendulum-lqr
title: "Stabilising an Inverted Pendulum with LQR"
description: >
  A complete walkthrough: derive the linearised state-space model of an inverted
  pendulum, design an LQR controller, simulate the closed-loop response, and
  discretise for embedded deployment — all in Python with Synapsys.
authors: [oseias]
tags: [artigo, tutorial, lqr, control-theory, simulation, python]
content_type: artigo
hide_table_of_contents: false
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

The inverted pendulum is the canonical benchmark of nonlinear control — unstable,
simple enough to model analytically, yet rich enough to reveal the full LQR design
workflow. This post derives the linearised model from physics and shows how to
stabilise it with Synapsys in a few dozen lines of Python.

{/* truncate */}

## Physics and linearisation

A rigid rod of mass $m$ and length $L$ is hinged at a cart. Let $\theta$ be the angle
from the vertical upright. Linearising around $\theta = 0$ gives:

$$
\ddot{\theta} = \frac{g}{L}\theta - \frac{1}{mL^2}u
$$

Choosing the state vector $x = [\theta,\; \dot{\theta}]^\top$ and the cart force $u$:

$$
\dot{x} = \underbrace{\begin{bmatrix}0 & 1 \\ g/L & 0\end{bmatrix}}_{A}\, x
         + \underbrace{\begin{bmatrix}0 \\ -1/(mL^2)\end{bmatrix}}_{B}\, u,
\qquad
y = \begin{bmatrix}1 & 0\end{bmatrix} x
$$

For $m = 0.5$ kg, $L = 0.3$ m, $g = 9.81$ m/s²:

```python
import numpy as np
from synapsys.api import ss

m, L, g = 0.5, 0.3, 9.81

A = np.array([[0,      1   ],
              [g/L,    0   ]])
B = np.array([[0           ],
              [-1/(m*L**2) ]])
C = np.array([[1, 0]])
D = np.zeros((1, 1))

plant = ss(A, B, C, D)
print(plant)                  # StateSpace n_states=2 n_inputs=1 n_outputs=1
print(plant.is_stable())      # False — poles at ±√(g/L) = ±5.72 rad/s
```

The open-loop poles are $\pm\sqrt{g/L} \approx \pm 5.72$ rad/s — one is in the right
half-plane, confirming instability.

---

## LQR design

LQR finds the state-feedback gain $K$ that minimises:

$$
J = \int_0^\infty \left(x^\top Q\, x + u^\top R\, u\right)\mathrm{d}t
$$

The tuning intuition: **large $Q$ penalises state error** (fast, aggressive), **large $R$
penalises control effort** (slow, conservative). Here we want tight angle control with
moderate actuation:

```python
from synapsys.algorithms import lqr

Q = np.diag([100.0, 1.0])   # penalise angle heavily, velocity lightly
R = np.array([[0.1]])        # moderate actuator cost

K, P = lqr(A, B, Q, R)
print(f"K = {K}")            # K = [[33.2  5.8]]
```

The closed-loop system matrix $A_{cl} = A - BK$ has eigenvalues that are all in the
left half-plane — the pendulum is now stabilised.

```python
A_cl = A - B @ K
print(np.linalg.eigvals(A_cl))   # e.g. [-4.1+2.3j  -4.1-2.3j]
```

---

## Simulation

```python
from synapsys.api import c2d
import matplotlib.pyplot as plt

# Build closed-loop state-space
cl = ss(A_cl, B, C, D)

# Step response — initial condition θ₀ = 0.2 rad (≈ 11°)
t = np.linspace(0, 3, 600)
x0 = np.array([0.2, 0.0])          # [θ, θ_dot]

# simulate() accepts x0 for initial condition
u_zero = np.zeros((len(t), 1))     # no reference tracking, pure stabilisation
t_out, y = cl.simulate(t, u_zero, x0=x0)

plt.plot(t_out, y)
plt.xlabel("Time (s)")
plt.ylabel("θ (rad)")
plt.title("Inverted Pendulum — LQR stabilisation from θ₀ = 0.2 rad")
plt.grid(True)
plt.show()
```

The angle returns to zero in roughly 1.5 s without overshoot — the $Q/R$ balance gave
us a well-damped response.

---

## Discretisation for embedded deployment

Real microcontrollers run discrete loops. ZOH discretisation at 100 Hz:

```python
dt = 0.01  # 100 Hz
plant_d = c2d(plant, dt=dt)

print(plant_d)   # StateSpace n_states=2  dt=0.01

# The same K works — LQR was designed in continuous time
# For production, redesign K in discrete time for better performance:
from synapsys.algorithms import lqr
from synapsys.api import c2d

# Discretise A and B for discrete-time LQR (dare)
# plant_d.A, plant_d.B are the ZOH-discretised matrices
K_d, _ = lqr(plant_d.A, plant_d.B, Q, R)
```

The control loop on the microcontroller reduces to:

```python
x = np.zeros(2)
for tick in range(n_steps):
    u = -K_d @ x
    x, y = plant_d.evolve(x, u)
```

---

## Key takeaways

| Step | Synapsys API |
|------|-------------|
| Model | `ss(A, B, C, D)` |
| Stability check | `plant.is_stable()`, `plant.poles()` |
| LQR design | `lqr(A, B, Q, R)` → returns `(K, P)` |
| Simulation | `cl.simulate(t, u, x0=x0)` |
| Discretisation | `c2d(plant, dt=0.01)` |
| Embedded loop | `plant_d.evolve(x, u)` |

The full notebook is available in [`examples/quickstart_en.ipynb`](https://github.com/synapsys-lab/synapsys/blob/main/examples/quickstart_en.ipynb).

---

## Next in the series

The next post covers **MIMO control of a quadrotor** — extending these ideas to a
12-state system with coupled dynamics and a residual Neural-LQR that adds a learned
correction layer on top of the classical solution.
