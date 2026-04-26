---
id: simulators-msd
title: Simulador Massa-Mola-Amortecedor
sidebar_label: Massa-Mola-Amortecedor
sidebar_position: 2
---

# Simulador Massa-Mola-Amortecedor

`MassSpringDamperSim` é o simulador de segunda ordem mais simples — um sistema linear
MMA de 1-DOF. É sempre estável para parâmetros positivos e serve como ponto de entrada
para compreender o `SimulatorBase`.

---

## Modelo físico

**Estados:** `x = [q, q̇]`
- `q` — deslocamento em relação ao repouso (m)
- `q̇` — velocidade (m/s)

**Entrada:** `u = [F]` — força aplicada (N)

**Saída:** `y = [q]` — posição apenas

**Dinâmica:**

```
m·q̈ + c·q̇ + k·q = F
```

---

## Construção

```python
from synapsys.simulators import MassSpringDamperSim

sim = MassSpringDamperSim(
    m=1.0,              # massa (kg)
    c=0.5,              # coeficiente de amortecimento (N·s/m)
    k=2.0,              # rigidez da mola (N/m)
    integrator="rk4",
    noise_std=0.0,
    disturbance_std=0.0,
)
```

---

## Resposta ao degrau

```python
import numpy as np

sim = MassSpringDamperSim()
sim.reset()

history = []
for _ in range(300):
    y, _ = sim.step(np.array([1.0]), dt=0.05)  # força constante
    history.append(y[0])

# deslocamento em regime permanente = F / k = 1,0 / 2,0 = 0,5 m
print(f"Regime permanente: {history[-1]:.4f} m")
```

---

## Validação da linearização

Como o MMA já é linear, `linearize()` deve retornar as matrizes analíticas conhecidas:

```python
ss = sim.linearize(np.zeros(2), np.zeros(1))
# A = [[0, 1], [-k/m, -c/m]]
# B = [[0], [1/m]]
# C = [[1, 0]]
# D = [[0]]
```

---

## Atualização de parâmetros thread-safe

```python
sim.set_params(m=2.0, k=5.0)   # aceitos: m, c, k
```
