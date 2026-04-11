---
id: state-space
title: State Space
sidebar_position: 2
---

# State Space

`StateSpace` represents an LTI system via the $(A, B, C, D)$ matrices.

**Continuous:**

$$\dot{x} = Ax + Bu \qquad y = Cx + Du$$

**Discrete:**

$$x(k+1) = Ax(k) + Bu(k) \qquad y(k) = Cx(k) + Du(k)$$

## Creating a system

```python
from synapsys.api import ss
import numpy as np

A = np.array([[ 0,  1],
              [-2, -3]])
B = np.array([[0], [1]])
C = np.array([[1, 0]])
D = np.array([[0]])

sys = ss(A, B, C, D)

# Discrete with dt = 10 ms
sys_d = ss(A, B, C, D, dt=0.01)
```

## Analysis

```python
sys.poles()        # eigenvalues of A
sys.zeros()        # transmission zeros
sys.is_stable()    # Re(poles) < 0  (continuous) | |poles| < 1 (discrete)

sys.n_states   # 2
sys.n_inputs   # 1
sys.n_outputs  # 1
```

## Batch simulation

```python
t, y = sys.step()               # step response
t, y = sys_d.step(n=300)        # discrete — 300 samples

t = np.linspace(0, 5, 500)
u = np.sin(2 * np.pi * t)
t, y = sys.simulate(t, u)       # arbitrary input response
```

## Step-by-step simulation (agents)

For real-time simulation inside a `PlantAgent`, use `evolve()`. It has no side-effects — the caller stores the state.

```python
x = np.zeros(sys_d.n_states)

for k in range(100):
    u = controller.compute(y)
    x, y = sys_d.evolve(x, u)   # x(k+1), y(k)
```

:::warning[Discrete only]
`evolve()` requires `is_discrete == True`. Discretise with `c2d()` first.
:::

## Conversions

```python
tf = sys.to_transfer_function()   # StateSpace -> TransferFunction
ss2 = tf.to_state_space()         # TransferFunction -> StateSpace
```

## API Reference

See the full reference at [synapsys.core — StateSpace](../../api/core#synapsyscorestate_spacestateSpace).
