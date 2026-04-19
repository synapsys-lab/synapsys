---
slug: mil-sil-hil-deployment-controle
title: "Do Modelo ao Hardware: MIL → SIL → HIL em Três Etapas"
description: >
  Um guia prático para o fluxo de desenvolvimento MIL/SIL/HIL com Synapsys —
  troque da simulação para o hardware real mudando uma linha, mantendo seu
  algoritmo de controle intacto.
authors: [oseias]
tags: [tutorial, sil, hil, simulation, python, control-theory]
hide_table_of_contents: false
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<div align="center">

![SIL Neural-LQR](https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/examples/03_sil_ai_controller.gif)

</div>

**MIL → SIL → HIL** é a progressão padrão do modelo-V para controle embarcado: simule
tudo primeiro, depois substitua o modelo da planta por hardware real uma camada de cada
vez. Com Synapsys, a transição é uma **troca de uma linha** porque a camada de transporte
é totalmente abstraída do algoritmo.

{/* truncate */}

## As três etapas

| Etapa | Planta | Controlador | Transporte | Objetivo |
|-------|--------|-------------|-----------|---------|
| **MIL** | Simulada (`StateSpace`) | Código do algoritmo | Memória compartilhada | Iteração rápida, testes unitários |
| **SIL** | Simulada | Binário compilado / processo externo | ZeroMQ | Testes de integração, perfil de latência |
| **HIL** | Dispositivo real | Código do algoritmo ou firmware MCU | `HardwareInterface` | Testes de aceitação na planta real |

---

## Etapa 1 — MIL: tudo em um processo

```python
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import SharedMemoryTransport
import numpy as np

planta_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)
pid = PID(Kp=4.0, Ki=1.0, dt=0.01)

def lei(y: np.ndarray) -> np.ndarray:
    return np.array([pid.compute(setpoint=3.0, measurement=y[0])])

with SharedMemoryTransport("demo", {"y": 1, "u": 1}, create=True) as bus:
    bus.write("y", np.zeros(1))
    bus.write("u", np.zeros(1))
    sync = SyncEngine(SyncMode.LOCK_STEP, dt=0.01)
    PlantAgent("planta", planta_d, bus, sync).start(blocking=False)
    ControllerAgent("ctrl", lei, bus, sync).start(blocking=True)
```

---

## Etapa 2 — SIL: dois processos via ZeroMQ

A função `lei` **não muda**. Apenas o transporte é trocado:

<Tabs>
<TabItem value="plant" label="processo_planta.py">

```python
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.transport import ZMQTransport

planta_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)
pub = ZMQTransport("tcp://*:5555", mode="pub")
sub = ZMQTransport("tcp://localhost:5556", mode="sub")
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
PlantAgent("planta", planta_d, pub, sync, sub_transport=sub).start(blocking=True)
```

</TabItem>
<TabItem value="ctrl" label="processo_controlador.py">

```python
from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import ZMQTransport
import numpy as np

pid = PID(Kp=4.0, Ki=1.0, dt=0.01)

def lei(y: np.ndarray) -> np.ndarray:
    return np.array([pid.compute(setpoint=3.0, measurement=y[0])])

sub = ZMQTransport("tcp://localhost:5555", mode="sub")
pub = ZMQTransport("tcp://*:5556", mode="pub")
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
ControllerAgent("ctrl", lei, sub, sync, pub_transport=pub).start(blocking=True)
```

</TabItem>
</Tabs>

---

## Etapa 3 — HIL: hardware real

```python
from synapsys.agents import HardwareAgent, SyncEngine, SyncMode
from synapsys.hw import HardwareInterface
from synapsys.transport import ZMQTransport
import numpy as np

class MinhaInterfaceDAQ(HardwareInterface):
    def __init__(self):
        super().__init__(n_inputs=1, n_outputs=1)

    def read_outputs(self, timeout_ms: float = 100.0) -> np.ndarray:
        # return np.array([self.daq.read_channel(0)])
        return np.array([0.0])   # stub

    def write_inputs(self, u: np.ndarray, timeout_ms: float = 100.0) -> None:
        # self.daq.write_channel(0, float(u[0]))
        pass

sub = ZMQTransport("tcp://localhost:5556", mode="sub")
pub = ZMQTransport("tcp://*:5555", mode="pub")
sync = SyncEngine(SyncMode.WALL_CLOCK, dt=0.01)
HardwareAgent("hw", MinhaInterfaceDAQ(), pub, sync, sub_transport=sub).start(blocking=True)
```

O processo controlador **não muda**. A troca é cirúrgica.

---

## Resumo

| Etapa | O que muda |
|-------|-----------|
| MIL → SIL | `SharedMemoryTransport` → `ZMQTransport`, dividir em dois processos |
| SIL → HIL | `PlantAgent` → `HardwareAgent(MinhaInterfaceDAQ())` |
| Algoritmo de controle | **Não muda** |

Veja o exemplo SIL completo em
[`examples/advanced/02_sil_ai_controller/`](https://github.com/synapsys-lab/synapsys/tree/main/examples/advanced/02_sil_ai_controller).
