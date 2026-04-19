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
| `tf(num, den, dt=0)` | `tf(num, den)` | Create a `TransferFunction` |
| `ss(A, B, C, D, dt=0)` | `ss(A, B, C, D)` | Create a `StateSpace` |
| `c2d(sys, dt, method='zoh')` | `c2d(sys, dt)` | Discretise a continuous system |
| `step(sys, T=None)` | `step(sys)` | Step response — returns `(t, y)` |
| `bode(sys, w=None)` | `bode(sys)` | Returns `(omega [rad/s], mag [dB], phase [deg])` |
| `feedback(G, H=None)` | `feedback(G, H)` | Closed-loop $T = G/(1+GH)$ with negative feedback |

### `c2d` discretisation methods

| `method` | Description |
|----------|-------------|
| `'zoh'` | Zero-Order Hold (default) — exact for piecewise-constant inputs |
| `'bilinear'` | Tustin / trapezoidal approximation |
| `'euler'` | Forward Euler (explicit) — fast but conditionally stable |
| `'backward_diff'` | Backward Euler (implicit) — unconditionally stable |

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

See [`synapsys/api/matlab_compat.py`](https://github.com/synapsys-lab/synapsys/blob/main/synapsys/api/matlab_compat.py) on GitHub.
