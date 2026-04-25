---
id: viz
title: synapsys.viz
sidebar_label: synapsys.viz
---

# `synapsys.viz`

Visualization module: canonical color palettes, matplotlib theming, a lightweight 2D
cart-pole animation, and plug-and-play 3D simulation windows.

```python
from synapsys.viz import (
    Dark, Light, mpl_theme,
    CartPole2DView,
    CartPoleView, PendulumView, MassSpringDamperView,
)
```

---

## `CartPole2DView`

Lightweight 2D cart-pole animation built on pure **matplotlib** — no Qt or PyVista
required.

```python
CartPole2DView(
    sim:        CartPoleSim | None = None,   # default instance created if None
    controller: Callable | None = None,      # (x: ndarray) → ndarray; auto-LQR if None
    dt:         float = 0.02,                # integration / animation step (s)
    duration:   float = 10.0,               # total simulation time (s)
    x0:         ndarray | None = None,       # initial state [p, ṗ, θ, θ̇]; default [0, 0, 0.15, 0]
)
```

### Methods

#### `simulate() → dict`

Run the simulation and return a history dictionary.

| Key | Shape | Contents |
|---|---|---|
| `"t"` | `(steps,)` | time array |
| `"pos"` | `(steps,)` | cart position (m) |
| `"angle"` | `(steps,)` | pole angle (rad) |
| `"force"` | `(steps,)` | control force (N) |
| `"states"` | `(steps, 4)` | full state `[p, ṗ, θ, θ̇]` |

#### `animate(save=None) → FuncAnimation`

Build and return a `matplotlib.animation.FuncAnimation`.

| Parameter | Type | Description |
|---|---|---|
| `save` | `str \| None` | save to file if given (e.g. `"out.gif"`); requires *Pillow* for GIF or *ffmpeg* for MP4 |

#### `run() → None`

`simulate()` → `animate()` → `plt.show()`. All-in-one entry point.

### Examples

```python
from synapsys.viz import CartPole2DView
import numpy as np

# Auto-LQR, default parameters
CartPole2DView().run()

# Custom controller
K = ...  # your gain matrix
CartPole2DView(controller=lambda x: np.clip(-K @ x, -50, 50)).run()

# Headless simulation (no display)
hist = CartPole2DView(dt=0.02, duration=5.0).simulate()
print(hist["angle"][-1])   # final pole angle (rad)

# Save animation to GIF
view = CartPole2DView()
anim = view.animate(save="cartpole.gif")
```

---

## `SimViewBase`

Base class for all 3D views. Inherits from `QMainWindow`.
**Do not instantiate directly** — use the concrete subclasses.

### Class attributes (configurable in subclasses)

| Attribute | Type | Default | Description |
|---|---|---|---|
| `_title` | `str` | `"Synapsys Simulator"` | Qt window title |
| `_mpl_title` | `str` | `"Telemetry"` | matplotlib panel title |
| `_dt` | `float` | `0.02` | simulation time step in seconds |
| `_hist_len` | `int` | `500` | history deque length |
| `_mpl_skip` | `int` | `3` | render matplotlib every N ticks |
| `_pert_max_default` | `float` | `20.0` | default perturbation magnitude |
| `_slider_range` | `tuple` | `(1, 50)` | magnitude slider range |
| `_slider_unit` | `str` | `"N"` | unit shown on the slider label |
| `_splitter_w` | `tuple` | `(770, 630)` | initial panel widths (3D, mpl) |
| `_u_clip` | `float` | `50.0` | controller output saturation |
| `_u_clip_total` | `float` | `80.0` | total saturation after adding perturbation |

### Constructor

```python
SimViewBase(
    controller: Callable | None = None,  # (x: ndarray) → ndarray; auto-LQR if None
    save:       str | None = None,       # path to save the animation on close (e.g. "out.gif")
)
```

### Public methods

#### `run() → None`

