---
id: transfer-function
title: Transfer Function
sidebar_position: 1
---

# Transfer Function

A `TransferFunction` represents a SISO linear time-invariant system as a ratio of two polynomials.

**Continuous:** $G(s) = \dfrac{N(s)}{D(s)}$

**Discrete:** $H(z) = \dfrac{N(z)}{D(z)}$

## Creating a system

```python
from synapsys.api import tf

# G(s) = 1 / (s + 1)
G = tf([1], [1, 1])

# G(s) = s / (s^2 + 2s + 1)
G = tf([1, 0], [1, 2, 1])

# Discrete: H(z) = 0.095 / (z - 0.905)
Hd = tf([0.095], [1, -0.905], dt=0.1)
```

:::tip[Automatic input sanitisation]
Lists, tuples, and 1-D arrays are all accepted. `dt=0` (default) creates a continuous-time system.
:::

## Analysis

```python
G = tf([1], [1, 3, 2])   # G(s) = 1 / (s+1)(s+2)

G.poles()        # array([-1., -2.])
G.zeros()        # array([])
G.is_stable()    # True
G.evaluate(0)    # DC gain = 0.5
```

## Step response and Bode diagram

```python
t, y = G.step()                     # continuous
t, y = Gd.step(n=200)               # discrete — 200 samples

w, mag, phase = G.bode()            # continuous
w, mag, phase = Gd.bode()           # discrete (dbode)
```

## Block algebra

```python
G1 = tf([1], [1, 1])
G2 = tf([2], [1, 2])

G1 * G2       # series:   G1(s) * G2(s)
G1 + G2       # parallel: G1(s) + G2(s)
G1 / G2       # ratio
-G1           # sign inversion
G1.feedback() # T = G1 / (1 + G1)  — unity negative feedback
```

:::warning[Mixing domains]
Combining a continuous system with a discrete one, or two discrete systems with different `dt`, raises `ValueError`.
:::

## API Reference

See the full reference at [synapsys.core — TransferFunction](../../api/core#transferfunction).
