---
id: hw
title: synapsys.hw — Hardware Abstraction
sidebar_position: 6
---

# synapsys.hw — Hardware Abstraction

:::note[Interface only]
This module defines the hardware abstraction interface. No concrete implementations exist yet — they are planned for v0.5.
:::

## HardwareInterface (Abstract Base Class)

Pluggable interface for connecting Synapsys agents directly to physical hardware (FPGA, microcontrollers, PLCs).

| Method | Description |
|--------|-------------|
| `read() -> np.ndarray` | Reads sensor data from hardware |
| `write(u: np.ndarray) -> None` | Sends control signal to hardware |
| `open() -> None` | Initialises the hardware connection |
| `close() -> None` | Closes the hardware connection |

## Planned implementations (v0.5)

| Class | Hardware |
|-------|----------|
| `SerialHardwareInterface` | ESP32, STM32 via UART |
| `OPCUAHardwareInterface` | PLCs, industrial SCADA (OPC-UA) |
| `FPGAHardwareInterface` | FPGA/FPAA low-latency co-simulation |
| `ROSTransport` | ROS 2 robotics bridge |

## Source

See [`synapsys/hw/base.py`](https://github.com/synapsys-lab/synapsys/blob/main/synapsys/hw/base.py) on GitHub.
