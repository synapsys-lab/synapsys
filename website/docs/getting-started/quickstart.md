---
id: quickstart
title: Quick Start
sidebar_position: 2
---

# Quick Start

## 1. Analysing a continuous-time system

```python
from synapsys.api import tf, step, bode, feedback
import matplotlib.pyplot as plt

# G(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2*zeta*wn, wn**2])

print(f"Poles:  {G.poles()}")
print(f"Stable: {G.is_stable()}")

t, y = step(G)
plt.plot(t, y)
plt.grid(True)
plt.show()
```

## 2. Closed-loop with unity negative feedback

```python
from synapsys.api import tf, feedback, step

G = tf([10], [1, 1])      # G(s) = 10/(s+1)
T = feedback(G)            # T = G/(1+G) = 10/(s+11)

print(f"DC gain: {T.evaluate(0).real:.4f}")   # 0.9091
t, y = step(T)
```

## 3. Discretise and simulate

```python
from synapsys.api import tf, c2d, step

G = tf([1], [1, 2, 1])      # continuous system
Gd = c2d(G, dt=0.05)         # ZOH, Ts = 50 ms

print(f"Discrete: {Gd.is_discrete}")
print(f"Stable:   {Gd.is_stable()}")

t, y = Gd.step(n=200)        # 200 samples
```

## 4. Distributed simulation (same machine)

Run in two separate terminals:

```bash
# Terminal 1 — start the plant first
python examples/distributed/01_shared_memory/plant.py

# Terminal 2 — then the controller
python examples/distributed/01_shared_memory/controller.py
```

The plant exposes its state via **shared memory** (zero-copy). The controller reads `y`, computes `u` with PID, and writes it back — no network sockets involved.

## 5. Distributed simulation (different machines)

```bash
# Machine A — plant
python examples/distributed/02_zmq/plant_zmq.py

# Machine B — controller (set PLANT_HOST to Machine A's IP)
PLANT_HOST=192.168.1.10 python examples/distributed/02_zmq/controller_zmq.py
```
