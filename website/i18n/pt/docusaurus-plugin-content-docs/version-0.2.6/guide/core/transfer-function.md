---
id: transfer-function
title: Função de Transferencia
sidebar_position: 1
---

# Função de Transferencia

`TransferFunction(num, den, dt=0.0)` representa um sistema LTI por seus polinomios numerador e denominador no dominio de Laplace (continuo) ou Z (discreto).

## Criacao

```python
from synapsys.api import tf

# G(s) = (s + 2) / (s^2 + 3s + 2)
G = tf([1, 2], [1, 3, 2])

# Equivalente com construtor direto
from synapsys.core import TransferFunction
G = TransferFunction([1, 2], [1, 3, 2])
```

Para sistemas discretos, passe `dt`:

```python
# H(z) = 0.1 / (z - 0.9),  Ts = 10 ms
H = tf([0.1], [1, -0.9], dt=0.01)
print(H.is_discrete)   # True
```

## Polos, zeros e estabilidade

```python
G = tf([1, 2], [1, 3, 2])   # polos em -1 e -2

print(G.poles())             # [-1. -2.]
print(G.zeros())             # [-2.]
print(G.is_stable())         # True  (Re(polos) < 0)
```

## Álgebra de blocos

```python
from synapsys.api import tf, feedback, series, parallel

G = tf([10], [1, 1])
H = tf([1], [1, 0])   # integrador

# Serie: G * H
GH = series(G, H)    # equivalente a G * H

# Paralelo: G + H
GP = parallel(G, H)  # equivalente a G + H

# Realimentacao negativa unitaria: G / (1 + G)
T = feedback(G)

# Realimentacao com H no ramo de retorno
T2 = feedback(G, H)
```

Os operadores Python também funcionam:

```python
T = G * H      # serie
P = G + H      # paralelo
N = -G         # negacao
```

## Resposta ao degrau e Bode

```python
from synapsys.api import step, bode
import matplotlib.pyplot as plt

G = tf([1], [1, 2, 1])

t, y = step(G)
plt.plot(t, y)

w, mag, phase = bode(G)
```

## Referência da API

Consulte a referência completa em [synapsys.core — TransferFunction](/docs/api/core).
