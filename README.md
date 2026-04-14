<div align="center">

<img src="https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/logo.svg" width="96" height="96" alt="Synapsys logo" />

# Synapsys

**Modern Python control systems framework with distributed multi-agent simulation**

[![CI](https://github.com/synapsys-lab/synapsys/actions/workflows/ci.yml/badge.svg)](https://github.com/synapsys-lab/synapsys/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/synapsys.svg?color=blue&label=PyPI)](https://pypi.org/project/synapsys/)
[![Python](https://img.shields.io/pypi/pyversions/synapsys.svg)](https://pypi.org/project/synapsys/)
[![Docs](https://img.shields.io/badge/docs-synapsys--lab.github.io-blue)](https://synapsys-lab.github.io/synapsys/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen.svg)](#testing)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[📖 Documentation](https://synapsys-lab.github.io/synapsys/) · [🚀 Quickstart](#quickstart) · [📦 PyPI](https://pypi.org/project/synapsys/) · [💡 Examples](examples/) · [📋 Changelog](CHANGELOG.md)

</div>

---

## Overview

Synapsys is an open-source Python library for **modelling, simulating, and deploying control systems**. It provides a **MATLAB-compatible API** built on SciPy, a modern **multi-agent simulation framework**, and a pluggable **transport layer** (shared memory / ZeroMQ) that scales from a single laptop to distributed lab setups.

```python
from synapsys.api import tf, feedback, step, c2d

G    = tf([1], [1, 2, 1])    # G(s) = 1 / (s² + 2s + 1)
T    = feedback(G)            # closed-loop: T = G / (1 + G)
t, y = step(T)                # step response
Gd   = c2d(G, dt=0.02)       # ZOH discretisation at 50 Hz
```

```bash
pip install synapsys
```

---

## See it in action

Neural-LQR controller on a 2-DOF mass-spring-damper — MLP initialized with LQR optimal gains tracking setpoint x₂ = 1 m:

<div align="center">
<img src="https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/examples/03_sil_ai_controller.gif" alt="Neural-LQR 2-DOF simulation — position tracking, velocities, control force and phase portrait" width="720" />
</div>

> Full walkthrough: [SIL + Neural-LQR example →](https://synapsys-lab.github.io/synapsys/docs/examples/advanced/sil-ai-controller)

---

## Features

| Feature | Description |
|---------|-------------|
| ⚡ **MATLAB-Compatible API** | `tf()`, `ss()`, `c2d()`, `step()`, `bode()`, `feedback()`, `lsim()` — same names, pure Python |
| 📐 **LTI Core** | `TransferFunction` and `StateSpace` with operator overloading, poles, zeros, stability |
| 🧮 **Control Algorithms** | Discrete PID with anti-windup · LQR via algebraic Riccati equation |
| 🤖 **Multi-Agent Simulation** | `PlantAgent` and `ControllerAgent` with lock-step and wall-clock sync |
| 🔗 **Pluggable Transport** | Zero-copy shared memory (single-host) · ZeroMQ PUB/SUB and REQ/REP (distributed) |
| 🔌 **Hardware Abstraction** | `HardwareInterface` contract enables seamless MIL → SIL → HIL transitions |
| 🧱 **Matrix Builders** | `StateEquations`, `mat()`, `col()`, `row()` — define state-space models from named equations |

---

## Installation

```bash
pip install synapsys
```

**Requirements:** Python ≥ 3.10 · NumPy ≥ 1.24 · SciPy ≥ 1.10 · pyzmq ≥ 25.0

For development:

```bash
git clone https://github.com/synapsys-lab/synapsys.git
cd synapsys
uv sync --extra dev
```

---

## Quickstart

### 1 · LTI systems and frequency analysis

```python
from synapsys.api import tf, ss, bode, feedback, c2d

# Second-order transfer function
G = tf([1], [1, 2, 1])

# Closed-loop with unity negative feedback
T = feedback(G)

# Frequency response
w, mag, phase = bode(G)

# ZOH discretisation at 50 Hz
Gd = c2d(G, dt=0.02)
```

### 2 · Control algorithms

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
# Control law: u = −K · x
```

### 3 · State-space from named equations

```python
from synapsys.utils import StateEquations

m, c, k = 1.0, 0.1, 2.0

eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1).eq("x2", v2=1)
    .eq("v1", x1=-2*k/m, x2=k/m,  v1=-c/m)
    .eq("v2", x1=k/m,  x2=-2*k/m, v2=-c/m, F=1/m)
)

print(eqs.A)   # 4×4 system matrix
print(eqs.B)   # 4×1 input matrix
```

### 4 · Multi-agent closed-loop simulation

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
    law  = lambda y: np.array([pid.compute(setpoint=3.0, measurement=y[0])])
    sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)

    PlantAgent("plant", plant_d, bus, sync).start(blocking=False)
    ControllerAgent("ctrl",  law,  bus, sync).start(blocking=True)
```

### 5 · MIL → SIL → HIL — swap transport, keep algorithm

```python
# MIL — shared memory, single host
from synapsys.transport import SharedMemoryTransport
bus = SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True)

# SIL — ZeroMQ, cross-process / cross-machine
from synapsys.transport import ZMQTransport
bus = ZMQTransport("tcp://localhost:5555", mode="pub")

# HIL — real hardware
from synapsys.agents import HardwareAgent
from synapsys.hw import MockHardwareInterface   # replace with your driver
hw    = MockHardwareInterface(n_inputs=1, n_outputs=1, plant_fn=my_hw)
agent = HardwareAgent("hw", hw, bus, sync)

# PlantAgent / ControllerAgent stay exactly the same in all three modes
```

---

## Examples

| Example | Description |
|---------|-------------|
| [`basic/step_response.py`](examples/basic/step_response.py) | Step response of a 2nd-order system |
| [`distributed/plant.py`](examples/distributed/plant.py) + [`controller.py`](examples/distributed/controller.py) | Two-process PID loop via shared memory |
| [`distributed/plant_zmq.py`](examples/distributed/plant_zmq.py) | Same loop over ZeroMQ (cross-machine) |
| [`advanced/01_custom_signals.py`](examples/advanced/01_custom_signals.py) | Custom reference signals with `lsim()` |
| [`advanced/02a_sil_plant.py`](examples/advanced/02a_sil_plant.py) + [`02b_sil_ai_controller.py`](examples/advanced/02_sil_ai_controller/02b_sil_ai_controller.py) | SIL + Neural-LQR PyTorch controller |
| [`advanced/03_realtime_scope.py`](examples/advanced/03_realtime_scope.py) | Text-mode real-time oscilloscope |
| [`advanced/04_realtime_matplotlib.py`](examples/advanced/04_realtime_matplotlib.py) | Live matplotlib oscilloscope |
| [`advanced/05_digital_twin.py`](examples/advanced/05_digital_twin.py) | Digital twin with mechanical wear detection |
| [`quickstart_en.ipynb`](examples/quickstart_en.ipynb) | Interactive Jupyter notebook walkthrough |

---

## Architecture

```
synapsys/
├── api/            # MATLAB-compatible façade  (tf, ss, c2d, step, bode, …)
├── core/           # LTI math — TransferFunction, StateSpace, LTIModel
├── algorithms/     # PID (discrete, anti-windup), LQR (ARE solver)
├── agents/         # PlantAgent, ControllerAgent, HardwareAgent, SyncEngine
├── transport/      # SharedMemoryTransport, ZMQTransport, ZMQReqRepTransport
├── hw/             # HardwareInterface (abstract) + MockHardwareInterface
└── utils/          # StateEquations, mat(), col(), row()
```

The transport layer is the key abstraction: agents communicate exclusively through a `TransportStrategy` interface. Swapping the concrete transport (shared memory ↔ ZMQ ↔ real hardware) requires changing **one line** — algorithms and agents are untouched.

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
| Test suite | 74 tests |
| Coverage | 86 % |
| Type checking | mypy strict — 0 errors |
| Python versions | 3.10 · 3.11 · 3.12 |

---

## Roadmap

| Version | Status | Planned features |
|---------|--------|-----------------|
| **v0.1.0** | ✅ Released | SISO LTI, PID, LQR, multi-agent, shared memory, ZMQ, hardware abstraction, Neural-LQR example |
| **v0.2** | 🔜 Planned | MIMO systems, `margin()`, `rlocus()`, `pole_placement()` |
| **v0.3** | 🔜 Planned | State estimation — Kalman filter, Luenberger observer |
| **v0.5** | 🔜 Planned | Real hardware drivers (serial, CAN, FPGA via PYNQ) |

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

Contributions are welcome! Please open an issue to discuss what you'd like to change before submitting a pull request.

```bash
git clone https://github.com/synapsys-lab/synapsys.git
cd synapsys
uv sync --extra dev
uv run pytest          # make sure everything passes before you start
```

---

## License

[MIT](LICENSE) © 2026 Synapsys Contributors
