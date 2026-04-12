# 03 — Real-Time Headless Monitor (Terminal Scope)

## Concept

This is a **read-only bus monitor** — a third process that attaches to an existing shared memory bus and displays the live signal values in the terminal, without interfering with the plant or controller.

It demonstrates the **observer pattern** for distributed simulation: any number of monitors can attach to the bus without affecting the closed-loop dynamics.

### Use cases

- **Debugging** without a GUI (SSH sessions, CI pipelines)
- **Logging** live values to a file (redirect stdout)
- **Sanity checking** before opening a full oscilloscope window
- **Headless environments** where matplotlib is not available

---

## Architecture

```
Plant ──write y──▶ shared memory "sil_bus" ◀──read y, u──▶ Monitor (this script)
                         ▲
Controller ──write u─────┘
```

The monitor connects as a **client** (`create=False`) and only calls `read()` — it never writes to the bus. The plant and controller continue running at their own rates, unaffected.

---

## Code walkthrough

```python
monitor = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1}, create=False)
```

Connects to the existing bus owned by `02a_sil_plant.py`. Raises `FileNotFoundError` if the plant is not running.

```python
while True:
    y = monitor.read("y")[0]
    u = monitor.read("u")[0]
    elapsed = time.time() - start_time

    sys.stdout.write(f"\r[t={elapsed:6.2f}s] Sensor y(t): {y:8.4f} | Inference u(t): {u:8.4f}")
    sys.stdout.flush()
    time.sleep(0.05)
```

`\r` (carriage return) overwrites the current terminal line — creating an in-place update effect without scrolling. `sys.stdout.flush()` forces the output to appear immediately.

`time.sleep(0.05)` = 20 Hz display rate. The actual control loop runs at 100 Hz — this monitor samples it at a lower rate, which is fine for visual inspection.

---

## How to run

Requires `02a_sil_plant.py` and `02b_sil_ai_controller.py` already running:

```bash
# Terminal 1
uv run python examples/advanced/02_sil_ai_controller/02a_sil_plant.py

# Terminal 2
uv run python examples/advanced/02_sil_ai_controller/02b_sil_ai_controller.py

# Terminal 3 — monitor
uv run python examples/advanced/03_realtime_scope/03_realtime_scope.py
```

Press `Ctrl+C` to stop the monitor. The plant and controller keep running.
