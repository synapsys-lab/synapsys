---
id: simview
title: Guia de Uso — SimView
sidebar_label: Uso dos Simuladores
sidebar_position: 2
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Simuladores 3D — Guia de Uso

Este guia mostra como usar os três simuladores 3D da lib, desde o
caso mais simples (`CartPoleView().run()`) até customização de parâmetros físicos.

---

## Cart-Pole

Sistema clássico de controle: um carrinho sobre trilho com um pêndulo invertido
articulado. Estado de 4 dimensões, instável no equilíbrio vertical.

![CartPole — simulação 3D em tempo real](/img/simview/docs/cartpole.gif)

```python
from synapsys.viz import CartPoleView

CartPoleView().run()
```

**Parâmetros físicos (valores padrão):**

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `m_c` | `1.0` kg | massa do carrinho |
| `m_p` | `0.1` kg | massa do bob |
| `l` | `0.5` m | comprimento da haste |
| `g` | `9.81` m/s² | gravidade |

**Estado:** `x = [posição do carrinho, velocidade, ângulo θ, velocidade angular θ̇]`

**LQR padrão:** `Q = diag([1, 0.1, 100, 10])`, `R = 0.01·I`

**Estado inicial customizado:**

```python
import numpy as np
CartPoleView(x0=np.array([0.0, 0.0, 0.30, 0.0])).run()  # ângulo inicial 0.30 rad
```

:::note Auto-reset
O carrinho muda de cor para **âmbar** ao atingir 72% do trilho e para **vermelho** em 92%. Ao ultrapassar 92%, a simulação é resetada automaticamente.
:::

---

## Pêndulo Invertido

Pêndulo de 1 elo articulado numa base fixa. O sistema mais simples para testar
controladores — apenas 2 estados, polo instável em `+√(g/l)`.

![Pêndulo Invertido — simulação 3D em tempo real](/img/simview/docs/pendulum.gif)

```python
from synapsys.viz import PendulumView

PendulumView().run()
```

**Parâmetros físicos (valores padrão):**

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `m` | `1.0` kg | massa do bob |
| `l` | `1.0` m | comprimento da haste |
| `g` | `9.81` m/s² | gravidade |
| `b` | `0.1` | coeficiente de amortecimento viscoso |

**Estado:** `x = [θ, θ̇]`

**LQR padrão:** `Q = diag([80, 5])`, `R = I`

---

## Mass-Spring-Damper

Sistema massa-mola-amortecedor com rastreamento de setpoint.
O MSD tem controles extras na barra: botões para selecionar 3 posições
de referência (0 m, +1.5 m, −1.5 m) e atalhos de teclado 1/2/3.

![Mass-Spring-Damper — simulação 3D em tempo real](/img/simview/docs/msd.gif)

```python
from synapsys.viz import MassSpringDamperView

MassSpringDamperView().run()
```

**Parâmetros físicos (valores padrão):**

| Parâmetro | Padrão | Descrição |
|---|---|---|
| `m` | `1.0` kg | massa |
| `c` | `0.5` N·s/m | coeficiente de amortecimento |
| `k` | `2.0` N/m | constante da mola |

**Estado:** `x = [q, q̇]`

**Lei de controle LQR (com feed-forward de setpoint):**

```
u = −K·(x − x_ref) + k·sp
```

**Setpoints disponíveis (teclado):**

| Tecla | Setpoint |
|---|---|
| `1` | 0.0 m |
| `2` | +1.5 m |
| `3` | −1.5 m |

**Setpoints e estado inicial customizados:**

```python
import numpy as np
MassSpringDamperView(
    setpoints=[("0", 0.0), ("+2m", 2.0), ("-2m", -2.0)],
    x0=np.array([1.0, 0.0]),
).run()
```

---

## Anatomia da janela

```
┌──────────────────────────────────────────────────────────────────────┐
│  Título da janela                                                    │
├──────────────────────────────┬───────────────────────────────────────┤
│                              │  ┌─────────────────────────────────┐  │
│   PyVista 3D                 │  │  Posição / ângulo               │  │
│   • animação física          │  ├─────────────────────────────────┤  │
│   • HUD com valores          │  │  Velocidade / vel. angular      │  │
│     do estado em             │  ├─────────────────────────────────┤  │
│     tempo real               │  │  Força / torque de controle     │  │
│                              │  ├─────────────────────────────────┤  │
│   A/D=pert  R=reset          │  │  Retrato de fase                │  │
│   SPACE=pausa  Q=fechar      │  │  (ponto atual em ciano)         │  │
│                              │  └─────────────────────────────────┘  │
├──────────────────────────────┴───────────────────────────────────────┤
│  [◀ Perturbar]  [──●────── Magnitude: 20 N ──]  [Perturbar ▶]       │
│  [⏸ Pausa]  [↺ Reset]                                               │
├──────────────────────────────────────────────────────────────────────┤
│  t = 3.42 s  |  pos = +0.012 m  |  θ = −0.03°  |  rodando           │
└──────────────────────────────────────────────────────────────────────┘
```

