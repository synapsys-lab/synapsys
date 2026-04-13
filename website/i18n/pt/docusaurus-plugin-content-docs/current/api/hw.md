---
id: hw
title: synapsys.hw — Hardware Abstraction
sidebar_position: 6
---

# synapsys.hw — Hardware Abstraction

Hardware abstraction layer for connecting Synapsys agents to physical devices (FPGAs, microcontrollers, PLCs) or in-process stubs for testing.

## HardwareInterface (Abstract Base Class)

Pluggable interface for bridging real hardware into the transport layer.
All concrete implementations must subclass `HardwareInterface` and implement
the four abstract methods below.

```python
from synapsys.hw import HardwareInterface
```

| Property / Method | Description |
|---|---|
| `n_inputs` *(property)* | Number of actuator channels (columns of `u`) |
| `n_outputs` *(property)* | Number of sensor channels (rows of `y`) |
| `connect() -> None` | Opens the hardware connection |
| `disconnect() -> None` | Closes the hardware connection |
| `read_outputs(timeout_ms=100) -> np.ndarray` | Reads sensor data from hardware |
| `write_inputs(u, timeout_ms=100) -> None` | Sends actuator command to hardware |

`HardwareInterface` also implements the context manager protocol (`__enter__` /
`__exit__`), so `with hw:` automatically calls `connect()` and `disconnect()`.

## MockHardwareInterface

In-process hardware stub for unit-testing and HIL demos **without physical
devices**.

```python
from synapsys.hw import MockHardwareInterface
```

```python
MockHardwareInterface(
    n_inputs: int,
    n_outputs: int,
    plant_fn: Callable[[np.ndarray], np.ndarray] | None = None,
    latency_ms: float = 0.0,
)
```

| Parameter | Description |
|---|---|
| `n_inputs` | Number of actuator channels |
| `n_outputs` | Number of sensor channels |
| `plant_fn` | `f(u) -> y` called on every `write_inputs`. Defaults to `y = u` when dimensions match, otherwise zeros |
| `latency_ms` | Artificial round-trip delay for jitter-tolerance testing |

**Example — first-order discrete plant:**

```python
from synapsys.hw import MockHardwareInterface
import numpy as np

state = [0.0]
def plant_fn(u):
    state[0] = 0.9 * state[0] + 0.1 * u[0]
    return np.array([state[0]])

hw = MockHardwareInterface(n_inputs=1, n_outputs=1, plant_fn=plant_fn)
with hw:
    hw.write_inputs(np.array([1.0]))
    y = hw.read_outputs()   # → approx [0.1]
```

## Planned implementations (v0.5)

| Class | Hardware |
|-------|----------|
| `SerialHardwareInterface` | ESP32, STM32 via UART |
| `OPCUAHardwareInterface` | PLCs, industrial SCADA (OPC-UA) |
| `FPGAHardwareInterface` | FPGA/FPAA low-latency co-simulation |
| `ROSTransport` | ROS 2 robotics bridge |

## Source

See [`synapsys/hw/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/hw) on GitHub.
