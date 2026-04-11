# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-04-11

### Added

#### Core LTI Systems
- `TransferFunction` — SISO transfer function with full operator overloading (`+`, `*`, `/`, negation), poles, zeros, stability check, step response, and Bode diagram.
- `StateSpace` — continuous and discrete state-space models with `evolve()` for real-time simulation, pole/zero extraction, stability, step response, and Bode diagram.
- Operator interoperability between `TransferFunction` and `StateSpace` via the `LTIModel` abstract base class.

#### MATLAB-Compatible API (`synapsys.api`)
- `tf(num, den)` — construct a transfer function.
- `ss(A, B, C, D)` — construct a state-space model.
- `c2d(sys, dt, method)` — continuous-to-discrete conversion (ZOH, bilinear/Tustin, Euler forward, backward-diff).
- `step(sys)` — compute step response; returns `(t, y)`.
- `bode(sys)` — compute frequency response; returns `(omega, mag, phase)`.
- `feedback(P, C)` — unity or custom negative feedback interconnection.
- `series(G1, G2)` — series connection.
- `parallel(G1, G2)` — parallel connection.

#### Control Algorithms (`synapsys.algorithms`)
- `PID` — discrete PID controller with anti-windup (back-calculation), output saturation, and `reset()`.
- `lqr(A, B, Q, R)` — continuous-time LQR solver via the algebraic Riccati equation; returns gain matrix `K` and cost matrix `P`.

#### Multi-Agent Simulation (`synapsys.agents`)
- `BaseAgent` — abstract lifecycle agent (setup → step loop → teardown) backed by a daemon thread.
- `PlantAgent` — simulates a discrete `StateSpace` plant in real time, publishing `y` and consuming `u` each tick.
- `ControllerAgent` — executes an arbitrary control law `Callable[[ndarray], ndarray]` (PID, LQR, neural net, …) each tick.
- `SyncEngine` — two synchronisation modes: `LOCK_STEP` (barrier-based) and `WALL_CLOCK` (fixed-rate wall time).
- `ACLMessage` / `Performative` — lightweight FIPA ACL message structure for agent communication.

#### Transport Layer (`synapsys.transport`)
- `SharedMemoryTransport` — zero-copy IPC via OS shared memory (`multiprocessing.shared_memory`); supports multiple named channels in a single block.
- `ZMQTransport` — asynchronous PUB/SUB transport over ZeroMQ for distributed (multi-machine) simulation.
- `ZMQReqRepTransport` — synchronous REQ/REP transport for lock-step coordination over the network.
- `TransportStrategy` — abstract interface; implement to plug in custom transports (serial, OPC-UA, ROS 2, …).

#### Hardware Abstraction (`synapsys.hw`)
- `HardwareInterface` — abstract interface for FPGA, FPAA, and microcontroller backends (implementations planned for v0.5).

### Known Limitations

- **SISO only** — `TransferFunction` and `StateSpace` assume a single input and single output. MIMO support is planned for v0.2.
- **No advanced frequency-domain tools** — `margin()`, `rlocus()`, `pole_placement()`, and Padé delay approximation are not yet implemented (v0.2).
- **No state estimation** — Kalman filter and Luenberger observer are planned for v0.3.
- **No hardware implementations** — `HardwareInterface` subclasses for real hardware are planned for v0.5.
- **Race-condition caveat** — `SharedMemoryTransport` has no internal mutex; architect channels so that each process is the sole writer of its own channel.

[0.1.0]: https://github.com/synapsys/synapsys/releases/tag/v0.1.0
