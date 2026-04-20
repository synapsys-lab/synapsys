---
id: quickstart
title: Início Rápido
sidebar_position: 2
---

# Início Rápido

## 1. Analisando um sistema continuo

```python
from synapsys.api import tf, step, bode, feedback
import matplotlib.pyplot as plt

# G(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2*zeta*wn, wn**2])

print(f"Polos:   {G.poles()}")
print(f"Estavel: {G.is_stable()}")

t, y = step(G)
plt.plot(t, y)
plt.grid(True)
plt.show()
```

## 2. Malha fechada com realimentação unitaria negativa

```python
from synapsys.api import tf, feedback, step

G = tf([10], [1, 1])      # G(s) = 10/(s+1)
T = feedback(G)            # T = G/(1+G) = 10/(s+11)

print(f"Ganho DC: {T.evaluate(0).real:.4f}")   # 0.9091
t, y = step(T)
```

## 3. Discretizar e simular

```python
from synapsys.api import tf, c2d, step

G = tf([1], [1, 2, 1])      # sistema continuo
Gd = c2d(G, dt=0.05)         # ZOH, Ts = 50 ms

print(f"Discreto: {Gd.is_discrete}")
print(f"Estavel:  {Gd.is_stable()}")

t, y = Gd.step(n=200)        # 200 amostras
```

## 4. Simulação distribuída (mesma máquina)

Execute em dois terminais separados:

```bash
# Terminal 1 — inicie a planta primeiro
python examples/distributed/plant.py

# Terminal 2 — depois o controlador
python examples/distributed/controller.py
```

A planta expoe seu estado via **memória compartilhada** (zero-copy). O controlador le `y`, calcula `u` com PID e escreve de volta — sem sockets de rede envolvidos.

## 5. Simulação distribuída (máquinas diferentes)

```bash
# Maquina A — planta
python examples/distributed/plant_zmq.py

# Maquina B — controlador (configure PLANT_HOST com o IP da Maquina A)
PLANT_HOST=192.168.1.10 python examples/distributed/controller_zmq.py
```
