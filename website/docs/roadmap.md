---
id: roadmap
title: Roadmap
sidebar_position: 99
---

# Roadmap

## Current state — v0.1.0

The foundation is complete and tested (40 tests, Python 3.10–3.12).

| Module | Status |
|--------|--------|
| `synapsys.core` — TransferFunction, StateSpace (continuous + discrete) | Done |
| `synapsys.algorithms` — PID (anti-windup), LQR | Done |
| `synapsys.agents` — PlantAgent, ControllerAgent, FIPA ACL, SyncEngine | Done |
| `synapsys.transport` — SharedMemory (zero-copy), ZMQ (PUB/SUB, REQ/REP) | Done |
| `synapsys.api` — tf(), ss(), c2d(), step(), bode(), feedback() | Done |
| `synapsys.hw` — Interface defined, no concrete implementations yet | Pending |

---

## v0.2 — Advanced analysis

**Core:**

- [ ] **MIMO systems** — `TransferFunction` and `StateSpace` for multiple inputs/outputs
- [ ] **Transport delay** — Pade approximation `pade(T, n)`
- [ ] **Phase and gain margin** — `margin(G)` returning $G_m$, $\phi_m$, $\omega_{gc}$, $\omega_{pc}$
- [ ] **Root locus** — `rlocus(G)` for root locus analysis
- [ ] **Pole placement** — `place(A, B, poles)` using Ackermann's algorithm

**Algorithms:**

- [ ] **PID in state space** — formulation with integrated Luenberger observer
- [ ] **LQI** — LQR with integral action for disturbance rejection

---

## v0.3 — Advanced control

- [ ] **MPC** — Model Predictive Control with sliding horizon and state/input constraints
- [ ] **Adaptive control** — MRAC (Model Reference Adaptive Control) for plants with varying parameters
- [ ] **Real-time reconfiguration** — swap the control law without stopping the simulation
- [ ] **Observers** — `ObserverAgent` with Kalman filter and Luenberger observer

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
