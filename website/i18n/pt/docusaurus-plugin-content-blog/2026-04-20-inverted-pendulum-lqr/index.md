---
slug: pendulo-invertido-lqr
title: "Estabilizando um Pêndulo Invertido com LQR"
description: >
  Um guia completo: derive o modelo linearizado em espaço de estados de um pêndulo
  invertido, projete um controlador LQR, simule a resposta em malha fechada e
  discretize para deployment embarcado — tudo em Python com Synapsys.
authors: [oseias]
tags: [tutorial, lqr, control-theory, simulation, python]
hide_table_of_contents: false
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

O pêndulo invertido é o benchmark canônico do controle não-linear — instável, simples
o suficiente para modelar analiticamente, mas rico o suficiente para revelar todo o
fluxo de projeto LQR. Este post deriva o modelo linearizado a partir da física e mostra
como estabilizá-lo com Synapsys em poucas dezenas de linhas de Python.

{/* truncate */}

## Física e linearização

Uma haste rígida de massa $m$ e comprimento $L$ é articulada em um carrinho.
Seja $\theta$ o ângulo em relação à vertical. Linearizando em torno de $\theta = 0$:

$$
\ddot{\theta} = \frac{g}{L}\theta - \frac{1}{mL^2}u
$$

Escolhendo o vetor de estados $x = [\theta,\; \dot{\theta}]^\top$ e a força do carrinho $u$:

$$
\dot{x} = \underbrace{\begin{bmatrix}0 & 1 \\ g/L & 0\end{bmatrix}}_{A}\, x
         + \underbrace{\begin{bmatrix}0 \\ -1/(mL^2)\end{bmatrix}}_{B}\, u,
\qquad
y = \begin{bmatrix}1 & 0\end{bmatrix} x
$$

Para $m = 0,5$ kg, $L = 0,3$ m, $g = 9,81$ m/s²:

```python
import numpy as np
from synapsys.api import ss

m, L, g = 0.5, 0.3, 9.81

A = np.array([[0,      1   ],
              [g/L,    0   ]])
B = np.array([[0           ],
              [-1/(m*L**2) ]])
C = np.array([[1, 0]])
D = np.zeros((1, 1))

planta = ss(A, B, C, D)
print(planta.is_stable())      # False — polos em ±√(g/L) = ±5,72 rad/s
```

---

## Projeto LQR

O LQR encontra o ganho de realimentação de estados $K$ que minimiza:

$$
J = \int_0^\infty \left(x^\top Q\, x + u^\top R\, u\right)\mathrm{d}t
$$

**$Q$ grande** penaliza erro de estado (rápido, agressivo). **$R$ grande** penaliza
esforço de controle (lento, conservador):

```python
from synapsys.algorithms import lqr

Q = np.diag([100.0, 1.0])   # penaliza ângulo pesadamente
R = np.array([[0.1]])

K, P = lqr(A, B, Q, R)
print(f"K = {K}")            # K = [[33.2  5.8]]

A_cl = A - B @ K
print(np.linalg.eigvals(A_cl))   # autovalores no semiplano esquerdo
```

---

## Simulação

```python
from synapsys.api import c2d
import matplotlib.pyplot as plt

cl = ss(A_cl, B, C, D)

t = np.linspace(0, 3, 600)
x0 = np.array([0.2, 0.0])       # θ₀ = 0,2 rad (≈ 11°)
u_zero = np.zeros((len(t), 1))
t_out, y = cl.simulate(t, u_zero, x0=x0)

plt.plot(t_out, y)
plt.xlabel("Tempo (s)"); plt.ylabel("θ (rad)")
plt.title("Pêndulo Invertido — estabilização LQR de θ₀ = 0,2 rad")
plt.grid(True); plt.show()
```

O ângulo retorna a zero em aproximadamente 1,5 s sem sobressinal.

---

## Discretização para deployment embarcado

```python
dt = 0.01  # 100 Hz
planta_d = c2d(planta, dt=dt)

# Redesenhar K no tempo discreto
K_d, _ = lqr(planta_d.A, planta_d.B, Q, R)

# Laço de controle embarcado
x = np.zeros(2)
for _ in range(n_steps):
    u = -K_d @ x
    x, y = planta_d.evolve(x, u)
```

---

## Resumo das APIs

| Etapa | API Synapsys |
|-------|-------------|
| Modelagem | `ss(A, B, C, D)` |
| Verificação de estabilidade | `planta.is_stable()`, `planta.poles()` |
| Projeto LQR | `lqr(A, B, Q, R)` → retorna `(K, P)` |
| Simulação | `cl.simulate(t, u, x0=x0)` |
| Discretização | `c2d(planta, dt=0.01)` |
| Laço embarcado | `planta_d.evolve(x, u)` |

O notebook completo está em [`examples/quickstart_en.ipynb`](https://github.com/synapsys-lab/synapsys/blob/main/examples/quickstart_en.ipynb).
