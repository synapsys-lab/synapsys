---
id: roadmap
title: Roadmap
sidebar_position: 99
---

# Roadmap

## Current state — v0.2.2

The library is complete and tested (222 tests, Python 3.10–3.12, 90 % coverage).

| Module | Status |
|--------|--------|
| `synapsys.core` — TransferFunction, StateSpace, TransferFunctionMatrix (continuous + discrete) | Done |
| `synapsys.algorithms` — PID (anti-windup), LQR (Q/R validated) | Done |
| `synapsys.agents` — PlantAgent, ControllerAgent, HardwareAgent, FIPA ACL, SyncEngine | Done |
| `synapsys.broker` — MessageBroker, Topic, SharedMemoryBackend, ZMQBrokerBackend | Done |
| `synapsys.transport` — SharedMemory (zero-copy), ZMQ (PUB/SUB, REQ/REP) | Done |
| `synapsys.api` — tf(), ss(), c2d(), step(), bode(), feedback() (SISO + MIMO) | Done |
| `synapsys.viz` — 3D sim views: CartPoleView, PendulumView, MassSpringDamperView + Dark palette | Done |
| `synapsys.hw` — Interface defined, no concrete implementations yet | Pending |

---

## v0.1.0 ✅ — Foundation

- SISO LTI (`TransferFunction`, `StateSpace`), PID, LQR, multi-agent, shared memory, ZMQ, hardware abstraction.

## v0.2.0 ✅ — MIMO

- `TransferFunctionMatrix` — MIMO transfer-function matrix with operator algebra, `to_state_space()`, poles/zeros/stability.
- MIMO `feedback()` — state-space closed-loop for `StateSpace` and `TransferFunctionMatrix` plants.
- Transmission zeros via Rosenbrock system-matrix pencil.
- `lqr()` Q positive semi-definiteness validation.
- Covariant LTI type annotations for mypy/pyright.

---

## v0.2.x ✅ — 3D Visualization

- `synapsys.viz.palette` — `Dark` color tokens mirroring the website design system + `mpl_theme()`.
- `synapsys.viz.simview` — plug-and-play 3D + matplotlib windows: `CartPoleView`, `PendulumView`, `MassSpringDamperView`.
- `SimViewBase` template — auto-LQR, QTimer loop, keyboard capture, perturbation controls, hold-to-apply buttons.
- Pluggable controller interface: `CartPoleView(controller=my_fn).run()` accepts any callable (LQR, PID, PyTorch, SB3).

**Next simulators planned for `synapsys.viz.simview`:**
- [ ] `DoublePendulumView` — pêndulo duplo caótico
- [ ] `AcrobotView` — acrobot de 2 elos
- [ ] `QuadrotorView` — drone MIMO 12 estados (baseado no exemplo 06c)
- [ ] `BallBeamView` — bola sobre viga

---

## v0.3 — Advanced analysis

**Core:**

- [ ] **Transport delay** — Pade approximation `pade(T, n)`
- [ ] **Phase and gain margin** — `margin(G)` returning $G_m$, $\phi_m$, $\omega_{gc}$, $\omega_{pc}$
- [ ] **Root locus** — `rlocus(G)` for root locus analysis
- [ ] **Pole placement** — `place(A, B, poles)` using Ackermann's algorithm

**Algorithms:**

- [ ] **LQI** — LQR with integral action for disturbance rejection
- [ ] **Observers** — `ObserverAgent` with Kalman filter and Luenberger observer

---

## v0.4 — Advanced control

- [ ] **MPC** — Model Predictive Control with sliding horizon and state/input constraints
- [ ] **Adaptive control** — MRAC (Model Reference Adaptive Control) for plants with varying parameters
- [ ] **Real-time reconfiguration** — swap the control law without stopping the simulation

---

## v0.4 — Distributed infrastructure

- [ ] **OS semaphores** — protect `SharedMemoryTransport` against race conditions in multi-process
- [ ] **Cross-process lock-step barrier** — deterministic synchronisation using `multiprocessing.Barrier`
- [ ] **Distributed clock protocol** — coordinate $t_k$ between agents on different machines
- [ ] **Fault tolerance** — agent keeps running with ZOH when its peer disconnects

---

## v0.5 — Hardware

- [ ] **Serial/UART** — `SerialHardwareInterface` for microcontrollers (ESP32, STM32)
- [ ] **OPC-UA** — interface for PLCs and industrial SCADA systems
- [ ] **FPGA/FPAA** — low-latency interface for analogue-digital co-simulation
- [ ] **ROS 2 bridge** — `ROSTransport` for robotics integration

---

## v1.0 — Graphical interface

- [ ] **JSON netlist parser** — load a block diagram from a JSON/YAML file
- [ ] **REST API** — FastAPI exposing the simulation engine as a service
- [ ] **Web visual editor** — React frontend with React Flow for drag-and-drop block diagrams
- [ ] **Real-time scope** — WebSocket for streaming simulation data to the browser

---

## Long-term ideas

- **Antifragility** — algorithms that reconfigure and improve under perturbations
- **Digital twins** — continuous synchronisation between model and physical plant
- **Compilation to C** — export the control law to embedded C code
- **Julia integration** — bridge to high-performance ODE solvers
