---
id: intro
title: Introduction
sidebar_position: 1
slug: /
---

# Synapsys

**Modern Python control systems framework with distributed multi-agent simulation.**

[![PyPI version](https://img.shields.io/pypi/v/synapsys.svg?color=blue&label=PyPI)](https://pypi.org/project/synapsys/)
[![Python](https://img.shields.io/pypi/pyversions/synapsys.svg)](https://pypi.org/project/synapsys/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://github.com/synapsys-lab/synapsys/blob/main/LICENSE)

Synapsys is designed as a MATLAB-compatible alternative for control engineers who want:

- A **clean Python API** that mirrors MATLAB/Simulink syntax
- **Distributed simulation** — plant and controller running as independent processes
- **Ultra-low latency** communication via shared memory (zero-copy) or ZeroMQ
- A **solid LTI core** that scales from simple PID loops to multi-agent CPS architectures

---

## Features

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
  <TabItem value="core" label="Core Math">

```python
from synapsys.api import tf, ss, step, bode, feedback, c2d

# Transfer function — same syntax as MATLAB
G = tf([1], [1, 2, 1])        # G(s) = 1 / (s^2 + 2s + 1)

# Block algebra
T = feedback(G)                # T = G / (1 + G)
t, y = step(T)                 # step response
w, mag, ph = bode(G)           # Bode diagram

# ZOH discretisation
Gd = c2d(G, dt=0.05)
```

  </TabItem>
  <TabItem value="algorithms" label="Algorithms">

```python
from synapsys.algorithms import PID, lqr

# Discrete PID with anti-windup
pid = PID(Kp=3.0, Ki=0.5, Kd=0.1, dt=0.01,
          u_min=-10.0, u_max=10.0)
u = pid.compute(setpoint=5.0, measurement=y)

# LQR — solves the algebraic Riccati equation
K, P = lqr(A, B, Q, R)
```

  </TabItem>
  <TabItem value="distributed" label="Distributed Simulation">

```python
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

# Discretise the plant
plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

# Each process gets its own transport handle to the same bus
bus = SharedMemoryTransport("ctrl_bus", {"y": 1, "u": 1}, create=True)
t_plant = SharedMemoryTransport("ctrl_bus", {"y": 1, "u": 1})

agent = PlantAgent("plant", plant_d, t_plant, SyncEngine())
agent.start()   # non-blocking background thread
```

  </TabItem>
</Tabs>

---

## Why Synapsys? (Developer Experience)

Beyond the robust multi-agent architecture for SIL/HIL simulations, Synapsys is built to provide an incredible Developer Experience (DX) for control engineers:

- **Zero Learning Curve (MATLAB Mirror):** The `synapsys.api` layer provides functions like `tf()`, `ss()`, `step()`, and `bode()`. It allows engineers to bring legacy scripts to open-source Python with almost zero friction, avoiding the complex object-oriented overhead of SciPy.
- **Natural Block Algebra:** Overloaded operators allow composing LTI systems exactly as they look in textbooks without invoking complex matrix concatenations manually:
  - Series (Cascade): `G_total = G1 * G2`
  - Parallel: `G_total = G1 + G2`
  - Closed-loop: `T = (C * G).feedback()`
- **Continuous vs. Discrete Abstraction:** You don't need to manually switch between differential ODE solvers and difference equations. Setting `dt > 0` on any object automatically changes behavior across all underlying `.bode()`, `.step()`, and `is_stable()` calls.
- **Zero Callback Hell:** Integrating distributed network agents usually forces complicated async/await wrappers or `.on_message()` callbacks. Synapsys's `ControllerAgent` relies on **synchronous, deterministic functions**, hiding the FIPA ACL communication overhead under a clean procedural layer.
- **Strict Type Hinting:** Built for Modern Python 3.10+, rigorous typing enables rich IDE IntelliSense (VSCode/PyCharm), catching structural array dimension issues before they execute.

---

## Installation

```bash
pip install synapsys
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add synapsys
```

---

## Project Status

:::warning[Pre-Alpha]
Synapsys is under active development. The API may change between versions.
:::

| Module | Status |
|--------|--------|
| `synapsys.core` — LTI, StateSpace, TransferFunction | Stable |
| `synapsys.algorithms` — PID, LQR | Stable |
| `synapsys.agents` — PlantAgent, ControllerAgent | Functional |
| `synapsys.transport` — SharedMemory, ZMQ | Functional |
| `synapsys.api` — MATLAB-compat layer | Stable |
| `synapsys.hw` — Hardware abstraction | Interface only |
| MPC, adaptive control | Planned |
| Graphical block editor | Planned |
