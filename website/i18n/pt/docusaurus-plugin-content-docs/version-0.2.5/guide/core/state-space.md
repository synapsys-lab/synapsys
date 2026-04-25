---
id: state-space
title: Espaço de Estados
sidebar_position: 2
---

# Espaço de Estados

`StateSpace(A, B, C, D, dt=0.0)` representa um sistema LTI na forma matricial:

$$
\dot{x} = Ax + Bu
$$
$$
y = Cx + Du
$$

Para sistemas discretos (dt > 0):

$$
x(k+1) = Ax(k) + Bu(k)
$$
$$
y(k) = Cx(k) + Du(k)
$$

## Criacao

```python
import numpy as np
from synapsys.api import ss

# Pendulo invertido simplificado
A = np.array([[0, 1], [10, 0]])
B = np.array([[0], [1]])
C = np.eye(2)
D = np.zeros((2, 1))

sys = ss(A, B, C, D)
```

## Estabilidade

```python
print(sys.is_stable())   # False — polo em +sqrt(10)
print(sys.poles())       # [+3.16, -3.16]
```

## Resposta ao degrau e Bode

```python
t, y = sys.step()
w, mag, phase = sys.bode()
```

## Evolucao passo a passo (discreto)

Para simulação em tempo real dentro de agentes, use `evolve()`:

```python
from synapsys.api import ss, c2d
import numpy as np

sys_c = ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]])
sys_d = c2d(sys_c, dt=0.01)   # ZOH

x = np.array([0.0])
for _ in range(100):
    x, y = sys_d.evolve(x, np.array([1.0]))   # degrau unitario
```

## Conversão para função de transferencia

```python
G = sys.to_transfer_function()
```

## Álgebra

```python
sys_series   = sys1 * sys2
sys_parallel = sys1 + sys2
```

## Referência da API

Consulte a referência completa em [synapsys.core — StateSpace](/docs/api/core).
