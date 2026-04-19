---
id: transport
title: synapsys.broker / synapsys.transport
sidebar_position: 5
---

# synapsys.broker

Central pub/sub routing layer. **This is the recommended interface for all agent communication.**

## Topic

Typed, shaped, hashable signal descriptor. Frozen dataclass.

```python
Topic(
    name: str,
    shape: tuple[int, ...],
    dtype: np.dtype = np.dtype(np.float64),
)
```

| Property | Description |
|---|---|
| `name` | Hierarchical string identifier, e.g. `"plant/y"` |
| `shape` | Expected array shape; validated on every `publish` |
| `dtype` | NumPy dtype (default `float64`) |
| `size` *(property)* | Total number of elements (product of `shape`) |

## BrokerBackend (Abstract Base Class)

Interface implemented by all backends.

| Method | Description |
|---|---|
| `supports(topic: Topic) -> bool` | Returns `True` if this backend handles the given topic |
| `write(topic: Topic, data: np.ndarray) -> None` | Writes validated data to the transport |
| `read(topic: Topic) -> np.ndarray` | Reads data from the transport (ZOH — returns last value if no new data) |
| `close() -> None` | Releases resources |

Backends are context managers: `with backend: ...` calls `close()` on exit.

## SharedMemoryBackend

Zero-copy backend using OS shared memory. Best for agents on the same machine.

```python
SharedMemoryBackend(
    name: str,
    topics: list[Topic],
    create: bool = False,
)
```

| Parameter | Description |
|---|---|
| `name` | OS shared memory block identifier |
| `topics` | Topics routed through this backend |
| `create` | `True` for the owner process (allocates memory and calls `unlink()` on close) |

Arrays are flattened on write and reshaped to `topic.shape` on read.

## ZMQBrokerBackend

Async PUB/SUB backend for cross-machine communication.

```python
ZMQBrokerBackend(
    address: str,
    topics: list[Topic],
    mode: Literal["pub", "sub"],
)
```

- In `"pub"` mode the socket **binds** to `address`.
- In `"sub"` mode the socket **connects** to `address` and starts a background recv thread.
- Reads are non-blocking (Zero-Order Hold cache).
- `linger=0` on close — no blocking on teardown.

## MessageBroker

```python
broker = MessageBroker()
```

| Method | Description |
|---|---|
| `declare_topic(topic: Topic)` | Registers a topic. Must be called before `publish` or `read`. |
| `add_backend(backend: BrokerBackend)` | Attaches a backend. Topics are routed to the first matching backend. |
| `publish(name: str, data: np.ndarray)` | Validates shape → writes to backend → fires callbacks. |
| `read(name: str) -> np.ndarray` | Non-blocking read from backend (ZOH). |
| `subscribe(name: str, callback)` | Registers a `Callable[[np.ndarray], None]` fired on every `publish`. |
| `unsubscribe(name: str, callback)` | Removes a previously registered callback. |
| `read_wait(name: str, timeout: float = 1.0) -> np.ndarray` | Blocks until new data arrives or `timeout` seconds elapse. |
| `close()` | Closes all registered backends. |

```python
from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend
import numpy as np

topic_y = Topic("plant/y", shape=(1,))
topic_u = Topic("plant/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend("ctrl_bus", [topic_y, topic_u], create=True))
broker.publish("plant/y", np.zeros(1))
broker.publish("plant/u", np.zeros(1))
```

---

# synapsys.transport

Low-level transport strategy implementations. Use these directly only when you need custom integrations or are building a new `BrokerBackend`.

## TransportStrategy (Abstract Base Class)

All transports implement this interface:

| Method | Description |
|--------|-------------|
| `write(channel: str, data: np.ndarray) -> None` | Writes data to a named channel |
| `read(channel: str) -> np.ndarray` | Reads data from a named channel |
| `close() -> None` | Releases resources |

## SharedMemoryTransport

Zero-copy transport using OS shared memory.

```python
SharedMemoryTransport(
    name: str,
    channels: dict[str, int],
    create: bool = False,
)
```

| Parameter | Description |
|-----------|-------------|
| `name` | OS shared memory block identifier |
| `channels` | Dict mapping channel name to number of float64 values |
| `create` | `True` for the owner process (allocates memory) |

:::warning
Only the `create=True` instance calls `unlink()` on close. All other instances call only `close()`.
:::

## ZMQTransport

PUB/SUB asynchronous transport over a network.

```python
ZMQTransport(address: str, mode: Literal["pub", "sub"])
```

## ZMQReqRepTransport {#zmqrepreptransport}

Synchronous REQ/REP transport for lock-step simulation over a network.

```python
ZMQReqRepTransport(address: str, mode: Literal["server", "client"])
```

:::warning[Order matters]
Server must call `read()` before `write()`. Client must call `write()` before `read()`. Mismatched order causes deadlock.
:::

## Source

See [`synapsys/broker/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/broker) and [`synapsys/transport/`](https://github.com/synapsys-lab/synapsys/tree/main/synapsys/transport) on GitHub.
