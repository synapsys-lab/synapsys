<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="website/static/img/logo_dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="website/static/img/logo_light.svg">
  <img src="website/static/img/logo.svg" width="96" height="96" alt="Synapsys logo" />
</picture>

# Synapsys

**Modern Python control systems framework with distributed multi-agent simulation**

[![CI](https://github.com/synapsys-lab/synapsys/actions/workflows/ci.yml/badge.svg)](https://github.com/synapsys-lab/synapsys/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/synapsys.svg?color=blue&label=PyPI)](https://pypi.org/project/synapsys/)
[![Python](https://img.shields.io/pypi/pyversions/synapsys.svg)](https://pypi.org/project/synapsys/)
[![Docs](https://img.shields.io/badge/docs-synapsys--lab.github.io-blue)](https://synapsys-lab.github.io/synapsys/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](#testing)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

[Documentation](https://synapsys-lab.github.io/synapsys/) · [Quickstart](#quickstart) · [PyPI](https://pypi.org/project/synapsys/) · [Examples](examples/) · [Changelog](CHANGELOG.md)

</div>

---

## Overview

Synapsys is an open-source Python library for **modelling, simulating, and deploying control systems**. It provides a **MATLAB-compatible API** built on SciPy, a modern **multi-agent simulation framework**, a pluggable **transport layer** (shared memory / ZeroMQ) that scales from a single laptop to distributed lab setups, and **nonlinear physical simulators** with real-time 3D visualisation.

Any PyTorch, Keras or JAX model plugs directly into a `ControllerAgent` via a plain `np.ndarray -> np.ndarray` callback, making it straightforward to combine classical control theory with deep learning or reinforcement learning.

```python
from synapsys.api import tf, ss, feedback, step, c2d

# SISO
G    = tf([1], [1, 2, 1])    # G(s) = 1 / (s^2 + 2s + 1)
T    = feedback(G)            # closed-loop: T = G / (1 + G)
t, y = step(T)                # step response
Gd   = c2d(G, dt=0.02)       # ZOH discretisation at 50 Hz

# MIMO
G_mimo = tf([[[ 1], [0]],
             [[ 0], [1]]],
            [[[1,1],[1]],
             [[1],[1,2]]])
T_mimo = feedback(G_mimo)     # returns StateSpace closed-loop
```

---

## Demo — Physical Simulators + SimView

Real-time 3D physics simulators with interactive Qt+PyVista visualisation. Each simulator exposes a clean `step(u, dt)` / `reset()` / `linearize()` API and can feed any Synapsys agent or controller algorithm directly.

<div align="center">
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/simview/msd.gif" alt="Mass-Spring-Damper SimView — 3D real-time visualisation" width="310" />
<br><sub>Mass-Spring-Damper — 3D view + live telemetry</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/simview/pendulum.gif" alt="Inverted Pendulum SimView — 3D real-time visualisation" width="310" />
<br><sub>Inverted Pendulum — nonlinear dynamics, numerical linearisation</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/simview/cartpole.gif" alt="Cart-Pole SimView — 3D real-time visualisation" width="310" />
<br><sub>Cart-Pole — 4-state Lagrangian system, partial observation</sub>
</td>
</tr>
</table>
</div>

```python
from synapsys.simulators import MassSpringDamperSim
import numpy as np

sim = MassSpringDamperSim(m=1.0, c=0.5, k=2.0)
sim.reset()

for _ in range(1000):
    y, info = sim.step(np.array([1.0]), dt=0.01)   # y = [position]

ss = sim.linearize(x0=np.zeros(2), u0=np.zeros(1))  # → Synapsys StateSpace
```

> Full guide: [SimView documentation](https://synapsys-lab.github.io/synapsys/docs/guide/viz/simview)

---

## Demo — Quadcopter MIMO Neural-LQR

12-state linearised quadcopter controlled by a residual Neural-LQR (`du = -K*e + MLP(e)`).
The MLP output layer is zeroed at initialisation, so the controller starts as provably stable LQR
and the residual can be trained later via RL or imitation learning without destabilising the loop.

<div align="center">
<table>
<tr>
<td align="center">
<img src="https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/examples/06_quadcopter_3d.gif" alt="PyVista 3D window — drone tracking a figure-8 trajectory in real time" width="380" />
<br><sub>PyVista 3D window — drone mesh, trajectory trail and live HUD at 50 Hz</sub>
</td>
<td align="center">
<img src="https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/examples/06_quadcopter_telemetry.gif" alt="matplotlib telemetry — position, Euler angles and control inputs" width="480" />
<br><sub>matplotlib telemetry — x-y position, altitude, Euler angles and control deviations</sub>
</td>
</tr>
</table>
</div>

> Full walkthrough: [Quadcopter MIMO Neural-LQR example](https://synapsys-lab.github.io/synapsys/docs/examples/advanced/quadcopter-mimo)

---

## Features

| Feature | Description |
|---------|-------------|
| MATLAB-Compatible API | `tf()`, `ss()`, `c2d()`, `step()`, `bode()`, `feedback()`, `lsim()` — same names, pure Python |
| LTI Core | `TransferFunction`, `StateSpace`, and `TransferFunctionMatrix` with operator overloading, poles, zeros, stability |
| MIMO Support | `TransferFunctionMatrix` for multi-input multi-output plants, MIMO `feedback()`, transmission zeros via Rosenbrock pencil |
| Control Algorithms | Discrete PID with anti-windup, LQR via algebraic Riccati equation (Q/R validated) |
| Physical Simulators | Nonlinear continuous-time simulators (MSD, inverted pendulum, cart-pole) with Euler/RK4/RK45 integrators, sensor noise and input disturbance, thread-safe `step()` and numerical `linearize()` |
| SimView 3D UI | Real-time Qt+PyVista 3D visualisation layer for each simulator — live telemetry panels, interactive parameter controls |
| AI Integration | Any PyTorch, Keras or JAX model as a controller — plain callable interface, no wrappers |
| Multi-Agent Simulation | `PlantAgent` and `ControllerAgent` with lock-step and wall-clock sync |
| Distributed Transport | Zero-copy shared memory (single-host) and ZeroMQ PUB/SUB and REQ/REP (multi-process / multi-machine) |
| Hardware Abstraction | `HardwareInterface` contract enables seamless MIL to SIL to HIL transitions |
| Matrix Builders | `StateEquations`, `mat()`, `col()`, `row()` — define state-space models from named equations |

---

## Installation

**Requirements:** Python >= 3.10, NumPy >= 1.24, SciPy >= 1.10, pyzmq >= 25.0

```bash
# pip
pip install synapsys

# uv
uv add synapsys

# Poetry
poetry add synapsys

# conda / mamba  (conda-forge)
conda install -c conda-forge synapsys
```

For 3D visualisation (simulators + quadcopter example):

```bash
pip install synapsys[viz] matplotlib
```

For development:

```bash
git clone https://github.com/synapsys-lab/synapsys.git
cd synapsys
uv sync --extra dev
```

---

## Quickstart

### 1. LTI systems and frequency analysis

```python
from synapsys.api import tf, ss, bode, feedback, c2d

# SISO second-order transfer function
G = tf([1], [1, 2, 1])

# Closed-loop with unity negative feedback
T = feedback(G)

# Frequency response
w, mag, phase = bode(G)

# ZOH discretisation at 50 Hz
Gd = c2d(G, dt=0.02)

# MIMO: 2x2 transfer-function matrix
G_mimo = tf(
    [[[1], [0]], [[0], [1]]],
    [[[1, 1], [1]], [[1], [1, 2]]],
)
T_mimo = feedback(G_mimo)    # returns StateSpace
```

### 2. Control algorithms

```python
from synapsys.algorithms import PID, lqr
import numpy as np

# Discrete PID with anti-windup saturation
pid = PID(Kp=3.0, Ki=0.5, Kd=0.1, dt=0.01, u_min=-10.0, u_max=10.0)
u   = pid.compute(setpoint=5.0, measurement=y)

# LQR — solves the algebraic Riccati equation
A = np.array([[0., 1.], [-2., -3.]])
B = np.array([[0.], [1.]])
K, P = lqr(A, B, Q=np.eye(2), R=np.eye(1))
# Control law: u = -K * x
```

### 3. State-space from named equations

```python
from synapsys.utils import StateEquations

m, c, k = 1.0, 0.1, 2.0

eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1).eq("x2", v2=1)
    .eq("v1", x1=-2*k/m, x2=k/m,  v1=-c/m)
    .eq("v2", x1=k/m,  x2=-2*k/m, v2=-c/m, F=1/m)
)

print(eqs.A)   # 4x4 system matrix
print(eqs.B)   # 4x1 input matrix
```

### 4. Multi-agent closed-loop simulation

```python
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import SharedMemoryTransport
import numpy as np

# Discretise G(s) = 1/(s+1) at 100 Hz
plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

with SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True) as bus:
    bus.write("y", np.zeros(1))
    bus.write("u", np.zeros(1))

    pid  = PID(Kp=4.0, Ki=1.0, dt=0.01)
    def law(y: np.ndarray) -> np.ndarray:
        return np.array([pid.compute(setpoint=3.0, measurement=y[0])])

    sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)

    PlantAgent("plant", plant_d, bus, sync).start(blocking=False)
    ControllerAgent("ctrl",  law,  bus, sync).start(blocking=True)
```

### 5. MIL to SIL to HIL — swap transport, keep algorithm

```python
# MIL — shared memory, single host
from synapsys.transport import SharedMemoryTransport
bus = SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True)

# SIL — ZeroMQ, cross-process or cross-machine
from synapsys.transport import ZMQTransport
bus = ZMQTransport("tcp://localhost:5555", mode="pub")

# HIL — real hardware
from synapsys.agents import HardwareAgent
from synapsys.hw import MockHardwareInterface
hw    = MockHardwareInterface(n_inputs=1, n_outputs=1, plant_fn=my_hw)
agent = HardwareAgent("hw", hw, bus, sync)

# PlantAgent and ControllerAgent stay exactly the same in all three modes
```

---

## Examples

| Example | Description |
|---------|-------------|
| [`basic/step_response.py`](examples/basic/step_response.py) | Step response of a 2nd-order system |
| [`distributed/plant.py`](examples/distributed/plant.py) + [`controller.py`](examples/distributed/controller.py) | Two-process PID loop via shared memory |
| [`distributed/plant_zmq.py`](examples/distributed/plant_zmq.py) | Same loop over ZeroMQ (cross-machine) |
| [`advanced/01_custom_signals.py`](examples/advanced/01_custom_signals.py) | Custom reference signals with `lsim()` |
| [`advanced/02_sil_ai_controller/02b_sil_ai_controller.py`](examples/advanced/02_sil_ai_controller/02b_sil_ai_controller.py) | SIL + Neural-LQR PyTorch controller on 2-DOF mass-spring-damper |
| [`advanced/03_realtime_scope.py`](examples/advanced/03_realtime_scope.py) | Text-mode real-time oscilloscope |
| [`advanced/04_realtime_matplotlib.py`](examples/advanced/04_realtime_matplotlib.py) | Live matplotlib oscilloscope |
| [`advanced/05_digital_twin/05_digital_twin.py`](examples/advanced/05_digital_twin/05_digital_twin.py) | Digital twin with mechanical wear detection |
| [`advanced/06_quadcopter_mimo/`](examples/advanced/06_quadcopter_mimo/) | 12-state quadcopter MIMO Neural-LQR with PyVista 3D, config GUI, GIF export |
| [`simulators/01_mass_spring_damper.py`](examples/simulators/01_mass_spring_damper.py) | Mass-spring-damper: step response, LQR design, linearisation validation |
| [`simulators/02_inverted_pendulum.py`](examples/simulators/02_inverted_pendulum.py) | Inverted pendulum: LQR stabilisation, noise and disturbance injection |
| [`simulators/03_cartpole.py`](examples/simulators/03_cartpole.py) | Cart-pole: Lagrangian dynamics, partial observation, LQR control |
| [`quickstart_en.ipynb`](examples/quickstart_en.ipynb) | Interactive Jupyter notebook walkthrough |

---

## Architecture

```
synapsys/
├── api/            # MATLAB-compatible facade  (tf, ss, c2d, step, bode, feedback, ...)
├── core/           # LTI math — TransferFunction, StateSpace, TransferFunctionMatrix, LTIModel
├── algorithms/     # PID (discrete, anti-windup), LQR (ARE solver)
├── agents/         # PlantAgent, ControllerAgent, HardwareAgent, SyncEngine
├── broker/         # MessageBroker, Topic, SharedMemoryBackend, ZMQBrokerBackend
├── transport/      # SharedMemoryTransport, ZMQTransport, ZMQReqRepTransport
├── hw/             # HardwareInterface (abstract) + MockHardwareInterface
├── simulators/     # SimulatorBase, MassSpringDamperSim, InvertedPendulumSim, CartPoleSim
├── viz/            # SimView real-time 3D UI (Qt + PyVista) — MSDView, PendulumView, CartPoleView
└── utils/          # StateEquations, mat(), col(), row()
```

The transport layer is the key abstraction: agents communicate exclusively through a `TransportStrategy` interface. The `broker/` module adds a higher-level pub/sub bus (backed by shared memory or ZMQ) for multi-agent scenarios. The `simulators/` module provides nonlinear physical models that integrate directly with any Synapsys controller via the `step()` API. Swapping transport, broker backend, or simulator requires changing one line — algorithms and agents are untouched.

---

## Testing

```bash
uv run pytest                      # run all tests
uv run pytest --cov=synapsys       # with coverage report
uv run mypy synapsys               # type checking
uv run ruff check synapsys tests   # linting
```

| Metric | Value |
|--------|-------|
| Test suite | 501 tests |
| Coverage | 100% |
| Type checking | mypy strict — 0 errors |
| Pre-commit hooks | ruff lint + format, mypy, pytest |
| Python versions | 3.10, 3.11, 3.12 |

---

## Roadmap

| Version | Status | Features |
|---------|--------|---------|
| v0.1.0 | Released | SISO LTI, PID, LQR, multi-agent, shared memory, ZMQ, hardware abstraction, Neural-LQR example |
| v0.2.0 | Released | MIMO support — `TransferFunctionMatrix`, MIMO `feedback()`, transmission zeros (Rosenbrock pencil), LQR Q/R validation, covariant type annotations |
| v0.2.1 | Released | Quadcopter MIMO Neural-LQR example with PyVista 3D, config GUI, GIF export, version sync fix |
| v0.2.2 | Released | `MessageBroker` pub/sub bus, 100% test coverage, mypy strict, pre-commit hooks |
| v0.2.3 | Released | Quadcopter heading-aligned yaw control, updated demos, PT docs snapshot |
| v0.2.4 | Released | New Synapse-S logo, theme-adaptive navbar, updated website assets |
| v0.2.5 | Released | Nonlinear physical simulators (MSD, inverted pendulum, cart-pole) + SimView real-time 3D UI, 501 tests |
| v0.3 | Planned | `margin()`, `rlocus()`, `pole_placement()`, Kalman filter, Luenberger observer |
| v0.5 | Planned | Real hardware drivers (serial, CAN, FPGA via PYNQ) |

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

---

## Citing

If you use Synapsys in academic work, please cite it as:

**BibTeX**
```bibtex
@software{synapsys2026,
  author    = {Farias, Oseias D. and contributors},
  title     = {Synapsys: A Python Framework for Modelling and
               Real-Time Simulation of Linear Control Systems},
  year      = {2026},
  url       = {https://github.com/synapsys-lab/synapsys},
  license   = {MIT},
}
```

**APA**
```
Farias, O. D., & contributors. (2026). Synapsys: A Python framework for
modelling and real-time simulation of linear control systems.
https://github.com/synapsys-lab/synapsys
```

> For the version number, use the version shown on [PyPI](https://pypi.org/project/synapsys/).

---

## Contributing

Contributions are welcome. Please open an issue to discuss what you would like to change before submitting a pull request.

```bash
git clone https://github.com/synapsys-lab/synapsys.git
cd synapsys
uv sync --extra dev
uv run pre-commit install   # install git hooks (ruff, mypy, pytest)
uv run pytest               # make sure everything passes before you start
```

---

## Contributors

<div align="center">
  <a href="https://github.com/synapsys-lab/synapsys/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=synapsys-lab/synapsys" alt="Contributors" />
  </a>
</div>

---

## License

[MIT](LICENSE) © 2026 Synapsys Contributors