| Região | O que mostra |
|---|---|
| Painel 3D (esquerda, ~55%) | Cena física animada + HUD de estado + indicações de teclado |
| Painel telemetria (direita, ~45%) | 4 gráficos matplotlib (atualização: CartPole ~17 Hz · Pêndulo/MSD ~20 Hz) |
| Barra de controles (80 px) | Perturbação hold-to-apply + slider + pausa/reset |
| Status bar | Tempo de simulação, variáveis principais, estado (rodando/PAUSADO) |

### Gráficos de telemetria por simulador

<Tabs>
  <TabItem value="cartpole" label="Cart-Pole">

| Painel | Conteúdo | Cor |
|---|---|---|
| 1 | Posição x(t) em m (eixo esq.) + Velocidade ẋ(t) em m/s (eixo dir.) | Azul + laranja tracejado |
| 2 | Ângulo da haste θ(t) em graus | Laranja |
| 3 | Força de controle u(t) em N | Vermelho |
| 4 | Retrato de fase (θ vs θ̇) | Violeta + ponto ciano |

  </TabItem>
  <TabItem value="pendulum" label="Pêndulo">

| Painel | Conteúdo | Cor |
|---|---|---|
| 1 | Ângulo θ(t) em graus | Azul |
| 2 | Velocidade angular θ̇(t) em °/s | Laranja |
| 3 | Torque de controle τ(t) em N·m | Vermelho |
| 4 | Retrato de fase (θ vs θ̇) | Violeta + ponto ciano |

  </TabItem>
  <TabItem value="msd" label="MSD">

| Painel | Conteúdo | Cor |
|---|---|---|
| 1 | Posição q(t) com setpoint | Azul + linha verde tracejada |
| 2 | Velocidade q̇(t) em m/s | Laranja |
| 3 | Força de controle u(t) em N | Vermelho |
| 4 | Retrato de fase (q vs q̇) | Violeta + ponto ciano |

  </TabItem>
</Tabs>

---

## Controles de teclado

| Tecla | Ação | Observação |
|---|---|---|
| `A` (hold) | Perturbação negativa | Liberando → perturbação volta a zero |
| `D` (hold) | Perturbação positiva | Liberando → perturbação volta a zero |
| `R` | Reset completo | Volta ao estado inicial, limpa histórico |
| `Space` | Pausa / Retomar | Alterna entre `⏸` e `▶` |
| `Q` / `Esc` | Fechar janela | Para o timer e fecha o PyVista |
| `1` / `2` / `3` | Mudar setpoint | **Apenas MSD** |

> Os atalhos funcionam independente de qual painel tem foco (3D ou matplotlib).

---

## Parâmetros físicos customizados

Todos os parâmetros físicos podem ser passados no construtor:

```python
from synapsys.viz import CartPoleView, PendulumView, MassSpringDamperView

# Carrinho pesado, haste longa
CartPoleView(m_c=3.0, m_p=0.5, l=1.0).run()

# Pêndulo curto com amortecimento maior
PendulumView(m=0.5, l=0.6, b=0.3).run()

# Mola mais rígida, amortecimento baixo (subamortecido)
MassSpringDamperView(m=1.0, c=0.1, k=10.0).run()
```

> Ao mudar os parâmetros físicos, o LQR automático é reprojetado internamente
> via `sim.linearize()` — nenhum ajuste manual necessário.

---

## Perturbações

Os botões `◀ Perturbar` e `Perturbar ▶` aplicam uma força/torque **enquanto
o botão está pressionado** (hold-to-apply). Ao soltar, a perturbação vai a zero.
Equivalente a segurar A ou D no teclado.

O **slider de magnitude** define o valor máximo da perturbação. Faixas por simulador:

| Simulador | Faixa | Padrão |
|---|---|---|
| Cart-Pole | 1–80 N | 30 N |
| Pêndulo | 1–40 N·m | 20 N·m |
| MSD | 1–30 N | 15 N |

---

## Paleta de cores

Todos os elementos visuais usam os tokens da paleta canônica.
Ver [tokens de cor `Dark` →](../../api/viz#dark)

```python
from synapsys.viz.palette import Dark, mpl_theme

mpl_theme()  # aplica tema escuro globalmente no matplotlib
```