Creates `QApplication` (if not already present), initializes `QMainWindow`, builds the full UI
and enters the Qt event loop. **Does not return** (calls `sys.exit`).

```python
CartPoleView().run()
CartPoleView(controller=fn).run()
```

#### `set_camera_preset(name) → None`

Apply a named camera position before the window opens.

| Preset | Description |
|---|---|
| `"iso"` | Isometric view (default for most views) |
| `"top"` | Top-down orthographic |
| `"side"` | Side view |
| `"follow"` | Low follow-cam (close behind) |

```python
view = CartPoleView()
view.set_camera_preset("top")
view.run()
```

#### `toggle_trail() → None`

Enable or disable the 3D trajectory trail. Each tick appends the point returned by
`_trail_point(x)` (overridable per view). The trail keeps the last 200 points.

```python
view = CartPoleView()
view.toggle_trail()   # enable trail
view.run()
```

### Hooks (optional override in subclasses)

| Method | Signature | Description |
|---|---|---|
| `_lqr_u(x)` | `(ndarray) → ndarray` | LQR control law. Default: `−K@x`. Override for setpoint tracking. |
| `_pert_vector()` | `() → ndarray` | Converts scalar `_pert` to input vector. |
| `_build_extra_controls(hb)` | `(QHBoxLayout) → None` | Injects extra widgets into the control bar. |
| `_on_reset()` | `() → None` | Called after `sim.reset()` — useful for resetting extra state. |
| `_post_tick(x, u)` | `(ndarray, ndarray) → None` | Called at the end of each tick. |
| `_trail_point(x)` | `(ndarray) → ndarray` | Returns a 3D world position `(3,)` to append to the trail. Default: `[x[0], 0, 0]`. |

---

## `CartPoleView`

```python
CartPoleView(
    controller: Callable | None = None,
    m_c: float = 1.0,              # cart mass [kg]
    m_p: float = 0.1,              # bob mass [kg]
    l:   float = 0.5,              # pole length [m]
    g:   float = 9.81,             # gravity [m/s²]
    x0:  np.ndarray | None = None, # initial state (4,) — default [0, 0, 0.18, 0]
    save: str | None = None,       # path to save animation on close
)
```

**System:** cart on a track with an articulated inverted pendulum.

**State:** `x = [cart position (m), velocity (m/s), angle θ (rad), angular velocity (rad/s)]`

**Input:** horizontal force on the cart (N).

**Default LQR:** `Q = diag([1, 0.1, 100, 10])`, `R = 0.01·I`

**Perturbation:** ◀/▶ buttons and A/D keys — horizontal force (1–80 N, default 30 N).

**Auto-reset:** the cart resets automatically when it reaches 92% of the track length (`_LIMIT_FRAC = 0.92`). Between 72% and 92% the cart changes color to amber as a warning.

**Trail point:** pole tip — `[p + l·sin(θ), 0, PIVOT_Z + l·cos(θ)]`

---

## `PendulumView`

```python
PendulumView(
    controller: Callable | None = None,
    m:  float = 1.0,              # bob mass [kg]
    l:  float = 1.0,              # pole length [m]
    g:  float = 9.81,             # gravity [m/s²]
    b:  float = 0.1,              # viscous damping
    x0: np.ndarray | None = None, # initial state (2,) — default [0.18, 0]
    save: str | None = None,      # path to save animation on close
)
```

**System:** single-link inverted pendulum on a fixed base.

**State:** `x = [angle θ (rad), angular velocity θ̇ (rad/s)]`

**Input:** joint torque (N·m).

**Unstable pole:** `λ = +√(g/l)` ≈ `+3.13 rad/s` at default parameters.

**Default LQR:** `Q = diag([80, 5])`, `R = I`

**Perturbation:** ↺/↻ buttons and A/D keys — torque (1–40 N·m, default 20 N·m).
Red arrows appear at the pole tip indicating direction and magnitude.

