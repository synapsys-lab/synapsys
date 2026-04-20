---
id: zmq
title: Transporte ZeroMQ
sidebar_position: 3
---

# Transporte ZeroMQ

O transporte ZMQ permite que agentes se comuniquem **por rede**, incluindo máquinas diferentes. É baseado na biblioteca [ZeroMQ](https://zeromq.org/), que usa C/C++ internamente e opera na casa dos microssegundos em rede local.

## PUB/SUB — Assíncrono

Cada agente publica em um endereço e assina em outro. Não ha bloqueio — se o consumidor estiver atrasado, ele le a última mensagem disponível.

```python
from synapsys.transport import ZMQTransport
import numpy as np

# Planta (publicador)
pub = ZMQTransport("tcp://0.0.0.0:5555", mode="pub")
pub.write("y", np.array([3.14]))

# Controlador (assinante)
sub = ZMQTransport("tcp://192.168.1.10:5555", mode="sub")
y = sub.read("y")
```

### Topologia bidirecional

```
Planta:       PUB :5555  ->  SUB :5556
Controlador:  PUB :5556  ->  SUB :5555
```

## REQ/REP — Lock-step

Garante sincronismo total: o cliente bloqueia até receber a resposta.

```python
from synapsys.transport import ZMQReqRepTransport

# Planta (servidor)
server = ZMQReqRepTransport("tcp://0.0.0.0:5555", mode="server")
u = server.read("u")
server.write("y", y_array)

# Controlador (cliente)
client = ZMQReqRepTransport("tcp://localhost:5555", mode="client")
client.write("u", u_array)
y = client.read("y")
```

:::warning Ordem importa no REQ/REP
O servidor deve fazer `read()` antes de `write()`, e o cliente `write()` antes de `read()`. Inverter a ordem causa deadlock.
:::

## Latência

| Cenario | Latência tipica |
|---------|----------------|
| Loopback (`localhost`) | ~50–100 µs |
| LAN 1 Gbps | ~100–300 µs |
| WAN / Internet | > 1 ms |

Para comparação, `SharedMemoryTransport` opera em < 1 µs.

## Referência da API

Consulte a referência completa em [synapsys.transport — ZMQTransport](/docs/api/transport).
