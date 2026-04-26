---
id: simulators-cartpole
title: Simulador Cart-Pole
sidebar_label: Cart-Pole
sidebar_position: 4
---

# Simulador Cart-Pole

`CartPoleSim` implementa o cart-pole Lagrangiano clássico: um carrinho deslizando
sobre um trilho sem atrito com um pêndulo invertido acoplado no pivô.

---

## Modelo físico

**Estados:** `x = [p, ṗ, θ, θ̇]`
- `p` — posição do carrinho (m)
- `ṗ` — velocidade do carrinho (m/s)
- `θ` — ângulo da haste em relação à vertical (rad, θ=0 → equilibrado)
- `θ̇` — velocidade angular da haste (rad/s)

**Entrada:** `u = [F]` — força horizontal no carrinho (N)

**Saída:** `y = [p, θ]` — observação parcial (sem velocidades)

**Dinâmica não-linear (Lagrangiana):**

```
Δ  = m_c + m_p · sin²(θ)
p̈  = [F + m_p · sin(θ) · (l · θ̇² − g · cos(θ))] / Δ
θ̈  = [g · sin(θ) − p̈ · cos(θ)] / l
```

---

## Construção

```python
from synapsys.simulators import CartPoleSim

sim = CartPoleSim(
    m_c=1.0,            # massa do carrinho (kg)
    m_p=0.1,            # massa da ponta da haste (kg)
    l=0.5,              # comprimento da haste (m)
    g=9.81,             # gravidade (m/s²)
    integrator="rk4",   # "euler", "rk4" ou "rk45"
    noise_std=0.0,       # ruído de sensor
    disturbance_std=0.0, # perturbação na entrada
    linearised=False,    # True → usar dinâmica linearizada
)
```

---

## Modo linearizado

Para ângulos pequenos, a dinâmica não-linear simplifica para um sistema linear.
Passe `linearised=True` para usar essa aproximação:

```python
sim_nl = CartPoleSim(linearised=False)   # não-linear completo
sim_l  = CartPoleSim(linearised=True)    # aproximação linear

# Próximo a θ=0 ambos se comportam de forma idêntica (atol ≈ 1e-4 para dt=0,01 s)
```

---

## Estabilização por LQR

```python
import numpy as np
from synapsys.algorithms.lqr import lqr

sim = CartPoleSim()
sim.reset()
ss = sim.linearize(np.zeros(4), np.zeros(1))

Q = np.diag([1.0, 0.1, 100.0, 10.0])   # penaliza fortemente o ângulo
R = np.eye(1) * 0.01
K, _ = lqr(ss.A, ss.B, Q, R)

sim.reset(x0=np.array([0.0, 0.0, 0.15, 0.0]))
for _ in range(500):
    x = sim.state
    u = np.clip(-K @ x, -50, 50)
    y, info = sim.step(u, dt=0.02)
    if info["failed"]:
        break
```

---

## Animação 2D com matplotlib

```python
from synapsys.viz import CartPole2DView

# LQR automático
CartPole2DView().run()

# Controlador customizado
CartPole2DView(controller=lambda x: np.clip(-K @ x, -50, 50)).run()

# Simulação sem display
hist = CartPole2DView(dt=0.02, duration=5.0).simulate()
print(hist["angle"][-1])   # ângulo final da haste (rad)

# Salvar animação
view = CartPole2DView()
anim = view.animate(save="cartpole.gif")
```

---

## Detecção de falha

O simulador sinaliza falha quando o sistema sai da região segura:

| Condição | Valor |
|---|---|
| Carrinho fora dos limites | `\|p\| > 4,8 m` |
| Haste caiu | `\|θ\| > π/3 rad (≈ 60°)` |

```python
y, info = sim.step(u, dt)
if info["failed"]:
    print("Episódio encerrado — reiniciando")
    sim.reset()
```

---

## Atualização de parâmetros thread-safe

```python
import threading

def controlador_lento():
    while True:
        sim.set_params(m_c=2.0)   # seguro a partir de qualquer thread

t = threading.Thread(target=controlador_lento, daemon=True)
t.start()
```

Chaves aceitas: `m_c`, `m_p`, `l`, `g`.
