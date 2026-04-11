---
id: zmq
title: ZeroMQ Transport
sidebar_position: 3
---

# ZeroMQ Transport

The ZMQ transport allows agents to communicate **over a network**, including across different machines. It is based on the [ZeroMQ](https://zeromq.org/) library, which uses C/C++ internally and operates in the microsecond range on a local network.

## PUB/SUB — Asynchronous

Each agent publishes on one address and subscribes on another. There is no blocking — if the consumer is behind, it reads the last available message.

```python
from synapsys.transport import ZMQTransport
import numpy as np

# Plant (publisher)
pub = ZMQTransport("tcp://0.0.0.0:5555", mode="pub")
pub.write("y", np.array([3.14]))

# Controller (subscriber)
sub = ZMQTransport("tcp://192.168.1.10:5555", mode="sub")
y = sub.read("y")
```

### Bidirectional topology

For two-way communication, use two PUB/SUB connections:

```
Plant:       PUB :5555  ->  SUB :5556
Controller:  PUB :5556  ->  SUB :5555
```

See `examples/distributed/plant_zmq.py` and `examples/distributed/controller_zmq.py` in the repository.

## REQ/REP — Lock-step

Guarantees full synchronisation: the client blocks until it receives a reply, and the server processes one request at a time.

```python
from synapsys.transport import ZMQReqRepTransport

# Plant (server)
server = ZMQReqRepTransport("tcp://0.0.0.0:5555", mode="server")
u = server.read("u")          # blocks until the controller sends
server.write("y", y_array)    # replies with new state

# Controller (client)
client = ZMQReqRepTransport("tcp://localhost:5555", mode="client")
client.write("u", u_array)    # sends control action
y = client.read("y")          # blocks until the plant replies
```

:::warning[Order matters in REQ/REP]
The server must call `read()` before `write()`, and the client must call `write()` before `read()`. Reversing the order causes deadlock.
:::

## Latency

| Scenario | Typical latency |
|---------|----------------|
| Loopback (`localhost`) | ~50–100 µs |
| 1 Gbps LAN | ~100–300 µs |
| WAN / Internet | > 1 ms |

For comparison, `SharedMemoryTransport` operates at < 1 µs.

## API Reference

See the full reference at [synapsys.transport — ZMQTransport](../../api/transport#synapsystransportnetworkzmqtransport) and [ZMQReqRepTransport](../../api/transport#synapsystransportnetworkzmqrepreptransport).
