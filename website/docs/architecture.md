---
id: architecture
title: Architecture
sidebar_position: 3
---

# Architecture

Synapsys is built in **seven layers**. Each layer has a single responsibility and depends only on the layers below. This means you can use the mathematical core alone without touching the agent infrastructure, or swap the transport backend without changing any control logic.

## Layer diagram

```mermaid
%%{init: {'theme': 'dark'}}%%
flowchart TB
    subgraph UserAPI["1. Public API — synapsys.api"]
        direction LR
        UI1["matlab_compat.py\ntf(), ss(), c2d(), step(), bode()"]
        UI2["agent_api.py\nPlantAgent(), ControllerAgent()"]
    end

    subgraph CoreMath["2. Math Engine — synapsys.core"]
        direction TB
        M1["LTIModel (ABC)"]
        M2["StateSpace"]
        M3["TransferFunction"]
        M5["TransferFunctionMatrix"]
        M4["NumPy / SciPy solvers"]
        M1 --> M2
        M1 --> M3
        M1 --> M5
        M2 --> M4
        M3 --> M4
        M5 --> M3
    end

    subgraph ControlLogic["3. Algorithms — synapsys.algorithms"]
        direction LR
        C1["Classical: PID, LQR"]
        C2["Advanced: MPC, Adaptive (planned)"]
        C3["Runtime reconfiguration (planned)"]
    end

    subgraph MAS["4. Multi-Agent System — synapsys.agents"]
        direction TB
        A1["FIPA ACL Messages\nINFORM, REQUEST, ..."]
        A2["SyncEngine\nWALL_CLOCK / LOCK_STEP"]
        A3["BaseAgent → PlantAgent, ControllerAgent, HardwareAgent"]
    end

    subgraph BrokerLayer["5. Broker — synapsys.broker"]
        direction TB
        B1["MessageBroker\nMediator / router"]
        B2["Topic\nTyped, shaped signal descriptor"]
        B3["SharedMemoryBackend\nZMQBrokerBackend"]
        B1 --> B2
        B1 --> B3
    end

    subgraph Transport["6. Transport — synapsys.transport"]
        direction TB
        T1{"TransportStrategy (ABC)"}
        T2["SharedMemoryTransport\nZero-copy IPC"]
        T3["ZMQTransport / ZMQReqRepTransport\nTCP network"]
        T1 --> T2
        T1 --> T3
    end

    subgraph Hardware["7. Hardware — synapsys.hw"]
        direction LR
        H1["HardwareInterface (ABC)"]
        H2["FPGA / FPAA (planned)"]
        H3["Microcontrollers (planned)"]
    end

    UserAPI ==> CoreMath
    UserAPI ==> MAS
    CoreMath ==> ControlLogic
    MAS ==> BrokerLayer
    BrokerLayer ==> Transport
    Transport -.-> Hardware
    ControlLogic -.-> MAS
```

## Design decisions

### API / math engine separation

The `synapsys.api` layer is a convenience wrapper only. All mathematics lives in `synapsys.core`. This allows the API to evolve without touching the numerical core.

### LTI class operator overloading

`G1 * G2` (series), `G1 + G2` (parallel), and `G.feedback()` allow composing systems with natural block algebra:

```python
T = (C * G).feedback()   # closed loop: C in series with G
```

`TransferFunctionMatrix` extends this algebra to MIMO plants: `*` performs matrix multiplication (series) and `+` is element-wise (parallel). Simulation and analysis delegate to a minimal `StateSpace` realisation built lazily by `to_state_space()`.

### Broker as mediator

`PlantAgent`, `ControllerAgent`, and `HardwareAgent` do not know **how** data is sent. They call `self._read(channel)` and `self._write(channel, data)`, which dispatch to the `MessageBroker` injected at construction time. The broker routes each channel to the appropriate backend (`SharedMemoryBackend`, `ZMQBrokerBackend`, or a custom one) — no control logic changes needed.

This mediator pattern enables **many-to-many topologies**: a `ControllerAgent` can simultaneously receive plant output (`plant/y`) and live parameter updates from a `ReconfigAgent` (`ctrl/config`) through the same broker instance.

### Transport lifecycle

The transport backend is **owned by the caller** via the `MessageBroker`. Agents never call `backend.close()` directly. This prevents double-free when multiple agents share views of the same memory block. Always call `broker.close()` in a `finally` block or at program exit.

### Continuous vs discrete

`StateSpace(A, B, C, D, dt=0)` is continuous. `dt > 0` is discrete. The same class supports both:

- `is_stable()` uses `Re(poles) < 0` for continuous and `|poles| < 1` for discrete
- `step()` delegates to `scipy.signal.step` or `scipy.signal.dstep` automatically
- `evolve(x, u)` executes `x(k+1) = Ax + Bu` step by step for real-time simulation
