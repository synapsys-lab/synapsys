---
id: simulators-overview
title: Simuladores Físicos — Visão Geral
sidebar_label: Visão Geral
sidebar_position: 1
---

# Simuladores Físicos

`synapsys.simulators` fornece simuladores físicos contínuos e não-lineares com uma
interface unificada para projeto de controladores, testes e aprendizado por reforço.

---

## Simuladores disponíveis

| Classe | Sistema | Estados | Entradas | Saídas |
|---|---|---|---|---|
| `MassSpringDamperSim` | MMA linear 1-DOF | `[q, q̇]` | `[F]` | `[q]` |
| `InvertedPendulumSim` | Pêndulo não-linear em pivô fixo | `[θ, θ̇]` | `[τ]` | `[θ]` |
| `CartPoleSim` | Cart-pole Lagrangiano | `[p, ṗ, θ, θ̇]` | `[F]` | `[p, θ]` |

---

## Interface comum

Todo simulador herda de `SimulatorBase` e expõe a mesma API:

```python
from synapsys.simulators import CartPoleSim

sim = CartPoleSim()
y = sim.reset()                   # reset → observação inicial
y, info = sim.step(u, dt=0.02)    # avança um passo
ss  = sim.linearize(x0, u0)      # linearização numérica → StateSpace
```

### Dicionário `info` do `step()`

```python
y, info = sim.step(u, dt=0.02)
info["x"]       # estado completo após o passo
info["t_step"]  # tempo de integração (= dt)
info["failed"]  # True quando o sistema saiu da região segura
```

---

## Integradores

Todos os simuladores suportam três métodos de integração numérica, selecionáveis na construção:

| Método | Precisão | Velocidade | Uso recomendado |
|---|---|---|---|
| `"euler"` | Baixa | Mais rápido | dt muito pequeno (≤ 1 ms), loops internos de RL |
| `"rk4"` | Alta | Rápido | Padrão — bom equilíbrio |
| `"rk45"` | Muito alta | Mais lento | Referência / validação |

```python
sim = CartPoleSim(integrator="rk4")   # padrão
sim = CartPoleSim(integrator="euler") # mais rápido
```

---

## Ruído e perturbações

```python
sim = InvertedPendulumSim(noise_std=0.01, disturbance_std=0.05)
```

- `noise_std` — ruído gaussiano adicionado a cada observação (modelo de ruído de sensor)
- `disturbance_std` — ruído gaussiano injetado na entrada de controle (ruído de processo)

---

## Atualização de parâmetros thread-safe

Todos os simuladores suportam alterações de parâmetros em tempo real a partir de outra thread:

```python
sim.set_params(m=0.5)     # InvertedPendulumSim
sim.set_params(m_c=2.0)   # CartPoleSim
```

---

## Detecção de falha

```python
y, info = sim.step(u, dt)
if info["failed"]:
    sim.reset()
```

| Simulador | Condição de falha |
|---|---|
| `CartPoleSim` | `\|p\| > 4,8 m` ou `\|θ\| > π/3 rad` |
| `InvertedPendulumSim` | `\|θ\| > π/2 rad` |
| `MassSpringDamperSim` | nunca (sempre estável) |

---

## Linearização

Todo simulador expõe `linearize(x0, u0)`, que retorna um `StateSpace` contínuo
via diferenças finitas centrais — pronto para projeto LQR:

```python
from synapsys.algorithms.lqr import lqr

ss = sim.linearize(np.zeros(4), np.zeros(1))
K, _ = lqr(ss.A, ss.B, Q, R)
```
