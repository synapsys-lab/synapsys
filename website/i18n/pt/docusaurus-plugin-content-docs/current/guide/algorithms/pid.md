---
format: md
id: pid
title: Controlador PID
sidebar_position: 1
---

# Controlador PID

O `PID` implementa um controlador Proporcional-Integral-Derivativo discreto com **saturação de saida** e **anti-windup por back-calculation**.

## Formula

$$
u(k) = K_p \, e(k) + K_i \sum_{j=0}^{k} e(j)\,\Delta t + K_d \, \frac{e(k) - e(k-1)}{\Delta t}
$$

O anti-windup corrige o integrador quando a saida satura:

$$
\text{integral} \mathrel{+}= \frac{u_{sat}(k) - u(k)}{K_i}
$$

## Uso basico

```python
from synapsys.algorithms import PID

pid = PID(
    Kp=2.0,
    Ki=0.5,
    Kd=0.1,
    dt=0.01,
    u_min=-10.0,
    u_max=10.0,
)

setpoint = 5.0
y = 0.0

for _ in range(1000):
    u = pid.compute(setpoint=setpoint, measurement=y)
    # ... aplica u na planta, le novo y ...
```

## Anti-windup

Sem anti-windup, o integrador continua acumulando erro durante a saturação, causando **integrator windup**: atraso excessivo ao sair da saturação.

Com back-calculation, quando `u` satura, o integrador e corrigido na direção oposta:

```python
pid_sem = PID(Kp=5.0, Ki=10.0, dt=0.01)
pid_com = PID(Kp=5.0, Ki=10.0, dt=0.01,
              u_min=-1.0, u_max=1.0)

# pid_com converge muito mais rapido ao sair de uma saturacao prolongada
```

## Reset do estado

```python
pid.reset()    # zera integrador e erro anterior
```

Útil em trocas de modo (manual para automatico) ou ao mudar o setpoint abruptamente.

## Referência da API

Consulte a referência completa em [synapsys.algorithms — PID](/docs/api/algorithms).
