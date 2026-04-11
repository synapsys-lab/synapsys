---
id: transport
title: synapsys.transport
sidebar_position: 5
---

# synapsys.transport

Transport strategy implementations for inter-process communication.

## TransportStrategy (Abstract Base Class)

All transports implement this interface:

| Method | Description |
|--------|-------------|
| `write(channel: str, data: np.ndarray) -> None` | Writes data to a named channel |
| `read(channel: str) -> np.ndarray` | Reads data from a named channel |
| `close() -> None` | Releases resources |

## SharedMemoryTransport

Zero-copy transport using OS shared memory. Best for processes on the same machine.

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

## ZMQReqRepTransport

Synchronous REQ/REP transport for lock-step simulation over a network.

```python
ZMQReqRepTransport(address: str, mode: Literal["server", "client"])
```

:::warning[Order matters]
Server must call `read()` before `write()`. Client must call `write()` before `read()`. Mismatched order causes deadlock.
:::

## Source

See [`synapsys/transport/`](https://github.com/synapsys/synapsys/tree/main/synapsys/transport) on GitHub.
