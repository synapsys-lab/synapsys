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

Use `self._read(channel)` / `self._write(channel, data)` in subclasses — these helpers dispatch to either the `broker` or the legacy `transport`, whichever is set.

## PlantAgent

Simulates a discrete `StateSpace` plant in real time.

```python
PlantAgent(
    name: str,
    plant: StateSpace,
    transport: TransportStrategy | None,   # pass None when using broker
    sync: SyncEngine,
    channel_y: str = "y",
    channel_u: str = "u",
    x0: np.ndarray | None = None,
    *,
    broker: MessageBroker | None = None,   # recommended
)
```

## ControllerAgent

Applies a control law in real time.

```python
ControllerAgent(
    name: str,
    control_law: Callable[[np.ndarray], np.ndarray],
    transport: TransportStrategy | None,   # pass None when using broker
    sync: SyncEngine,
    channel_y: str = "y",
    channel_u: str = "u",
    *,
    broker: MessageBroker | None = None,   # recommended
)
```

## HardwareAgent

Bridges a physical (or mock) hardware device into the broker layer.
Replaces `PlantAgent` in a HIL (Hardware-in-the-Loop) setup — the real
device becomes the plant.

```python
HardwareAgent(
    name: str,
    hardware: HardwareInterface,
    transport: TransportStrategy | None,   # pass None when using broker
    sync: SyncEngine,
    channel_y: str = "y",
    channel_u: str = "u",
    timeout_ms: float = 100.0,
    *,
    broker: MessageBroker | None = None,   # recommended
)
```

Each tick: reads `y` from hardware → publishes `y` to broker → reads `u` from
broker → writes `u` to hardware. On `TimeoutError`, the last known `y`/`u`
are held (Zero-Order Hold) and a warning is logged.

```python
from synapsys.hw import MockHardwareInterface
from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend

topic_y = Topic("hw/y", shape=(1,))
topic_u = Topic("hw/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend("hil_bus", [topic_y, topic_u], create=True))
broker.publish("hw/y", np.zeros(1))
broker.publish("hw/u", np.zeros(1))

hw    = MockHardwareInterface(n_inputs=1, n_outputs=1)
sync  = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
agent = HardwareAgent(
    "hw_plant", hw, None, sync,
    channel_y="hw/y", channel_u="hw/u", broker=broker,
)

with hw:
    agent.start(blocking=False)
```

## Source

See [`synapsys/agents/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/agents) on GitHub.
