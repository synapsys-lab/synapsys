---
id: concepts
title: Multi-Agent Simulation — Concepts
sidebar_position: 1
---

# Multi-Agent Simulation — Concepts

Synapsys treats each simulation component (plant, controller, observer) as an **independent agent**. Agents communicate by messages, not function calls — which allows running each component in a separate process, thread, or machine.

## Why agents?

The monolithic model (everything in one script) is simple but has limitations:

- Hard to test components in isolation
- Does not scale to distributed systems (HIL, controller networks)
- Impossible to introduce realistic network delays between plant and controller

With agents:

```
[ PlantAgent ]  <->  [ SharedMemory / ZMQ ]  <->  [ ControllerAgent ]
   Process A              Data bus                     Process B
```

## FIPA ACL

Synapsys uses a subset of the **FIPA ACL** (Agent Communication Language) standard for structured messages between agents.

```python
from synapsys.agents import ACLMessage, Performative

msg = ACLMessage(
    performative=Performative.INFORM,
    sender="plant",
    receiver="controller",
    content={"y": 3.14},
)

reply = msg.reply(Performative.REQUEST, content={"u": 1.5})
```

| Performative | Meaning |
|---|---|
| `INFORM` | Reports a fact (e.g. plant state) |
| `REQUEST` | Requests an action (e.g. compute u) |
| `AGREE` | Accepts a request |
| `REFUSE` | Declines a request |
| `FAILURE` | Reports a failed execution |
| `SUBSCRIBE` | Requests periodic updates |

## Synchronisation

The `SyncEngine` controls how time advances inside each agent.

```python
from synapsys.agents import SyncEngine, SyncMode

# Wall-clock: runs in real time, sleeps to pace ticks
sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=0.01)   # 100 Hz

# Lock-step: advances only when explicitly called (deterministic)
sync = SyncEngine(mode=SyncMode.LOCK_STEP, dt=0.01)
```

### Wall-clock vs lock-step

| | WALL_CLOCK | LOCK_STEP |
|---|---|---|
| **Speed** | Real time (limited by dt) | As fast as possible |
| **Synchrony** | Each agent at its own rate | Coupled by external barrier |
| **Network delay** | Simulated naturally | Transparent |
| **Reproducibility** | Non-deterministic | Deterministic |
| **Use case** | Robustness tests, HIL | Mathematical validation |

## Agent lifecycle

```
          start()
             |
          setup()          <- initialise resources
             |
    +--------+---------+
    |  while running:  |
    |    step()        |   <- one simulation tick
    |    sync.tick()   |   <- advance the clock
    +--------+---------+
             |
         teardown()        <- release resources
```

The transport is **not closed** by the agent — its lifecycle is managed by the code that created the agent.
