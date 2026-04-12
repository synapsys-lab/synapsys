# 02 — Software-in-the-Loop with AI Controller

## Concept

### What is SIL?

**SIL (Software-in-the-Loop)** is a simulation methodology where:
- The **plant** (physical system) is replaced by a mathematical model running in real time
- The **controller** operates as it would in production: reading sensors, computing actions, respecting timing
- Both run as **separate processes** communicating through an IPC bus — just like in a real embedded system

The key difference from MIL (Model-in-the-Loop) is **real-time constraint**: the simulation advances with wall-clock time, so timing behaviour (latency, jitter, sample rate mismatch) is visible.

### Architecture

```
┌─────────────────────────────────┐
│   02a_sil_plant.py              │
│   (Process 1 — Physics Engine)  │
│                                 │
│   G(s) = 10/(s²+3s+10)         │
│   ZOH discretised @ 100 Hz      │
│   PlantAgent → evolve(x, u)     │
│                                 │
│   OWNS the shared memory bus    │
└───────────────┬─────────────────┘
                │  Shared Memory "sil_bus"
                │  ┌──────────────────┐
                │  │  y  (float64)    │  ← plant writes
                │  │  u  (float64)    │  ← controller writes
                │  └──────────────────┘
                │
┌───────────────▼─────────────────┐
│   02b_sil_ai_controller.py      │
│   (Process 2 — AI Inference)    │
│                                 │
│   DummyRLController (PyTorch)   │
│   ControllerAgent @ 100 Hz      │
│   Real-time plot (matplotlib)   │
└─────────────────────────────────┘
```

Each process runs independently. The plant does not know whether the controller uses PID, LQR, or a neural network — it only reads `u` from memory.

---

## SharedMemoryTransport

`SharedMemoryTransport` is a zero-copy IPC bus based on Python's `multiprocessing.shared_memory`. One process creates the block (`create=True`), others connect to it (`create=False`).

```python
# Plant (owner) — creates the memory block
bus_server = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1}, create=True)

# Controller (client) — connects to existing block
transport = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1}, create=False)
```

`{"y": 1, "u": 1}` defines the channel schema: two channels, each holding 1 float64 value. The total shared memory size is `2 × 8 bytes = 16 bytes`.

Benefits over sockets:
- **Zero latency** — no serialisation, no kernel network stack
- **Zero copy** — both processes access the same physical memory pages
- **No coordination** — processes read/write independently at their own rate

---

## Plant (02a_sil_plant.py)

```python
plant_c = tf([10], [1, 3, 10])   # G(s) = 10/(s²+3s+10)
plant_d = c2d(plant_c, dt=0.01)  # ZOH discretisation at 100 Hz
```

`c2d` converts the continuous transfer function to a discrete state-space model using Zero-Order Hold (ZOH). ZOH assumes the input `u` is constant between samples — the standard assumption for digital control.

`PlantAgent` runs the discrete simulation loop:
```
x(k+1) = A·x(k) + B·u(k)
y(k)   = C·x(k) + D·u(k)
```
At each tick it reads `u` from the bus, advances the state, and writes `y` back.

---

## AI Controller (02b_sil_ai_controller.py)

### The neural network

```python
class DummyRLController(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(1, 1)
        with torch.no_grad():
            self.linear.weight.fill_(-0.5)
            self.linear.bias.fill_(1.0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x)
```

A single `nn.Linear(1→1)` layer with fixed weights: `u = -0.5·y + 1.0`. This mimics a proportional controller (Kp = -0.5, offset 1.0). In a real application, the weights would come from training a Reinforcement Learning policy.

### Integration pattern

```python
def ai_control_law(y: np.ndarray) -> np.ndarray:
    state_tensor = torch.tensor(y, dtype=torch.float32)
    with torch.no_grad():
        u = model(state_tensor).numpy()
    return u
```

The key pattern:
1. `numpy → torch.Tensor` — convert sensor reading to PyTorch format
2. `model(state_tensor)` — forward pass (inference, no gradient)
3. `.numpy()` — convert back to numpy for the transport layer

`torch.no_grad()` disables gradient tracking during inference — faster and uses less memory.

### Real-time plot

The controller runs in a **background thread** (`blocking=False`) while the main thread drives the matplotlib animation:

```python
ai_ctrl.start(blocking=False)   # background thread
plt.show()                      # main thread blocks here
```

A `collections.deque(maxlen=300)` acts as a circular buffer (3 s window at 100 Hz). `deque.append()` is thread-safe, so the background thread can write while the main thread reads for plotting.

`FuncAnimation` calls `update()` every 100 ms (10 Hz display rate) — fast enough for visual feedback, slow enough not to compete with the 100 Hz control loop.

---

## Why this pattern matters for AI control

| Traditional controller | AI controller |
|---|---|
| PID, LQR, MPC — derived analytically | Neural network — trained from data |
| White-box: equations known | Black-box: weights learned |
| Easy to prove stability | Hard to guarantee stability |
| `law = lambda y: pid.compute(y[0])` | `law = lambda y: model(tensor(y)).numpy()` |

In synapsys, the `ControllerAgent` accepts **any callable** as `control_law`. Swapping PID for a neural network requires changing only the function — the agent, transport, and timing infrastructure remain identical.

---

## How to run

Open two terminals in the project root:

```bash
# Terminal 1 — start the physics engine first
uv run python examples/advanced/02_sil_ai_controller/02a_sil_plant.py

# Terminal 2 — connect the AI controller (wait ~1s for plant to start)
uv run python examples/advanced/02_sil_ai_controller/02b_sil_ai_controller.py
```

A matplotlib window opens showing `y(t)` (plant output) and `u(t)` (AI control action) in real time. Close the window to stop.

> **Note:** If you get `Address already in use`, run `fuser -k 5555/tcp 5556/tcp` to release stale sockets.
