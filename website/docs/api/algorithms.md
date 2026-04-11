---
id: algorithms
title: synapsys.algorithms
sidebar_position: 3
---

# synapsys.algorithms

Control algorithm implementations ready for use in agents or standalone scripts.

## PID

Discrete-time PID controller with output saturation and back-calculation anti-windup.

### Constructor

```python
PID(
    Kp: float,
    Ki: float = 0.0,
    Kd: float = 0.0,
    dt: float = 0.01,
    u_min: float = -inf,
    u_max: float = inf,
)
```

| Parameter | Description |
|-----------|-------------|
| `Kp` | Proportional gain |
| `Ki` | Integral gain |
| `Kd` | Derivative gain |
| `dt` | Sample time in seconds |
| `u_min`, `u_max` | Output saturation limits |

### Methods

| Method | Description |
|--------|-------------|
| `compute(setpoint, measurement) -> float` | Computes the control signal for one timestep |
| `reset()` | Clears the integrator and previous error |

## lqr

Solves the infinite-horizon Linear Quadratic Regulator problem.

```python
lqr(A, B, Q, R) -> tuple[np.ndarray, np.ndarray]
```

| Parameter | Description |
|-----------|-------------|
| `A` | System matrix $(n \times n)$ |
| `B` | Input matrix $(n \times m)$ |
| `Q` | State cost matrix $(n \times n)$, positive semi-definite |
| `R` | Control cost matrix $(m \times m)$, positive definite |

**Returns:** `(K, P)` where `K` is the optimal gain and `P` is the Riccati solution.

## Source

See [`synapsys/algorithms/`](https://github.com/synapsys/synapsys/tree/main/synapsys/algorithms) on GitHub.
