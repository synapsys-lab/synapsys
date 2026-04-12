# 02 — Distributed Simulation via ZeroMQ (Network)

## Concept

This example extends the distributed simulation to **network communication** using **ZeroMQ** (ZMQ). Unlike the shared memory example, the plant and controller can run on **different machines** connected over a network.

ZMQ is a high-performance asynchronous messaging library. It provides socket-like primitives but handles reconnection, buffering, and framing automatically.

```
Machine A                          Machine B (or same machine)
plant_zmq.py                       controller_zmq.py
     │                                     │
     │  PUB :5555  ──── TCP ────  SUB :5555│  y(t)
     │                                     │
     │  SUB :5556  ──── TCP ────  PUB :5556│  u(t)
```

### ZMQ PUB/SUB pattern

ZMQ's **Publisher-Subscriber** pattern is ideal for sensor data streaming:
- The **publisher** (PUB) sends data to all connected subscribers
- The **subscriber** (SUB) filters messages by topic prefix

In synapsys, `ZMQTransport` serialises numpy arrays to bytes and uses the channel name as the topic.

### Why ZMQ over raw TCP sockets?

| Feature | Raw TCP | ZMQ PUB/SUB |
|---|---|---|
| Reconnection | Manual | Automatic |
| Multiple subscribers | Complex | Built-in |
| Message framing | Manual | Built-in |
| Async buffering | Manual | Built-in |
| Language bindings | OS-specific | 40+ languages |

---

## Plant (plant_zmq.py)

```python
pub = ZMQTransport("tcp://0.0.0.0:5555", mode="pub")
sub = ZMQTransport(f"tcp://{CONTROLLER_HOST}:5556", mode="sub")
sub._socket.setsockopt(0x8, 100)  # ZMQ_RCVTIMEO = 100 ms
```

- PUB on port **5555** — plant publishes `y` to the network
- SUB on port **5556** — plant subscribes to `u` from the controller
- `ZMQ_RCVTIMEO = 100ms` — if no `u` arrives within 100ms, `read()` raises an exception

```python
# Non-blocking read — keep last u if controller hasn't sent yet (ZOH)
try:
    u = sub.read("u")
except Exception:
    pass  # keep previous u
```

**Zero-Order Hold (ZOH) fallback**: if the controller hasn't sent a new `u` yet (e.g., startup lag or network delay), the plant reuses the last control value. This prevents the plant from stalling.

---

## Controller (controller_zmq.py)

```python
sub = ZMQTransport(f"tcp://{PLANT_HOST}:5555", mode="sub")
pub = ZMQTransport("tcp://0.0.0.0:5556", mode="pub")
sub._socket.setsockopt(0x8, 50)  # ZMQ_RCVTIMEO = 50 ms
```

Note the **cross-subscription**:
- Controller SUBscribes to plant's PUB (port 5555)
- Controller PUBlishes to plant's SUB (port 5556)

The controller runs at **2× the plant rate** (DT=0.025s vs plant DT=0.05s), issuing control commands more frequently than plant state updates arrive. Extra cycles simply retry `sub.read("y")` — the `except` block silently skips if no new data is available.

---

## Timing and rate decoupling

```python
elapsed = time.monotonic() - t0
if DT - elapsed > 0:
    time.sleep(DT - elapsed)
```

Both plant and controller use a **deadline-based sleep**: measure how long the computation took, sleep only the remaining time. This gives more accurate timing than a fixed `time.sleep(DT)`.

---

## Running on two machines

To run across machines, change the host variables:

**On Machine A (plant):**
```python
CONTROLLER_HOST = "192.168.1.42"   # IP of Machine B
```

**On Machine B (controller):**
```python
PLANT_HOST = "192.168.1.10"        # IP of Machine A
```

Make sure ports 5555 and 5556 are open in the firewall.

---

## How to run (same machine)

```bash
# Terminal 1
uv run python examples/distributed/02_zmq/plant_zmq.py

# Terminal 2
uv run python examples/distributed/02_zmq/controller_zmq.py
```

The plant runs for 300 steps (~15 seconds) and prints each tick. The controller runs until `Ctrl+C`.

> **Port conflict?** Run `fuser -k 5555/tcp 5556/tcp` to release stale ZMQ sockets from a previous run.
