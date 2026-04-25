---
id: viz-overview
title: 3D Simulators — Overview
sidebar_label: Overview
sidebar_position: 1
---

# 3D Simulators — Overview

![Cart-Pole — real-time 3D simulation](/img/simview/cartpole.gif)

`synapsys.viz.simview` provides **plug-and-play 3D simulation windows** that combine
real-time PyVista rendering and matplotlib telemetry in a single PySide6 interface —
ready to accept any controller you design.

---

## What you get in one line

```python
from synapsys.viz import CartPoleView
CartPoleView().run()
```

A complete window with:

- **3D panel** — real-time physics animation (PyVista + VTK)
- **Telemetry panel** — 4 synchronized matplotlib charts (position, angle, control, phase portrait)
- **Control bar** — hold-to-apply perturbation buttons, magnitude slider, pause/reset
- **Automatic LQR** — if no controller is provided, the lib linearizes the simulator and designs an LQR internally
- **Global keyboard capture** — A/D (perturbation), R (reset), Space (pause), Q (close)

---

## Architecture

```
SimulatorBase          ← synapsys.simulators
│  dynamics(), step(), linearize()
│
SimViewBase            ← synapsys.viz.simview._base  (QMainWindow)
│  • creates Qt window (3D + matplotlib splitter)
│  • QTimer loop → _on_tick()
│  • auto-LQR via linearize() + lqr()
│  • keyboard, perturbations, pause, reset
│  • _build_all() called in run()
│
├── CartPoleView        ← state: [x, ẋ, θ, θ̇]
├── PendulumView        ← state: [θ, θ̇]
└── MassSpringDamperView ← state: [q, q̇]  + setpoint tracking
```

Each subclass implements only what is specific to its physical system
(3D scene, charts, HUD, LQR parameters). All Qt boilerplate is inherited from the base.

---

## Available simulators

| Class | Physical system | State | Input | Perturbation |
|---|---|---|---|---|
| `CartPoleView` | Cart + inverted pendulum | `[x, ẋ, θ, θ̇]` | Horizontal force on cart (N) | ◀/▶ horizontal force |
| `PendulumView` | Single-link inverted pendulum | `[θ, θ̇]` | Joint torque (N·m) | ↺/↻ angular torque |
| `MassSpringDamperView` | Mass-spring-damper | `[q, q̇]` | External force (N) | ◀/▶ force + setpoints 1/2/3 |

---

## Standalone vs. library module

<table>
<thead><tr><th>Approach</th><th>Lines of code</th><th>Requires Qt knowledge?</th></tr></thead>
<tbody>
<tr>
<td>Standalone file <code>viz3d_cartpole_qt.py</code></td>
<td>~470 lines</td>
<td>Yes — layout, QTimer, splitter, canvas</td>
</tr>
<tr>
<td><code>CartPoleView().run()</code></td>
<td>1 line</td>
<td>No</td>
</tr>
<tr>
<td><code>CartPoleView(controller=my_net).run()</code></td>
<td>1 line + your function</td>
<td>No</td>
</tr>
</tbody>
</table>

The standalone files in `examples/simulators/` remain available as a reference for
anyone who wants to understand the internal implementation or build highly customized
UIs beyond what the library provides.

---

## Dependencies

```bash
pip install synapsys[viz]
# or individually:
pip install pyside6 pyvistaqt matplotlib numpy
```

> **Note:** `pyvistaqt` requires a VTK installation compatible with Qt.
> In headless environments (servers without a display), use `pyvista` with the offscreen backend.

---

## Next steps

- [Usage guide →](./simview)
- [Connecting your own controller →](./custom-controller)
- [API Reference →](../../api/viz)
