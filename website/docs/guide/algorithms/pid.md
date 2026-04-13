---
id: pid
title: PID Controller
sidebar_position: 1
---

# PID Controller

`PID` implements a discrete-time Proportional-Integral-Derivative controller with **output saturation** and **back-calculation anti-windup**.

## Formula

$$u(k) = K_p \, e(k) + K_i \sum_{j=0}^{k} e(j)\,\Delta t + K_d \, \frac{e(k) - e(k-1)}{\Delta t}$$

Anti-windup corrects the integrator when the output saturates:

$$\text{integral} \mathrel{+}= \frac{u_{sat}(k) - u(k)}{K_i}$$

## Basic usage

```python
from synapsys.algorithms import PID

pid = PID(
    Kp=2.0,
    Ki=0.5,
    Kd=0.1,
    dt=0.01,
    u_min=-10.0,
    u_max=10.0,
)

setpoint = 5.0
y = 0.0

for _ in range(1000):
    u = pid.compute(setpoint=setpoint, measurement=y)
    # ... apply u to plant, read new y ...
```

## Anti-windup

Without anti-windup, the integrator keeps accumulating error during saturation, causing **integrator windup**: excessive delay when leaving saturation.

With back-calculation, when $u$ saturates, the integrator is corrected in the opposite direction:

```python
pid_no_limit = PID(Kp=5.0, Ki=10.0, dt=0.01)
pid_limited  = PID(Kp=5.0, Ki=10.0, dt=0.01,
                   u_min=-1.0, u_max=1.0)

# pid_limited converges much faster after a prolonged saturation
```

## Resetting state

```python
pid.reset()    # clears integrator and previous error
```

Useful on mode switches (manual to automatic) or after abrupt setpoint changes.

## API Reference

See the full reference at [synapsys.algorithms — PID](../../api/algorithms#pid).
