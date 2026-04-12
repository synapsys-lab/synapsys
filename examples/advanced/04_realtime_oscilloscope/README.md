# 04 — Real-Time Oscilloscope with Sinusoidal Reference

## Concept

This is the most complete self-contained real-time simulation in the examples. It demonstrates a **three-role architecture** where plant, controller, and visualisation run concurrently without blocking each other:

```
Thread A  →  PlantAgent       (physics engine, 50 Hz)
Thread B  →  ControllerAgent  (PID law, 50 Hz)
Main      →  Oscilloscope     (read-only monitor + matplotlib, 30 Hz)
```

The control objective is **sinusoidal reference tracking**: the setpoint is not a constant but a time-varying signal `r(t) = 3 + 2·sin(2π·0.2·t)`. The PID controller must continuously adjust `u(t)` to keep `y(t)` following `r(t)`.

---

## Plant model

```python
plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT)
```

A first-order system G(s) = 1/(s+1), discretised with ZOH at 50 Hz. Simple but illustrative — the PID has to work to track the sinusoid because the plant has lag.

State-space form:
```
ẋ = -x + u
y  =  x
```

---

## Sinusoidal reference and the time-closure pattern

```python
t_start = time.monotonic()

def _setpoint(t: float) -> float:
    return SP_OFFSET + SP_AMP * np.sin(2.0 * np.pi * SP_FREQ * t)

def law(y: np.ndarray) -> np.ndarray:
    r = _setpoint(time.monotonic() - t_start)
    return np.array([pid.compute(setpoint=r, measurement=y[0])])
```

The control law is a **closure** over `t_start`. Each time the `ControllerAgent` calls `law(y)`, it reads the current wall-clock time, evaluates `r(t)`, and feeds it to the PID. This gives a time-varying setpoint with no external coordination.

The oscilloscope independently recomputes `r(t)` using the same `_setpoint()` function — so the reference trace in the plot is always accurate.

---

## Three-handle bus pattern

```python
owner   = SharedMemoryTransport(BUS, CHANNELS, create=True)   # owns memory
t_plant = SharedMemoryTransport(BUS, CHANNELS)                 # plant agent
t_ctrl  = SharedMemoryTransport(BUS, CHANNELS)                 # controller agent
scope   = SharedMemoryTransport(BUS, CHANNELS)                 # read-only monitor
```

Each agent gets its own handle to the shared memory. Multiple handles to the same bus name are allowed — they all point to the same physical memory pages. The `owner` handle keeps the memory block alive; closing it frees the OS resource.

---

## PID controller

```python
pid = PID(Kp=6.0, Ki=2.0, dt=DT, u_min=-15.0, u_max=15.0)
```

- **Kp = 6.0** — proportional gain; large enough for fast response
- **Ki = 2.0** — integral gain; eliminates steady-state error even for sinusoidal reference (because the error integrated over a full period is non-zero due to lag)
- **u_min / u_max** — anti-windup saturation limits

---

## Rolling window oscilloscope

```python
WINDOW = 200   # samples
buf_t = deque([0.0] * WINDOW, maxlen=WINDOW)
buf_y = deque([0.0] * WINDOW, maxlen=WINDOW)
```

`deque(maxlen=N)` automatically discards the oldest sample when a new one is appended — a circular buffer. With `WINDOW=200` at `DT=0.02`, the plot shows the last `200 × 0.02 = 4 seconds`.

```python
x_min = max(0.0, now - WINDOW * DT)
x_max = x_min + WINDOW * DT
ax_y.set_xlim(x_min, x_max)
```

The x-axis scrolls to always show the most recent `WINDOW` samples — exactly like a real oscilloscope.

---

## FuncAnimation and blit

```python
ani = animation.FuncAnimation(
    fig, _update,
    interval=int(1000 / SCOPE_HZ),   # 33 ms at 30 Hz
    blit=True,
    cache_frame_data=False,
)
```

- `interval` — milliseconds between frames (30 Hz ≈ 33 ms)
- `blit=True` — only redraws the `Artist` objects returned by `_update`, not the full figure; much faster
- `cache_frame_data=False` — prevents matplotlib from storing frames in memory (important for long runs)

`_update` returns a tuple of `Line2D` objects — matplotlib uses this list to know what to redraw.

---

## How to run

Single terminal — everything runs in-process:

```bash
uv run python examples/advanced/04_realtime_oscilloscope/04_realtime_matplotlib.py
```

The oscilloscope window opens immediately. You should see `y(t)` tracking `r(t)` with a small phase lag (due to plant dynamics) and `u(t)` oscillating as the PID compensates. Close the window to stop.
