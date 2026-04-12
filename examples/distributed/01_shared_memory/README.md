# 01 — Distributed Simulation via Shared Memory

## Concept

This example shows how to split the plant and controller into **two separate processes** that communicate via **shared memory IPC** — without using any network protocol, socket, or file I/O.

This is the simplest form of multi-process simulation: both processes run on the **same machine**, and the OS maps the same physical memory pages into both address spaces.

```
Process 1 (plant.py)          Process 2 (controller.py)
       │                              │
       ▼                              ▼
 write y → ┌──────────────┐ ← read y
           │  Shared Mem  │
 read  u ← │  "synapsys_  │ → write u
           │   demo"      │
           └──────────────┘
```

### Why multi-process instead of multi-thread?

- **Process isolation** — a crash in the controller does not kill the plant
- **Independent deployment** — processes can be started/stopped independently
- **Rate independence** — the controller runs at 40 Hz while the plant runs at 20 Hz; they don't need to be synchronised at the code level
- **Mimics real hardware** — in an actual embedded system, the plant runs on a PLC and the controller on a separate computer

---

## Plant (plant.py)

```python
with SharedMemoryTransport(BUS_NAME, CHANNELS, create=True) as bus:
    bus.write("y", np.array([0.0]))
    bus.write("u", np.array([0.0]))
    print("Plant: bus ready. Starting in 2s — launch controller.py now.")
    time.sleep(2.0)
```

The plant **creates** the shared memory block (`create=True`). It initialises both channels to 0 and waits 2 seconds to give you time to start the controller in another terminal.

Using `with` ensures the memory block is released even if the script crashes.

```python
for k in range(N_STEPS):
    u = bus.read("u")[0]
    y = bus.read("y")[0]
    y_next = 0.9 * y + 0.1 * u   # y(k+1) = 0.9·y(k) + 0.1·u(k)
    bus.write("y", np.array([y_next]))
    time.sleep(DT)
```

Discrete first-order dynamics with pole at z = 0.9. Equivalent to:
```
G(z) = 0.1 / (z - 0.9)
```
Continuous equivalent: G(s) = 1/(s+1) with ZOH at ~20 Hz.

---

## Controller (controller.py)

```python
with SharedMemoryTransport(BUS_NAME, CHANNELS, create=False) as bus:
    while True:
        y = bus.read("y")[0]
        u = pid.compute(setpoint=SETPOINT, measurement=y)
        bus.write("u", np.array([u]))
        time.sleep(DT)
```

The controller **connects** to the existing bus (`create=False`). If the plant is not running, `SharedMemoryTransport` raises `FileNotFoundError` — caught with a helpful error message.

The PID runs at 40 Hz (`DT=0.025`) — twice the plant rate. This is intentional: the controller samples the bus faster than the plant updates it, demonstrating rate decoupling. The controller simply reuses the last `y` value between plant updates.

```python
pid = PID(Kp=3.0, Ki=0.5, dt=DT, u_min=-10.0, u_max=10.0)
```

- **Kp = 3.0** — fast proportional response
- **Ki = 0.5** — eliminates steady-state error for setpoint = 5.0
- Saturation limits prevent integrator windup

---

## How to run

```bash
# Terminal 1 — start plant first
uv run python examples/distributed/01_shared_memory/plant.py

# Terminal 2 — connect controller (within 2s)
uv run python examples/distributed/01_shared_memory/controller.py
```

The plant prints `k=NNN  u=X.XXX  y=X.XXX` for 200 steps (~10 seconds), then exits. The controller runs until you press `Ctrl+C`.

You should see `y` converge to `5.0` (the setpoint) within the first few steps.
