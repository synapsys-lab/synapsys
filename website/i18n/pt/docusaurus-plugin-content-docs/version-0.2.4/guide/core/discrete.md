---
id: discrete
title: Sistemas de Tempo Discreto
sidebar_position: 3
---

# Sistemas de Tempo Discreto

O Synapsys diferencia sistemas continuos e discretos pelo atributo `dt`:

| `dt` | Dominio | Estabilidade |
|------|---------|-------------|
| `0.0` (padrão) | Continuo — s | `Re(polos) < 0` |
| `> 0` | Discreto — z | `\|polos\| < 1` |

## Discretização (ZOH)

Use `c2d()` para converter um sistema continuo em discreto pelo método **Zero-Order Hold**:

```python
from synapsys.api import tf, ss, c2d

# Sistema continuo
G_c = tf([1], [1, 1])   # G(s) = 1/(s+1)

# Discretizar com Ts = 10 ms
G_d = c2d(G_c, dt=0.01)

print(G_d.is_discrete)   # True
print(G_d.dt)            # 0.01
print(G_d.poles())       # [exp(-0.01)] ≈ [0.990]
```

O mesmo funciona para `StateSpace`:

```python
import numpy as np
from synapsys.api import ss, c2d

sys_c = ss(np.array([[-1.0]]), np.array([[1.0]]),
           np.array([[1.0]]), np.array([[0.0]]))
sys_d = c2d(sys_c, dt=0.05)
```

## Resposta ao degrau discreta

```python
t, y = G_d.step(n=300)   # 300 amostras
```

Ou com tempo continuo equivalente:

```python
import numpy as np
t = np.arange(300) * G_d.dt
t_out, y_out = G_d.step(n=300)
```

## Simulação passo a passo

`StateSpace.evolve(x, u)` avanca um tick — o bloco basico para agentes em tempo real:

```python
x = np.zeros(sys_d.A.shape[0])
u = np.array([1.0])

for k in range(200):
    x, y = sys_d.evolve(x, u)
```

## Estabilidade discreta

```python
G_d = c2d(tf([1], [1, -0.5]), dt=0.1)
print(G_d.is_stable())   # |polo| < 1?
print(abs(G_d.poles()))
```

## Referência da API

Consulte a referência completa em [synapsys.core — StateSpace](/docs/api/core) e [synapsys.api — c2d](/docs/api/matlab-compat).
