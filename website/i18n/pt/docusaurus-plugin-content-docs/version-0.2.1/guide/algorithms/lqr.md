---
id: lqr
title: LQR — Regulador Quadrático Linear
sidebar_position: 2
---

# LQR — Regulador Quadrático Linear

O LQR encontra o ganho de realimentação de estados $K$ que minimiza o custo quadrático:

$$J = \int_0^\infty \left( x^\top Q x + u^\top R u \right) dt$$

A solução e $u = -Kx$, onde $K = R^{-1} B^\top P$ e $P$ e a solução da **Equacao Algebrica de Riccati (ARE)**.

## Uso

```python
import numpy as np
from synapsys.algorithms import lqr
from synapsys.api import ss

# Pendulo invertido simplificado
A = np.array([[0, 1], [10, 0]])
B = np.array([[0], [1]])

Q = np.diag([10.0, 1.0])   # penaliza posicao mais que velocidade
R = np.array([[0.1]])       # penaliza esforco de controle

K, P = lqr(A, B, Q, R)
print(f"Ganho K: {K}")      # ex: [[-29.14, -7.61]]

# Verificar estabilidade da malha fechada
A_cl = A - B @ K
sys_cl = ss(A_cl, B, np.eye(2), np.zeros((2, 1)))
print(f"Estavel: {sys_cl.is_stable()}")   # True
```

## Ajuste de Q e R

| Objetivo | Ajuste |
|----------|--------|
| Resposta mais rápida | Aumentar $Q$ (penalizar erro de estado) |
| Menor esforco de atuacao | Aumentar $R$ |
| Priorizar um estado especifico | Aumentar elemento diagonal de $Q$ correspondente |

:::tip Regra de Bryson
Um ponto de partida clássico: $Q_{ii} = 1 / x_{i,max}^2$ e $R_{jj} = 1 / u_{j,max}^2$
:::

## Referência da API

Consulte a referência completa em [synapsys.algorithms — lqr](/docs/api/algorithms).
