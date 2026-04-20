---
id: shared-memory
title: Transporte por Memória Compartilhada
sidebar_position: 2
---

# Transporte por Memória Compartilhada

`SharedMemoryTransport` usa o mecanismo de **memória compartilhada do SO** (`multiprocessing.shared_memory`) para comunicação **zero-copy** entre processos na mesma máquina.

Os dados são escritos diretamente em endereços de RAM física mapeados como arrays NumPy. Sem serialização, sem copia — apenas um ponteiro para o mesmo endereço.

## Como funciona

```
Processo A (planta)           RAM Fisica               Processo B (controlador)
─────────────────────    ┌──────────────────────┐    ──────────────────────────
bus._buf -> array  ─────▶│  [y0, y1, ..., u0]  │◀────── bus._buf -> array
                         └──────────────────────┘
                              "ctrl_bus" (nome OS)
```

## Uso

```python
from synapsys.transport import SharedMemoryTransport
import numpy as np

CHANNELS = {
    "y": 2,    # saida da planta — 2 floats
    "u": 1,    # sinal de controle — 1 float
}

# Processo owner: cria o bloco (create=True)
owner = SharedMemoryTransport("ctrl_bus", CHANNELS, create=True)
owner.write("y", np.array([0.0, 0.0]))
owner.write("u", np.array([0.0]))

# Outros processos: conectam pelo nome
client = SharedMemoryTransport("ctrl_bus", CHANNELS)
y = client.read("y")
```

:::warning Owner e responsavel pelo unlink
Apenas o processo `create=True` libera a memória no SO ao fechar. Os clientes chamam apenas `close()`.
:::

## Múltiplos agentes no mesmo bloco

```python
t_plant = SharedMemoryTransport("ctrl_bus", CHANNELS)
t_ctrl  = SharedMemoryTransport("ctrl_bus", CHANNELS)

plant_agent = PlantAgent(..., transport=t_plant, ...)
ctrl_agent  = ControllerAgent(..., transport=t_ctrl, ...)
```

:::danger Race conditions
Não ha mutex na implementação atual. Arquitete seus canais para que cada processo seja o único escritor do seu canal.
:::

## Referência da API

Consulte a referência completa em [synapsys.transport — SharedMemoryTransport](/docs/api/transport).