**Trail point:** pole tip — `[l·sin(θ), 0, PIVOT_Z + l·cos(θ)]`

---

## `MassSpringDamperView`

```python
MassSpringDamperView(
    controller: Callable | None = None,
    m:         float = 1.0,              # mass [kg]
    c:         float = 0.5,              # damping [N·s/m]
    k:         float = 2.0,             # spring constant [N/m]
    x0:        np.ndarray | None = None, # initial state (2,) — default [0, 0]
    setpoints: list | None = None,       # list of (label, value_m) — default 3 points
    save:      str | None = None,        # path to save animation on close
)
```

**System:** 1D mass-spring-damper with setpoint tracking.

**State:** `x = [position q (m), velocity q̇ (m/s)]`

**Input:** external force (N).

**LQR with feed-forward:** `u = −K·(x − x_ref) + k·sp`

**Default setpoints:** `[("0 m", 0.0), ("+1.5 m", 1.5), ("−1.5 m", -1.5)]` (buttons or keys 1/2/3).
Custom setpoints:

```python
MassSpringDamperView(setpoints=[("0", 0.0), ("+2m", 2.0), ("-2m", -2.0)]).run()
```

**Perturbation:** ◀/▶ buttons and A/D keys — force (1–30 N, default 15 N).

**Trail point:** mass position — `[q, 0, MASS_H/2]`

---

## `Dark`

Synapsys design system color tokens — dark theme (mirrors the website dark mode).

```python
from synapsys.viz.palette import Dark
```

### Backgrounds

| Token | Hex | Use |
|---|---|---|
| `Dark.BG` | `#111111` | Window background / matplotlib figure |
| `Dark.SURFACE` | `#1a1a1a` | Cards, panels, matplotlib axes |
| `Dark.PANEL` | `#1e1e1e` | Qt GroupBox |
| `Dark.BORDER` | `#2e2e2e` | Default borders |
| `Dark.BORDER_LT` | `#222222` | Subtle border |

### Text

| Token | Hex | Use |
|---|---|---|
| `Dark.FG` | `#e2e8f0` | Primary text |
| `Dark.MUTED` | `#999999` | Axis labels, secondary text |
| `Dark.SUBTLE` | `#666666` | Tertiary text / hints |
| `Dark.GRID` | `#2e2e2e` | matplotlib grid lines |

### Brand

| Token | Hex | Use |
|---|---|---|
| `Dark.GOLD` | `#c8a870` | Primary brand color / highlight |
| `Dark.GOLD_DIM` | `#987040` | Dark variant |
| `Dark.GOLD_LT` | `#d8b880` | Light variant |
| `Dark.TEAL` | `#0d9488` | Secondary brand color |

### Status / alerts

| Token | Hex | Use |
|---|---|---|
| `Dark.DANGER` | `#ef4444` | Error, limit reached, active perturbation |
| `Dark.WARN` | `#f59e0b` | Warning (e.g. cart approaching track limit) |
| `Dark.OK` | `#22c55e` | Stabilized / ok |

### Signals

| Token | Hex | Physical quantity |
|---|---|---|
| `Dark.SIG_POS` | `#3b82f6` | Position / displacement |
| `Dark.SIG_POS_LT` | `#60a5fa` | Position (light variant / second channel) |
| `Dark.SIG_VEL` | `#f97316` | Velocity / rate |
| `Dark.SIG_VEL_LT` | `#fb923c` | Velocity (light variant) |
| `Dark.SIG_ANG` | `#f97316` | Angle |
| `Dark.SIG_REF` | `#22c55e` | Setpoint / reference |
| `Dark.SIG_REF_DK` | `#16a34a` | Reference (dark variant — dashed line) |
| `Dark.SIG_REF_LT` | `#4ade80` | Reference (light variant — checked/active) |
| `Dark.SIG_CTRL` | `#ef4444` | Control force / torque |
| `Dark.SIG_PHASE` | `#a78bfa` | Phase portrait |
| `Dark.SIG_TRAIL` | `#7c3aed` | 3D trail |
| `Dark.SIG_ALT` | `#facc15` | Altitude z |
| `Dark.SIG_CYAN` | `#38bdf8` | Current point (dot marker) |

