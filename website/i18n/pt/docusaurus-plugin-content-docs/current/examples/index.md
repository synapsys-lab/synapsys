---
id: examples-index
title: Examples
sidebar_position: 1
---

# Examples

A curated set of runnable examples that demonstrate the full capability spectrum of Synapsys — from a single `step()` call to a multi-process Digital Twin with anomaly detection.

Each example lives in its own subfolder under `examples/` and includes a detailed `README.md`.

---

## Basic

| Example | Concepts |
|---|---|
| [Step Response](./basic/step-response.md) | Transfer function, `tf()`, `step()`, poles, stability |

## Advanced

| Example | Concepts |
|---|---|
| [Custom Signal Injection](./advanced/custom-signals.md) | MIL, superposition, `simulate()`, arbitrary waveforms |
| [SIL + AI Controller](./advanced/sil-ai-controller.md) | SIL, `PlantAgent`, `ControllerAgent`, PyTorch integration, real-time plot |
| [Real-Time Scope (Terminal)](./advanced/realtime-scope.md) | Read-only bus monitor, headless display |
| [Real-Time Oscilloscope](./advanced/realtime-oscilloscope.md) | Three-role architecture, PID, sinusoidal reference, `FuncAnimation` |
| [Digital Twin](./advanced/digital-twin.md) | Virtual twin, wear injection, divergence metric, anomaly detection |

## Distributed

| Example | Concepts |
|---|---|
| [Shared Memory](./distributed/shared-memory.md) | Multi-process IPC, bus ownership, rate decoupling |
| [ZeroMQ Network](./distributed/zmq.md) | PUB/SUB, cross-machine simulation, ZOH fallback |

---

## Running any example

All examples use `uv`:

```bash
uv run python examples/<path>/<script>.py
```

Make sure dev dependencies are installed:

```bash
uv sync --extra dev
```
