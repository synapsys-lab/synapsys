---
id: simulators-inverted-pendulum
title: Simulador Pêndulo Invertido
sidebar_label: Pêndulo Invertido
sidebar_position: 3
---

# Simulador Pêndulo Invertido

`InvertedPendulumSim` implementa um pêndulo invertido não-linear em pivô fixo —
o sistema intrinsecamente instável mais simples e um benchmark clássico para
projeto de controladores.

---

## Modelo físico

**Estados:** `x = [θ, θ̇]`
- `θ` — ângulo em relação à vertical (rad, θ=0 → equilibrado)
- `θ̇` — velocidade angular (rad/s)

**Entrada:** `u = [τ]` — torque no pivô (N·m)

**Saída:** `y = [θ]` — ângulo da haste apenas

**Dinâmica não-linear:**

```
I = m · l²
θ̈ = (g/l) · sin(θ) − (b/I) · θ̇ + τ/I
```

**Polo instável** (b=0): `λ_instável = +√(g/l)`

---

## Construção

```python
from synapsys.simulators import InvertedPendulumSim

sim = InvertedPendulumSim(
    m=1.0,              # massa do pêndulo (kg)
    l=1.0,              # comprimento do pêndulo (m)
    g=9.81,             # gravidade (m/s²)
    b=0.0,              # coeficiente de atrito (N·m·s/rad)
    integrator="rk4",
    noise_std=0.0,
    disturbance_std=0.0,
)
```

---

## Estabilização por LQR

```python
import numpy as np
from synapsys.algorithms.lqr import lqr

sim = InvertedPendulumSim(m=1.0, l=1.0, g=9.81, b=0.1)
sim.reset()
ss = sim.linearize(np.zeros(2), np.zeros(1))

K, _ = lqr(ss.A, ss.B, np.diag([10.0, 1.0]), np.eye(1))

sim.reset(x0=np.array([0.1, 0.0]))
for _ in range(1000):
    x = sim.state
    u = -K @ x
    y, info = sim.step(u, dt=0.01)
    if info["failed"]:
        break
```

---

## Detecção de falha

`info["failed"]` é `True` quando `|θ| > π/2 rad` (haste ultrapassou a horizontal).

---

## Utilitários

```python
# Polo instável em malha aberta (teórico)
sim.unstable_pole()   # ≈ √(g/l)

# Atualização de parâmetros thread-safe
sim.set_params(b=0.5)   # aceitos: m, l, g, b
```
