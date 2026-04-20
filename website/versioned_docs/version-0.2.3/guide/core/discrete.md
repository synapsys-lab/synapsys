---
id: discrete
title: Discrete-Time Systems
sidebar_position: 3
---

# Discrete-Time Systems

Continuous-time systems must be discretised before running in digital control loops or Synapsys agents.

## c2d — Continuous to Discrete

```python
from synapsys.api import tf, ss, c2d

G_c = tf([1], [1, 1])          # G(s) = 1/(s+1)
G_d = c2d(G_c, dt=0.1)         # ZOH, Ts = 100 ms
```

### Available methods

| `method` | Description | When to use |
|----------|-------------|-------------|
| `'zoh'` (default) | Zero-Order Hold | Classical digital control |
| `'bilinear'` | Tustin / bilinear | Filters, preserves frequency response |
| `'euler'` | Euler forward | Fast prototyping, small Ts |
| `'backward_diff'` | Euler backward | Systems with integrators |

```python
G_bilinear = c2d(G_c, dt=0.1, method='bilinear')
G_euler    = c2d(G_c, dt=0.01, method='euler')
```

## Verifying discrete stability

```python
G_d = c2d(tf([1], [1, 1]), dt=0.1)

G_d.is_discrete    # True
G_d.poles()        # array([0.9048])  — inside the unit circle
G_d.is_stable()    # True  (|pole| < 1)
```

## Nyquist rule

:::tip[Minimum sampling frequency]
Nyquist's theorem requires $f_s \geq 2 f_{max}$.
In practice, for control use $f_s \geq 10 \times$ the system bandwidth.
:::

```python
import numpy as np
G = tf([100], [1, 20, 100])  # wn = 10 rad/s

w, mag, _ = G.bode()
bw_idx = np.argmax(mag < mag[0] - 3)
omega_bw = w[bw_idx]

dt_recommended = (2 * np.pi) / (10 * omega_bw)
print(f"Recommended dt: {dt_recommended*1000:.1f} ms")
```

## Continuous vs discrete comparison

```python
import matplotlib.pyplot as plt
from synapsys.api import tf, c2d, step

G_c = tf([1], [1, 2, 1])
fig, ax = plt.subplots()

t, y = G_c.step()
ax.plot(t, y, label='Continuous')

for dt in [0.5, 0.2, 0.05]:
    G_d = c2d(G_c, dt=dt)
    t_d, y_d = G_d.step(n=int(5/dt))
    ax.step(t_d, y_d, where='post', label=f'ZOH Ts={dt}s')

ax.legend()
ax.grid(True)
plt.show()
```
