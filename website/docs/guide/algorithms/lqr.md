---
id: lqr
title: LQR — Linear Quadratic Regulator
sidebar_position: 2
---

# LQR — Linear Quadratic Regulator

LQR finds the state-feedback gain $K$ that minimises the quadratic cost:

$$J = \int_0^\infty \left( x^\top Q x + u^\top R u \right) dt$$

The solution is $u = -Kx$, where $K = R^{-1} B^\top P$ and $P$ is the solution to the **Algebraic Riccati Equation (ARE)**.

## Usage

```python
import numpy as np
from synapsys.algorithms import lqr
from synapsys.api import ss

# Simplified inverted pendulum
A = np.array([[0, 1], [10, 0]])
B = np.array([[0], [1]])

Q = np.diag([10.0, 1.0])   # penalise position more than velocity
R = np.array([[0.1]])       # penalise control effort

K, P = lqr(A, B, Q, R)
print(f"Gain K: {K}")       # e.g. [[-29.14, -7.61]]

# Verify closed-loop stability
A_cl = A - B @ K
sys_cl = ss(A_cl, B, np.eye(2), np.zeros((2, 1)))
print(f"Stable: {sys_cl.is_stable()}")   # True
```

## Tuning Q and R

| Goal | Adjustment |
|------|-----------|
| Faster response | Increase $Q$ (penalise state error more) |
| Less actuator effort | Increase $R$ |
| Prioritise one state | Increase the corresponding diagonal element of $Q$ |

:::tip[Bryson's rule]
A classical starting point: $Q_{ii} = 1 / x_{i,max}^2$ and $R_{jj} = 1 / u_{j,max}^2$
:::

## API Reference

See the full reference at [synapsys.algorithms — lqr](../../api/algorithms#synapsysalgorithmslqrlqr).
