---
id: simview
title: Usage Guide — SimView
sidebar_label: Using the Simulators
sidebar_position: 2
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# 3D Simulators — Usage Guide

This guide shows how to use the three 3D simulators, from the simplest case
(`CartPoleView().run()`) to customizing physical parameters and initial conditions.

---

## Cart-Pole

Classic control benchmark: a cart on a track with an articulated inverted pendulum.
4-dimensional state, unstable at the vertical equilibrium.

![CartPole — real-time 3D simulation](/img/simview/docs/cartpole.gif)

```python
from synapsys.viz import CartPoleView

CartPoleView().run()
```

**Physical parameters (default values):**

| Parameter | Default | Description |
|---|---|---|
| `m_c` | `1.0` kg | cart mass |
| `m_p` | `0.1` kg | bob mass |
| `l` | `0.5` m | pole length |
| `g` | `9.81` m/s² | gravity |

**State:** `x = [cart position, velocity, angle θ, angular velocity θ̇]`

**Default LQR:** `Q = diag([1, 0.1, 100, 10])`, `R = 0.01·I`

**Custom initial state:**

```python
import numpy as np
CartPoleView(x0=np.array([0.0, 0.0, 0.30, 0.0])).run()  # initial angle 0.30 rad
```

:::note Auto-reset
The cart changes color to **amber** at 72% of the track and to **red** at 92%.
When it exceeds 92%, the simulation resets automatically.
:::

---

## Inverted Pendulum

Single-link pendulum on a fixed base. The simplest system for testing
controllers — only 2 states, unstable pole at `+√(g/l)`.

![Inverted Pendulum — real-time 3D simulation](/img/simview/docs/pendulum.gif)

```python
from synapsys.viz import PendulumView

PendulumView().run()
```

**Physical parameters (default values):**

| Parameter | Default | Description |
|---|---|---|
| `m` | `1.0` kg | bob mass |
| `l` | `1.0` m | pole length |
| `g` | `9.81` m/s² | gravity |
| `b` | `0.1` | viscous damping coefficient |

**State:** `x = [θ, θ̇]`

**Default LQR:** `Q = diag([80, 5])`, `R = I`

---

## Mass-Spring-Damper

1D mass-spring-damper system with setpoint tracking.
The MSD has extra controls in the bar: buttons to select 3 reference positions
(0 m, +1.5 m, −1.5 m) and keyboard shortcuts 1/2/3.

![Mass-Spring-Damper — real-time 3D simulation](/img/simview/docs/msd.gif)

```python
from synapsys.viz import MassSpringDamperView

MassSpringDamperView().run()
```

**Physical parameters (default values):**

| Parameter | Default | Description |
|---|---|---|
| `m` | `1.0` kg | mass |
| `c` | `0.5` N·s/m | damping coefficient |
| `k` | `2.0` N/m | spring constant |

**State:** `x = [q, q̇]`

**LQR control law (with setpoint feed-forward):**

```
u = −K·(x − x_ref) + k·sp
```

**Available setpoints (keyboard):**

| Key | Setpoint |
|---|---|
| `1` | 0.0 m |
| `2` | +1.5 m |
| `3` | −1.5 m |

**Custom setpoints and initial state:**

```python
import numpy as np
MassSpringDamperView(
    setpoints=[("0", 0.0), ("+2m", 2.0), ("-2m", -2.0)],
    x0=np.array([1.0, 0.0]),
).run()
```

---

## Window anatomy

```
┌──────────────────────────────────────────────────────────────────────┐
│  Window title                                                        │
├──────────────────────────────┬───────────────────────────────────────┤
│                              │  ┌─────────────────────────────────┐  │
│   PyVista 3D                 │  │  Position / angle               │  │
│   • physics animation        │  ├─────────────────────────────────┤  │
│   • HUD with live            │  │  Velocity / angular velocity    │  │
│     state values             │  ├─────────────────────────────────┤  │
│                              │  │  Control force / torque         │  │
│   A/D=pert  R=reset          │  ├─────────────────────────────────┤  │
│   SPACE=pause  Q=close       │  │  Phase portrait                 │  │
│                              │  │  (current point in cyan)        │  │
│                              │  └─────────────────────────────────┘  │
├──────────────────────────────┴───────────────────────────────────────┤
│  [◀ Perturb]  [──●────── Magnitude: 20 N ──]  [Perturb ▶]           │
│  [⏸ Pause]  [↺ Reset]                                               │
├──────────────────────────────────────────────────────────────────────┤
│  t = 3.42 s  |  pos = +0.012 m  |  θ = −0.03°  |  running           │
└──────────────────────────────────────────────────────────────────────┘
```

