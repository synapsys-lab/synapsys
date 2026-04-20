---
id: plant-agent
title: PlantAgent
sidebar_position: 2
---

# PlantAgent

`PlantAgent` simula uma **planta discreta** (`StateSpace` com `dt > 0`) em tempo real, publicando `y` e consumindo `u` a cada tick.

## Requisitos

- A planta deve ser discreta. Use `c2d()` para discretizar uma planta continua.
- O transporte deve ter dois canais: um para `y` (saida) e um para `u` (entrada).

## Exemplo completo

```python
import numpy as np
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

# 1. Definir e discretizar a planta
plant_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])   # G(s) = 1/(s+1)
plant_d = c2d(plant_c, dt=0.01)                      # ZOH, 100 Hz

# 2. Criar o barramento de memoria compartilhada
BUS = "minha_simulacao"
CHANNELS = {"y": 1, "u": 1}

owner = SharedMemoryTransport(BUS, CHANNELS, create=True)
owner.write("u", np.array([0.0]))
owner.write("y", np.array([0.0]))

# 3. Cada agente tem seu proprio handle
t_plant = SharedMemoryTransport(BUS, CHANNELS)

sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
agent = PlantAgent("planta", plant_d, t_plant, sync)

# 4. Iniciar em background
agent.start(blocking=False)

agent.stop()
t_plant.close()
owner.close()
```

## Estado inicial

```python
x0 = np.array([2.0])    # estado inicial nao-zero
agent = PlantAgent("planta", plant_d, transport, sync, x0=x0)
```

## Referência da API

Consulte a referência completa em [synapsys.agents — PlantAgent](/docs/api/agents).
