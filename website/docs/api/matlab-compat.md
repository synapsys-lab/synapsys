---
id: matlab-compat
title: synapsys.api — MATLAB-Compatible Layer
sidebar_position: 1
---

# synapsys.api — MATLAB-Compatible Layer

High-level functions that mirror MATLAB syntax, delegating to the core classes.

:::note
This module is the recommended entry point for most users.
:::

## Functions

| Function | MATLAB equivalent | Description |
|----------|------------------|-------------|
| `tf(num, den, dt=0)` | `tf(num, den)` | Create a TransferFunction |
| `ss(A, B, C, D, dt=0)` | `ss(A, B, C, D)` | Create a StateSpace |
| `c2d(sys, dt, method='zoh')` | `c2d(sys, dt)` | Discretise a continuous system |
| `step(sys, T=None)` | `step(sys)` | Step response |
| `bode(sys, w=None)` | `bode(sys)` | Bode diagram data |
| `feedback(G, H=None, sign=-1)` | `feedback(G, H)` | Closed-loop system |

## Example

```python
from synapsys.api import tf, c2d, step, bode, feedback

G = tf([1], [1, 2, 1])          # G(s) = 1/(s+1)^2
T = feedback(G)                  # closed-loop
Gd = c2d(G, dt=0.05)            # ZOH discretisation

t, y = step(T)                   # step response
w, mag, phase = bode(G)          # Bode data
```

## Source

See [`synapsys/api/matlab_compat.py`](https://github.com/synapsys/synapsys/blob/main/synapsys/api/matlab_compat.py) on GitHub.