| Region | Contents |
|---|---|
| 3D panel (left, ~55%) | Animated physics scene + state HUD + keyboard hints |
| Telemetry panel (right, ~45%) | 4 matplotlib charts (update rate: CartPole ~17 Hz · Pendulum/MSD ~20 Hz) |
| Control bar (80 px) | Hold-to-apply perturbation + slider + pause/reset |
| Status bar | Simulation time, key variables, state (running/PAUSED) |

### Telemetry charts by simulator

<Tabs>
  <TabItem value="cartpole" label="Cart-Pole">

| Panel | Contents | Color |
|---|---|---|
| 1 | Cart position x(t) in m (left axis) + velocity ẋ(t) in m/s (right axis) | Blue + dashed orange |
| 2 | Pole angle θ(t) in degrees | Orange |
| 3 | Control force u(t) in N | Red |
| 4 | Phase portrait (θ vs θ̇) | Violet + cyan dot |

  </TabItem>
  <TabItem value="pendulum" label="Pendulum">

| Panel | Contents | Color |
|---|---|---|
| 1 | Angle θ(t) in degrees | Blue |
| 2 | Angular velocity θ̇(t) in °/s | Orange |
| 3 | Control torque τ(t) in N·m | Red |
| 4 | Phase portrait (θ vs θ̇) | Violet + cyan dot |

  </TabItem>
  <TabItem value="msd" label="MSD">

| Panel | Contents | Color |
|---|---|---|
| 1 | Position q(t) with setpoint reference | Blue + dashed green line |
| 2 | Velocity q̇(t) in m/s | Orange |
| 3 | Control force u(t) in N | Red |
| 4 | Phase portrait (q vs q̇) | Violet + cyan dot |

  </TabItem>
</Tabs>

---

## Keyboard controls

| Key | Action | Note |
|---|---|---|
| `A` (hold) | Negative perturbation | Release → perturbation returns to zero |
| `D` (hold) | Positive perturbation | Release → perturbation returns to zero |
| `R` | Full reset | Returns to initial state, clears history |
| `Space` | Pause / Resume | Toggles between `⏸` and `▶` |
| `Q` / `Esc` | Close window | Stops timer and closes PyVista |
| `1` / `2` / `3` | Change setpoint | **MSD only** |

> Shortcuts work regardless of which panel has focus (3D or matplotlib).

---

## Custom physical parameters

All physical parameters can be passed in the constructor:

```python
from synapsys.viz import CartPoleView, PendulumView, MassSpringDamperView

# Heavy cart, long pole
CartPoleView(m_c=3.0, m_p=0.5, l=1.0).run()

# Short pendulum with higher damping
PendulumView(m=0.5, l=0.6, b=0.3).run()

# Stiffer spring, low damping (underdamped)
MassSpringDamperView(m=1.0, c=0.1, k=10.0).run()
```

> When physical parameters change, the automatic LQR is redesigned internally
> via `sim.linearize()` — no manual tuning needed.

---

## Perturbations

The `◀ Perturb` and `Perturb ▶` buttons apply a force/torque **while
the button is held** (hold-to-apply). Releasing the button returns the perturbation to zero.
Equivalent to holding A or D on the keyboard.

The **magnitude slider** sets the maximum perturbation value. Ranges by simulator:

| Simulator | Range | Default |
|---|---|---|
| Cart-Pole | 1–80 N | 30 N |
| Pendulum | 1–40 N·m | 20 N·m |
| MSD | 1–30 N | 15 N |

---

## Color palette

All visual elements use the canonical palette tokens.
See [Dark color tokens →](../../api/viz#dark)

```python
from synapsys.viz.palette import Dark, mpl_theme

mpl_theme()  # apply dark theme globally to matplotlib
```
