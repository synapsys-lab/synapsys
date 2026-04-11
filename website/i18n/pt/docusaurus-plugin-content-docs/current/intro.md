---
id: intro
title: Introdução
slug: /
---

# Synapsys

**Framework moderno de sistemas de controle em Python com simulação multiagente distribuída.**

Synapsys é uma alternativa compatível com MATLAB para engenheiros de controle que buscam:

- Uma **API Python limpa** que espelha a sintaxe do MATLAB/Simulink
- **Simulação distribuída** — planta e controlador rodando como processos independentes
- Comunicação de **ultra-baixa latência** via memória compartilhada (zero-copy) ou ZeroMQ
- Um **núcleo LTI sólido** que escala de malhas PID simples até arquiteturas CPS multiagente

---

## Funcionalidades

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

<Tabs>
  <TabItem value="core" label="Núcleo Matemático">

```python
from synapsys.api import tf, ss, step, bode, feedback, c2d

# Função de transferência — mesma sintaxe do MATLAB
G = tf([1], [1, 2, 1])        # G(s) = 1 / (s^2 + 2s + 1)

# Álgebra de blocos
T = feedback(G)                # T = G / (1 + G)
t, y = step(T)                 # resposta ao degrau
w, mag, ph = bode(G)           # diagrama de Bode

# Discretização ZOH
Gd = c2d(G, dt=0.05)
```

  </TabItem>
  <TabItem value="algorithms" label="Algoritmos">

```python
from synapsys.algorithms import PID, lqr

# PID discreto com anti-windup
pid = PID(Kp=3.0, Ki=0.5, Kd=0.1, dt=0.01,
          u_min=-10.0, u_max=10.0)
u = pid.compute(setpoint=5.0, measurement=y)

# LQR — resolve a equação algébrica de Riccati
K, P = lqr(A, B, Q, R)
```

  </TabItem>
  <TabItem value="distributed" label="Simulação Distribuída">

```python
from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

# Discretizar a planta
plant_d = c2d(ss([[-1]], [[1]], [[1]], [[0]]), dt=0.01)

# Cada processo tem seu próprio handle para o mesmo barramento
bus = SharedMemoryTransport("ctrl_bus", {"y": 1, "u": 1}, create=True)
t_plant = SharedMemoryTransport("ctrl_bus", {"y": 1, "u": 1})

agent = PlantAgent("planta", plant_d, t_plant, SyncEngine())
agent.start()   # thread em background, não-bloqueante
```

  </TabItem>
</Tabs>

---

## Instalação

```bash
pip install synapsys
```

Ou com [uv](https://docs.astral.sh/uv/):

```bash
uv add synapsys
```

---

## Status do Projeto

:::warning[Pré-Alpha]
O Synapsys está em desenvolvimento ativo. A API pode mudar entre versões.
:::

| Módulo | Status |
|--------|--------|
| `synapsys.core` — LTI, StateSpace, TransferFunction | Estável |
| `synapsys.algorithms` — PID, LQR | Estável |
| `synapsys.agents` — PlantAgent, ControllerAgent | Funcional |
| `synapsys.transport` — SharedMemory, ZMQ | Funcional |
| `synapsys.api` — camada MATLAB-compat | Estável |
| `synapsys.hw` — abstração de hardware | Interface apenas |
| MPC, controle adaptativo | Planejado |
| Editor gráfico de blocos | Planejado |
