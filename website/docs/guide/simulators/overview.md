---
id: simulators-overview
title: Physics Simulators — Overview
sidebar_label: Overview
sidebar_position: 1
---

# Physics Simulators

`synapsys.simulators` provides nonlinear continuous-time physics simulators with a
unified interface for control design, testing, and reinforcement learning.

---

## Available simulators

| Class | System | States | Inputs | Outputs |
|---|---|---|---|---|
| `MassSpringDamperSim` | 1-DOF linear MSD | `[q, q̇]` | `[F]` | `[q]` |
| `InvertedPendulumSim` | Nonlinear pendulum on fixed pivot | `[θ, θ̇]` | `[τ]` | `[θ]` |
| `CartPoleSim` | Lagrangian cart-pole | `[p, ṗ, θ, θ̇]` | `[F]` | `[p, θ]` |

---

## Common interface

Every simulator inherits from `SimulatorBase` and exposes the same API:

```python
from synapsys.simulators import CartPoleSim

sim = CartPoleSim()
y = sim.reset()                   # reset → initial observation
y, info = sim.step(u, dt=0.02)    # advance one step
ss  = sim.linearize(x0, u0)      # numerical linearisation → StateSpace
```

### `step()` info dict

```python
y, info = sim.step(u, dt=0.02)
info["x"]       # full state after step
info["t_step"]  # integration time (= dt)
info["failed"]  # True when the system left its safe region
```

---

## Integrators

All simulators support three numerical integration methods selectable at construction:

| Method | Accuracy | Speed | Recommended use |
|---|---|---|---|
| `"euler"` | Low | Fastest | Very small dt (≤ 1 ms), RL inner loops |
| `"rk4"` | High | Fast | Default — good balance |
| `"rk45"` | Very high | Slower | Reference / validation |

```python
sim = CartPoleSim(integrator="rk4")   # default
sim = CartPoleSim(integrator="euler") # fastest
```

---

## Noise and disturbances

```python
sim = InvertedPendulumSim(noise_std=0.01, disturbance_std=0.05)
```

- `noise_std` — Gaussian noise added to every observation (sensor noise model)
- `disturbance_std` — Gaussian noise injected into the control input (process noise)

---

## Thread-safe parameter updates

All simulators support live parameter changes from a separate thread:

```python
sim.set_params(m=0.5)     # InvertedPendulumSim
sim.set_params(m_c=2.0)   # CartPoleSim
```

---

## Failure detection

```python
y, info = sim.step(u, dt)
if info["failed"]:
    sim.reset()
```

| Simulator | Failure condition |
|---|---|
| `CartPoleSim` | `\|p\| > 4.8 m` or `\|θ\| > π/3 rad` |
| `InvertedPendulumSim` | `\|θ\| > π/2 rad` |
| `MassSpringDamperSim` | never (always stable) |

---

## Linearisation

Every simulator exposes `linearize(x0, u0)` which returns a continuous-time
`StateSpace` via central finite differences — ready for LQR design:

```python
from synapsys.algorithms.lqr import lqr

ss = sim.linearize(np.zeros(4), np.zeros(1))
K, _ = lqr(ss.A, ss.B, Q, R)
```