### 3D objects

| Token | Hex | Object |
|---|---|---|
| `Dark.MESH_BODY` | `#2563eb` | Main body (mass, cart) |
| `Dark.MESH_POLE` | `#c8a870` | Pole / arm |
| `Dark.MESH_BOB` | `#f97316` | Bob / pole tip |
| `Dark.MESH_SPRING` | `#c8a870` | Spring |
| `Dark.MESH_DAMP` | `#64748b` | Damper |
| `Dark.MESH_STRUCT` | `#334155` | Structure / base |
| `Dark.MESH_WALL` | `#334155` | Anchor wall |
| `Dark.MESH_FLOOR` | `#1a1a1a` | Floor / ground plane |
| `Dark.MESH_RAIL` | `#475569` | Track rail |
| `Dark.MESH_STOP` | `#ef4444` | Track end stop |
| `Dark.MESH_REF` | `#4ade80` | Reference sphere (setpoint) |

---

## `Light`

Synapsys design system color tokens — light theme (for presentations, reports, and
environments with white backgrounds).

```python
from synapsys.viz.palette import Light
```

### Backgrounds

| Token | Hex | Use |
|---|---|---|
| `Light.BG` | `#ffffff` | Window background / matplotlib figure |
| `Light.SURFACE` | `#f8fafc` | Cards, panels, matplotlib axes |
| `Light.PANEL` | `#f1f5f9` | Qt GroupBox |
| `Light.BORDER` | `#e2e8f0` | Default borders |

### Text

| Token | Hex | Use |
|---|---|---|
| `Light.FG` | `#0f172a` | Primary text |
| `Light.MUTED` | `#475569` | Axis labels, secondary text |
| `Light.SUBTLE` | `#94a3b8` | Tertiary text / hints |
| `Light.GRID` | `#e2e8f0` | matplotlib grid lines |

### Brand

| Token | Hex | Use |
|---|---|---|
| `Light.GOLD` | `#92671e` | Primary brand color / highlight |
| `Light.GOLD_LT` | `#c8a870` | Light variant |
| `Light.TEAL` | `#0d9488` | Secondary brand color |

### Signals

| Token | Hex | Physical quantity |
|---|---|---|
| `Light.SIG_POS` | `#1d4ed8` | Position / displacement |
| `Light.SIG_VEL` | `#c2410c` | Velocity / rate |
| `Light.SIG_ANG` | `#c2410c` | Angle |
| `Light.SIG_REF` | `#15803d` | Setpoint / reference |
| `Light.SIG_CTRL` | `#b91c1c` | Control force / torque |
| `Light.SIG_PHASE` | `#7c3aed` | Phase portrait |
| `Light.SIG_TRAIL` | `#6d28d9` | 3D trail |
| `Light.SIG_CYAN` | `#0284c7` | Current point (dot marker) |

---

## `mpl_theme()`

```python
from synapsys.viz.palette import mpl_theme

mpl_theme()            # dark (default)
mpl_theme("light")     # light
mpl_theme("dark")      # dark (explicit)
```

Applies Synapsys theme global rcParams to matplotlib.
Must be called **before** creating any `Figure`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `theme` | `str` | `"dark"` | `"dark"` or `"light"` |

Automatically configures: `figure.facecolor`, `axes.facecolor`, grid, ticks,
legend, and font (`JetBrains Mono`).

```python
from synapsys.viz.palette import mpl_theme, Light
import matplotlib.pyplot as plt

mpl_theme("light")

fig, ax = plt.subplots()
ax.plot([0, 1, 2], [0, 1, 0], color=Light.SIG_POS)
plt.show()
```
