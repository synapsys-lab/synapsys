---
slug: quadrotor-mimo-neural-lqr
title: "Controle MIMO de um Quadrotor com Neural-LQR"
description: >
  Como modelar um quadrotor linearizado de 12 estados, projetar um LQR MIMO,
  aumentá-lo com um MLP residual e simular a malha fechada em 3D — um estudo
  de caso de nível de pesquisa usando Synapsys.
authors: [oseias]
tags: [research, mimo, lqr, neural-lqr, simulation, python]
hide_table_of_contents: false
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<div align="center">

![Rastreamento 3D do Quadrotor](https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/examples/06_quadcopter_3d.gif)

</div>

Um quadrotor possui quatro rotores, seis graus de liberdade de corpo rígido e dinâmica
rotacional totalmente acoplada — é o benchmark MIMO da robótica aérea. Este post
percorre o pipeline completo de projeto: física → linearização → LQR → residual
Neural-LQR → simulação 3D.

{/* truncate */}

## Modelo em espaço de estados

A linearização de 12 estados em torno do equilíbrio de hover utiliza posição
$(x, y, z)$, velocidade $(\dot x, \dot y, \dot z)$, ângulos de Euler
$(\phi, \theta, \psi)$ e taxas angulares $(p, q, r)$.

```python
import numpy as np
from synapsys.api import ss, c2d
from synapsys.algorithms import lqr
from quadcopter_dynamics import build_matrices

A, B, C, D = build_matrices()    # A: 12×12, B: 12×4
planta = ss(A, B, C, D)

print(f"Estável: {planta.is_stable()}")  # False — integradores na posição
```

---

## Projeto LQR MIMO

```python
Q = np.diag([
    10.0, 10.0, 20.0,    # x, y, z
    1.0,  1.0,  1.0,     # ẋ, ẏ, ż
    20.0, 20.0, 10.0,    # φ, θ, ψ
    2.0,  2.0,  2.0,     # p, q, r
])
R = np.eye(4) * 0.5

K, P = lqr(A, B, Q, R)
print(f"Shape de K: {K.shape}")   # (4, 12)

A_cl = A - B @ K
print(f"Estável em malha fechada: {np.all(np.real(np.linalg.eigvals(A_cl)) < 0)}")
```

---

## Neural-LQR Residual

$$
u = -Ke + \underbrace{\text{MLP}(e)}_{\text{residual}}
$$

A camada de saída do MLP é **inicializada com zeros** — na inicialização, o
controlador é *exatamente* LQR. O residual adiciona correção apenas após treinamento,
garantindo estabilidade provável desde o início.

```python
import torch
import torch.nn as nn

class MLPResidual(nn.Module):
    def __init__(self, n_estados: int, n_entradas: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_estados, 64), nn.Tanh(),
            nn.Linear(64, 64),        nn.Tanh(),
            nn.Linear(64, n_entradas),
        )
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

    def forward(self, e: torch.Tensor) -> torch.Tensor:
        return self.net(e)

mlp = MLPResidual(n_estados=12, n_entradas=4)

def lei_neural_lqr(e: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        e_t = torch.tensor(e, dtype=torch.float32)
        return (-K @ e) + mlp(e_t).numpy()
```

---

## Simulação em malha fechada

```python
from synapsys.api import c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend

dt = 0.02
planta_d = c2d(planta, dt=dt)

topics = [Topic("quad/estado", shape=(12,)), Topic("quad/u", shape=(4,))]
broker = MessageBroker()
for t in topics:
    broker.declare_topic(t)
broker.add_backend(SharedMemoryBackend("quad_bus", topics, create=True))

ref = np.array([0, 0, 1.5, 0, 0, 0, 0, 0, 0, 0, 0, 0])

def lei(y: np.ndarray) -> np.ndarray:
    return lei_neural_lqr(ref - y)

sync = SyncEngine(SyncMode.LOCK_STEP, dt=dt)
PlantAgent("quad", planta_d, None, sync,
           channel_y="quad/estado", channel_u="quad/u", broker=broker).start(blocking=False)
ControllerAgent("ctrl", lei, None, sync,
                channel_y="quad/estado", channel_u="quad/u", broker=broker).start(blocking=True)
broker.close()
```

---

## Resultados

<div align="center">

![Telemetria do Quadrotor](https://raw.githubusercontent.com/synapsys-lab/synapsys/main/website/static/img/examples/06_quadcopter_telemetry.gif)

</div>

- **Erro de posição** < 0,08 m RMS após a primeira órbita
- **Ângulos de Euler** dentro de ±5° durante manobras agressivas
- **Entradas de controle** suaves — o custo do atuador em $R$ funcionou

O código completo está em
[`examples/advanced/06_quadcopter_mimo/`](https://github.com/synapsys-lab/synapsys/tree/main/examples/advanced/06_quadcopter_mimo).
