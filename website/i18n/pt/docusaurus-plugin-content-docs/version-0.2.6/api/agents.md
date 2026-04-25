---
id: agents
title: synapsys.agents
sidebar_position: 4
---

# synapsys.agents

Multi-agent infrastructure for distributed control simulation.

## Performative (Enum)

FIPA ACL performatives: `INFORM`, `REQUEST`, `AGREE`, `REFUSE`, `FAILURE`, `SUBSCRIBE`.

## ACLMessage

Structured message for inter-agent communication.

```python
ACLMessage(
    performative: Performative,
    sender: str,
    receiver: str,
    content: dict,
)
```

| Method | Description |
|--------|-------------|
| `reply(performative, content) -> ACLMessage` | Creates a reply message swapping sender/receiver |

## SyncMode (Enum)

- `WALL_CLOCK` — real-time execution, sleeps between ticks
- `LOCK_STEP` — advances only when `tick()` is called externally

## SyncEngine

Controls simulation time for an agent.

```python
SyncEngine(mode: SyncMode = SyncMode.WALL_CLOCK, dt: float = 0.01)
```

| Property / Method | Description |
|---|---|
| `mode` | The `SyncMode` this engine is running in |
| `dt` | Step size in seconds |
| `k` *(property)* | Current discrete step counter |
| `t` *(property)* | Simulation time in seconds: `k × dt` |
| `elapsed` *(property)* | Wall-clock seconds since the engine was created or last reset |
| `tick()` | Advances `k` by 1; blocks in `WALL_CLOCK` mode to maintain real-time pacing |
| `reset()` | Resets `k` to 0 and restarts the wall-clock reference |

## BaseAgent

Abstract base class. Subclass and override `setup()`, `step()`, and `teardown()`.

| Method | Description |
|--------|-------------|
| `start(blocking=True)` | Starts the simulation loop in the **current thread** (`True`) or a background daemon thread (`False`) |
| `stop()` | Signals the agent to stop after the current tick |

## PlantAgent

Simulates a discrete `StateSpace` plant in real time.

```python
PlantAgent(
    name: str,
    plant: StateSpace,
    transport: TransportStrategy,
    sync: SyncEngine,
    channel_y: str = "y",   # channel name for plant output
    channel_u: str = "u",   # channel name for control input
    x0: np.ndarray | None = None,
)
```

## ControllerAgent

Applies a control law in real time.

```python
ControllerAgent(
    name: str,
    control_law: Callable[[np.ndarray], np.ndarray],
    transport: TransportStrategy,
    sync: SyncEngine,
    channel_y: str = "y",   # channel name to read measurements from
    channel_u: str = "u",   # channel name to write control commands to
)
```

## HardwareAgent

Bridges a physical (or mock) hardware device into the transport layer.
Replaces `PlantAgent` in a HIL (Hardware-in-the-Loop) setup — the real
device becomes the plant.

```python
HardwareAgent(
    name: str,
    hardware: HardwareInterface,
    transport: TransportStrategy,
    sync: SyncEngine,
    channel_y: str = "y",      # channel to publish sensor measurements
    channel_u: str = "u",      # channel to read actuator commands from
    timeout_ms: float = 100.0, # per-call hardware I/O timeout
)
```

Each tick: reads `y` from hardware → writes `y` to transport → reads `u` from
transport → writes `u` to hardware. On `TimeoutError`, the last known `y`/`u`
are held (Zero-Order Hold) and a warning is logged.

```python
from synapsys.hw import MockHardwareInterface
from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

hw    = MockHardwareInterface(n_inputs=1, n_outputs=1)
bus   = SharedMemoryTransport("hil_bus", {"y": 1, "u": 1}, create=True)
sync  = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
agent = HardwareAgent("hw_plant", hw, bus, sync)

with hw:
    agent.start(blocking=False)
```

## Source

See [`synapsys/agents/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/agents) on GitHub.
