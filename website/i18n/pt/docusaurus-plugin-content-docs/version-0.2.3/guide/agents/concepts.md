---
id: concepts
title: Simulação Multiagente — Conceitos
sidebar_position: 1
---

# Simulação Multiagente — Conceitos

O Synapsys trata cada componente da simulação (planta, controlador, observador) como um **agente independente**. Agentes se comunicam por mensagens, não por chamadas de função — o que permite rodar cada componente em um processo, thread ou máquina separada.

## Por que agentes?

O modelo monolítico (tudo no mesmo script) e simples, mas tem limitações:

- Difícil de testar componentes isoladamente
- Não escala para sistemas distribuídos (HIL, redes de controladores)
- Impossível introduzir atraso de rede realista entre planta e controlador

Com agentes:

```
[ PlantAgent ]  <->  [ SharedMemory / ZMQ ]  <->  [ ControllerAgent ]
   Processo A              Barramento                  Processo B
```

## FIPA ACL

O Synapsys usa um subconjunto do padrão **FIPA ACL** (Agent Communication Language) para mensagens estruturadas entre agentes.

```python
from synapsys.agents import ACLMessage, Performative

msg = ACLMessage(
    performative=Performative.INFORM,
    sender="planta",
    receiver="controlador",
    content={"y": 3.14},
)

reply = msg.reply(Performative.REQUEST, content={"u": 1.5})
```

| Performative | Significado |
|---|---|
| `INFORM` | Informa um fato (ex: estado da planta) |
| `REQUEST` | Solicita uma ação (ex: calcular u) |
| `AGREE` | Aceita um pedido |
| `REFUSE` | Recusa um pedido |
| `FAILURE` | Reporta falha na execucao |
| `SUBSCRIBE` | Solicita atualizações periodicas |

## Sincronismo

O `SyncEngine` controla como o tempo avanca dentro de cada agente.

```python
from synapsys.agents import SyncEngine, SyncMode

# Wall-clock: executa em tempo real, com sleep para cadenciar os ticks
sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=0.01)   # 100 Hz

# Lock-step: avanca so quando chamado explicitamente (deterministico)
sync = SyncEngine(mode=SyncMode.LOCK_STEP, dt=0.01)
```

### Wall-clock vs lock-step

| | WALL_CLOCK | LOCK_STEP |
|---|---|---|
| **Velocidade** | Tempo real (limitado por dt) | Tão rápido quanto possível |
| **Sincronia** | Cada agente no seu ritmo | Acoplado por barreira externa |
| **Atraso de rede** | Simulado naturalmente | Transparente |
| **Reprodutibilidade** | Não-determinístico | Determinístico |
| **Uso** | Testes de robustez, HIL | Validacao matemática |

## Ciclo de vida do agente

```
          start()
             |
          setup()          <- inicializa recursos
             |
    +--------+---------+
    |  while running:  |
    |    step()        |   <- um tick da simulacao
    |    sync.tick()   |   <- avanca o relogio
    +--------+---------+
             |
         teardown()        <- libera recursos
```

O transporte **não e fechado** pelo agente — seu ciclo de vida e gerenciado pelo código que criou o agente.
