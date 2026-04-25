---
id: custom-controller
title: Conectando seu Controlador
sidebar_label: Controlador Customizado
sidebar_position: 3
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# Conectando seu Controlador

Qualquer callable Python pode ser usado como controlador nas views 3D.
Basta passar a função para o parâmetro `controller=`:

```python
CartPoleView(controller=minha_funcao).run()
```

---

## Assinatura esperada

```python
controller(x: np.ndarray) -> np.ndarray | float
```

| Argumento | Tipo | Descrição |
|---|---|---|
| `x` | `np.ndarray` shape `(n,)` | vetor de estado completo no instante atual |
| retorno | `np.ndarray` shape `(m,)` ou `float` | ação de controle (será convertida para array internamente) |

O controlador é chamado a cada `dt` segundos na **thread da UI**.
Para modelos pesados (> 5 ms de inferência), veja a seção [Thread-safety](#thread-safety).

:::tip
Quando `controller=None` (padrão), a lib projeta um LQR automaticamente
via `sim.linearize()` + `lqr(Q, R)`. O controlador customizado **substitui** o LQR.
A perturbação interativa dos botões é adicionada **depois** do retorno do seu controlador.
:::

---

## Exemplos

<Tabs>
  <TabItem value="lqr" label="LQR manual">

Projete o LQR fora da lib e passe o ganho K como controlador:

```python
import numpy as np
from synapsys.viz import CartPoleView
from synapsys.simulators import CartPoleSim
from synapsys.algorithms.lqr import lqr

# 1. Obter o modelo linearizado
sim = CartPoleSim(m_c=1.0, m_p=0.1, l=0.5)
sim.reset()
ss = sim.linearize(np.zeros(4), np.zeros(1))

# 2. Projetar LQR com pesos customizados
Q = np.diag([5.0, 0.1, 500.0, 50.0])  # penaliza mais o ângulo
R = 0.001 * np.eye(1)                  # permite forças maiores
K, _ = lqr(ss.A, ss.B, Q, R)

# 3. Passar para a view
CartPoleView(
    controller=lambda x: np.clip(-K @ x, -100, 100)
).run()
```

  </TabItem>
  <TabItem value="pid" label="PID">

Um controlador PID para o pêndulo (controla apenas o ângulo θ):

```python
import numpy as np
from synapsys.viz import PendulumView
from synapsys.algorithms.pid import PID

pid = PID(kp=80.0, ki=5.0, kd=8.0, dt=0.01,
          u_min=-30.0, u_max=30.0)

def pid_ctrl(x: np.ndarray) -> np.ndarray:
    theta = x[0]            # ângulo (rad)
    tau = pid.compute(setpoint=0.0, measurement=theta)
    return np.array([tau])

PendulumView(controller=pid_ctrl).run()
```

  </TabItem>
  <TabItem value="pytorch" label="PyTorch">

Uma política neural treinada com PyTorch:

```python
import numpy as np
import torch
from synapsys.viz import CartPoleView

# Carregar modelo pré-treinado
model = torch.load("cartpole_policy.pt", map_location="cpu")
model.eval()

def neural_ctrl(x: np.ndarray) -> np.ndarray:
    with torch.no_grad():
        t = torch.tensor(x, dtype=torch.float32).unsqueeze(0)
        u = model(t).squeeze(0).numpy()
    return np.clip(u, -80, 80)

CartPoleView(controller=neural_ctrl).run()
```

> **Dica:** se o modelo foi treinado com normalização de estado,
> aplique o mesmo scaler antes de passar `x` para o modelo.

  </TabItem>
  <TabItem value="sb3" label="Stable-Baselines3 (RL)">

Um agente RL treinado com Stable-Baselines3:

```python
import numpy as np
from stable_baselines3 import SAC
from synapsys.viz import CartPoleView

agent = SAC.load("cartpole_sac_trained")

def rl_ctrl(x: np.ndarray) -> np.ndarray:
    action, _ = agent.predict(x, deterministic=True)
    return action

CartPoleView(controller=rl_ctrl).run()
```

  </TabItem>
  <TabItem value="residual" label="Neural-LQR residual">

Arquitetura residual: o LQR garante estabilidade, a rede aprende o resíduo.
Mesma arquitetura do exemplo Quadcopter MIMO da lib:

```python
import numpy as np
import torch
import torch.nn as nn
from synapsys.viz import PendulumView
from synapsys.simulators import InvertedPendulumSim
from synapsys.algorithms.lqr import lqr

# LQR base
sim = InvertedPendulumSim()
sim.reset()
ss = sim.linearize(np.zeros(2), np.zeros(1))
K, _ = lqr(ss.A, ss.B, np.diag([80, 5]), np.eye(1))

# Rede residual (inicia zerada → comportamento = LQR puro)
class ResidualMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(2, 32), nn.Tanh(),
            nn.Linear(32, 32), nn.Tanh(),
            nn.Linear(32, 1),
        )
        # Inicializar última camada com zeros
        nn.init.zeros_(self.net[-1].weight)
        nn.init.zeros_(self.net[-1].bias)

mlp = ResidualMLP().eval()

def residual_lqr(x: np.ndarray) -> np.ndarray:
    u_lqr = float((-K @ x).ravel()[0])
    with torch.no_grad():
        t = torch.tensor(x, dtype=torch.float32)
        delta_u = mlp(t).item()
    return np.array([np.clip(u_lqr + delta_u, -30, 30)])

PendulumView(controller=residual_lqr).run()
```

  </TabItem>
</Tabs>

---

## Thread-safety

O controlador é executado na **thread principal da UI** (mesma thread do Qt).
Isso significa:

- **Modelos rápidos (< 2 ms):** sem problema, use diretamente.
- **Modelos médios (2–10 ms):** a animação ficará um pouco lenta mas funciona.
- **Modelos lentos (> 10 ms):** a UI trava. Use um thread separado com fila:

```python
import threading
import queue
import numpy as np
from synapsys.viz import CartPoleView

# Fila para comunicação entre threads
action_queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=1)
state_queue:  queue.Queue[np.ndarray] = queue.Queue(maxsize=1)

def slow_model_thread():
    while True:
        x = state_queue.get()
        u = meu_modelo_lento(x)          # pode demorar
        try:
            action_queue.put_nowait(u)
        except queue.Full:
            pass

last_u = np.zeros(1)

def controller(x: np.ndarray) -> np.ndarray:
    global last_u
    try:
        state_queue.put_nowait(x)
        last_u = action_queue.get_nowait()
    except (queue.Full, queue.Empty):
        pass
    return last_u

threading.Thread(target=slow_model_thread, daemon=True).start()
CartPoleView(controller=controller).run()
```

---

## Verificando o controlador antes de rodar

Antes de passar um controlador para a view, você pode testá-lo diretamente
com o simulador:

```python
import numpy as np
from synapsys.simulators import CartPoleSim

sim = CartPoleSim()
sim.reset(x0=np.array([0, 0, 0.2, 0]))

x = sim.state
u = meu_controlador(x)
print("u =", u, "shape =", np.asarray(u).shape)   # deve ser (1,)

y, info = sim.step(np.asarray(u).ravel(), dt=0.02)
print("próximo estado:", info["x"])
```
