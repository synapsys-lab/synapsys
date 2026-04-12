<div align="center">

<img src="website/static/img/logo.svg" width="96" height="96" alt="Synapsys logo" />

# Synapsys

**Modern Python control systems framework with distributed multi-agent simulation**

[![CI](https://github.com/synapsys-lab/synapsys/actions/workflows/ci.yml/badge.svg)](https://github.com/synapsys-lab/synapsys/actions/workflows/ci.yml)
[![Deploy Docs](https://github.com/synapsys-lab/synapsys/actions/workflows/docs.yml/badge.svg)](https://synapsys-lab.github.io/synapsys/)
[![PyPI version](https://img.shields.io/pypi/v/synapsys.svg?color=blue)](https://pypi.org/project/synapsys/)
[![Python](https://img.shields.io/pypi/pyversions/synapsys.svg)](https://pypi.org/project/synapsys/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Coverage](https://img.shields.io/badge/coverage-86%25-brightgreen.svg)](#testing)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

[Documentation](https://synapsys-lab.github.io/synapsys/) · [Quickstart](#quickstart) · [Examples](examples/) · [Changelog](CHANGELOG.md)

</div>

---

## Overview

Synapsys is an open-source Python library for modelling, simulating, and deploying control systems. It provides a **MATLAB-compatible API** that lowers the barrier for engineers already familiar with control toolboxes, while adding a modern **multi-agent simulation layer** with pluggable transports that scales from a single laptop to a distributed lab setup.

```python
from synapsys.api import tf, feedback, step, c2d

G  = tf([1], [1, 2, 1])      # G(s) = 1 / (s² + 2s + 1)
T  = feedback(G)              # closed-loop T = G / (1 + G)
t, y = step(T)                # step response

Gd = c2d(G, dt=0.02)         # ZOH discretisation at 50 Hz
```

---

## Features

| Feature | Description |
|---------|-------------|
| ⚡ **MATLAB-Compatible API** | `tf()`, `ss()`, `c2d()`, `step()`, `bode()`, `feedback()`, `lsim()` — same names, pure Python |
| 📐 **LTI Core** | `TransferFunction` and `StateSpace` with operator overloading, poles, zeros, stability |
| 🧮 **Control Algorithms** | Discrete PID with anti-windup · LQR via algebraic Riccati equation |
| 🤖 **Multi-Agent Simulation** | `PlantAgent` and `ControllerAgent` with FIPA ACL messaging, lock-step and wall-clock sync |
| 🔗 **Pluggable Transport** | Zero-copy shared memory (single-host) · ZeroMQ PUB/SUB and REQ/REP (distributed) |
| 🔌 **Hardware Abstraction** | `HardwareInterface` contract enables seamless MIL → SIL → HIL transitions |

---

## Installation

```bash
pip install synapsys
```

**Requirements:** Python ≥ 3.10, NumPy ≥ 1.24, SciPy ≥ 1.10, pyzmq ≥ 25.0

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

# ZOH discretisation
Gd = c2d(G, dt=0.02)          # 50 Hz
```

### 2 · Control algorithms

```python
from synapsys.algorithms import PID, lqr
import numpy as np

# Discrete PID with anti-windup
pid = PID(Kp=3.0, Ki=0.5, Kd=0.1, dt=0.01, u_min=-10.0, u_max=10.0)
u   = pid.compute(setpoint=5.0, measurement=y)

# LQR — solves the algebraic Riccati equation
A = np.array([[0., 1.], [-2., -3.]])
B = np.array([[0.], [1.]])
K, P = lqr(A, B, Q=np.eye(2), R=np.eye(1))
```

### 3 · Distributed simulation

Run plant and controller as independent processes connected by shared memory:

```bash
# Terminal 1 — physics engine
python examples/distributed/plant.py

# Terminal 2 — PID controller
python examples/distributed/controller.py
```

Or connect over a network using ZeroMQ:

```bash
python examples/distributed/plant_zmq.py
python examples/distributed/controller_zmq.py
```

### 4 · MIL → SIL → HIL — swap transport, keep algorithm

```python
# MIL (Model-in-the-Loop) — shared memory, single process
from synapsys.transport import SharedMemoryTransport
bus = SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True)

# SIL (Software-in-the-Loop) — ZeroMQ, cross-process / cross-machine
from synapsys.transport import ZMQTransport
bus = ZMQTransport("tcp://localhost:5555", mode="pub")

# HIL (Hardware-in-the-Loop) — real hardware driver
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
| [`distributed/plant_zmq.py`](examples/distributed/plant_zmq.py) | Same loop over ZeroMQ |
| [`advanced/01_custom_signals.py`](examples/advanced/01_custom_signals.py) | Custom reference signals with `lsim()` |
| [`advanced/02a_sil_plant.py`](examples/advanced/02a_sil_plant.py) | SIL plant process |
| [`advanced/03_realtime_scope.py`](examples/advanced/03_realtime_scope.py) | Text-mode real-time oscilloscope |
| [`advanced/04_realtime_matplotlib.py`](examples/advanced/04_realtime_matplotlib.py) | Live matplotlib oscilloscope with sinusoidal reference |
| [`advanced/05_digital_twin.py`](examples/advanced/05_digital_twin.py) | Digital twin with mechanical wear detection |
| [`quickstart.ipynb`](examples/quickstart.ipynb) | Interactive Jupyter notebook walkthrough |

---

## Architecture

```
synapsys/
├── api/            # MATLAB-compatible façade (tf, ss, c2d, step, bode, …)
├── core/           # LTI math — TransferFunction, StateSpace, LTIModel
├── algorithms/     # PID, LQR
├── agents/         # PlantAgent, ControllerAgent, HardwareAgent, SyncEngine
├── transport/      # SharedMemoryTransport, ZMQTransport, ZMQReqRepTransport
└── hw/             # HardwareInterface (abstract) + MockHardwareInterface
```

The transport layer is the key abstraction: agents communicate exclusively through a `TransportStrategy` interface. Swapping the concrete transport (shared memory ↔ ZMQ ↔ real hardware) requires changing **one line** at the call site — algorithms and agents are untouched.

---

## Testing

```bash
uv run pytest                          # run all tests
uv run pytest --cov=synapsys           # with coverage report
uv run mypy synapsys                   # type checking
uv run ruff check synapsys tests       # linting
```

| Metric | Value |
|--------|-------|
| Test suite | 69 tests |
| Coverage | 86 % |
| Type checking | mypy strict — 0 errors |
| Python versions | 3.10 · 3.11 · 3.12 |

---

## Roadmap

| Version | Planned features |
|---------|-----------------|
| **v0.1.0** | ✅ Current release — SISO LTI, PID, LQR, multi-agent, shared memory, ZMQ, hardware abstraction |
| **v0.2** | MIMO systems, `margin()`, `rlocus()`, `pole_placement()` |
| **v0.3** | State estimation — Kalman filter, Luenberger observer |
| **v0.5** | Real hardware drivers (serial, CAN, FPGA via PYNQ) |

See [CHANGELOG.md](CHANGELOG.md) for the full release history.

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
