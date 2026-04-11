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

| Method | Description |
|--------|-------------|
| `tick()` | Advances the clock by `dt` (blocks in WALL_CLOCK mode) |
| `elapsed` | Current simulation time in seconds |

## BaseAgent

Abstract base class. Subclass and override `setup()`, `step()`, and `teardown()`.

| Method | Description |
|--------|-------------|
| `start(blocking=True)` | Starts the simulation loop |
| `stop()` | Signals the agent to stop after the current tick |

## PlantAgent

Simulates a discrete `StateSpace` plant in real time.

```python
PlantAgent(
    name: str,
    plant: StateSpace,
    transport: TransportStrategy,
    sync: SyncEngine,
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
)
```

## Source

See [`synapsys/agents/`](https://github.com/synapsys/synapsys/tree/main/synapsys/agents) on GitHub.
