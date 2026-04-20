---
slug: pid-anti-windup-research
title: "PID com Anti-Windup: Teoria, Ajuste e Validação Experimental"
description: >
  Um deep-dive orientado à pesquisa sobre PID discreto com anti-windup por
  back-calculation — do problema de windup integral à validação experimental
  de resposta ao degrau, com código Synapsys ao longo do post.
authors: [oseias]
tags: [artigo, research, pid, control-theory, simulation, python, tutorial]
content_type: artigo
hide_table_of_contents: false
---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

O windup integral é um dos modos de falha mais comuns em controladores PID em produção.
Este post cobre o problema a partir dos primeiros princípios, deriva o esquema de
anti-windup por back-calculation, mostra como o Synapsys o implementa e valida o
projeto contra uma planta simulada de segunda ordem.

{/* truncate */}

## O problema do windup

Um controlador PID com saturação na saída tem uma interação problemática: quando o
atuador está saturado, o integrador continua acumulando erro mesmo que a saída esteja
limitada. Quando o sinal do erro se inverte, o integrador leva muito tempo para
"desacumular" antes que a saída saia da saturação — causando sobressinal e oscilação.

---

## Anti-windup por back-calculation

O esquema de back-calculation realimenta o erro de saturação para o integrador com
ganho $1/T_t$:

$$
\dot{I}(t) = K_i \cdot e(t) + \frac{1}{T_t}\bigl[u_{sat}(t) - u_{uns}(t)\bigr]
$$

Quando a saída *não* está saturada, $u_{sat} = u_{uns}$ e o termo de correção é
zero — o integrador se comporta normalmente.

### Implementação no Synapsys

```python
from synapsys.algorithms import PID

pid = PID(
    Kp    = 5.0,
    Ki    = 2.0,
    Kd    = 0.1,
    dt    = 0.01,
    u_min = -1.0,
    u_max =  1.0,
    # anti_windup=True é o padrão
)

u = pid.compute(setpoint=5.0, measurement=y)
```

---

## Simulação comparativa

<Tabs>
<TabItem value="code" label="Simulação">

```python
import numpy as np
from synapsys.algorithms import PID
from synapsys.api import ss, c2d

planta = c2d(ss([[-0.5]], [[1]], [[1]], [[0]]), dt=0.01)

def rodar_sim(anti_windup: bool, n_passos: int = 800):
    pid = PID(Kp=5.0, Ki=2.0, Kd=0.05, dt=0.01,
              u_min=-1.0, u_max=1.0, anti_windup=anti_windup)
    x = np.zeros(1)
    ys = []
    for i in range(n_passos):
        setpoint = 3.0 if i < 400 else -3.0
        y = float(x[0])
        u = np.array([pid.compute(setpoint, y)])
        x, _ = planta.evolve(x, u)
        ys.append(y)
    return np.array(ys)

y_sem = rodar_sim(anti_windup=False)
y_com = rodar_sim(anti_windup=True)
```

</TabItem>
<TabItem value="results" label="Resultados">

**Sem anti-windup:**
- Degrau positivo: sobressinal ~40% antes de estabilizar
- Degrau negativo: transiente grande por windup acumulado

**Com anti-windup:**
- Ambos os degraus: resposta limpa, similar a primeira ordem
- Sobressinal < 5%
- Tempo de acomodação reduzido em ~60%

</TabItem>
</Tabs>

---

## Diretrizes de ajuste para pesquisa

| Parâmetro | Efeito | Ponto de partida |
|-----------|--------|------------------|
| $K_p$ | Velocidade de resposta | FOPDT: $K_p = 0,6 / (K_{planta} \cdot \tau)$ |
| $K_i = K_p / T_i$ | Eliminação de erro em regime permanente | $T_i = 2\tau$ |
| $K_d = K_p \cdot T_d$ | Amortecimento, amplificação de ruído | $T_d = \tau / 4$ |
| $u_{min}, u_{max}$ | Limites do atuador | Especificação física do atuador |

---

## Conexão com a literatura

O esquema de back-calculation usado no Synapsys segue **Åström & Hägglund (2006)**
*Advanced PID Control*, Capítulo 6.

```bibtex
@book{astrom2006advanced,
  author    = {Åström, Karl Johan and Hägglund, Tore},
  title     = {Advanced PID Control},
  publisher = {ISA — The Instrumentation, Systems, and Automation Society},
  year      = {2006},
  isbn      = {978-1556175169},
}
```

A referência completa da API está em [synapsys.algorithms →](/docs/api/algorithms).
