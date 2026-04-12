# 05 — Digital Twin with Anomaly Detection

## Concept

A **Digital Twin** is a virtual replica of a physical system that runs in parallel with the real system, fed with the same inputs. The twin's purpose is **anomaly detection**: if the real system starts behaving differently from the model, it indicates wear, damage, or parameter drift.

```
Same u(t) ──▶  Physical plant  ──▶  y_physical(t)  ┐
           │                                         ├──▶ divergence(t) = |y_p - y_v|
           └──▶  Virtual twin  ──▶  y_virtual(t)   ┘
                 (nominal model)
```

When `divergence > threshold`, an alert fires — the physical system has deviated from its nominal behaviour.

### Real-world applications

- **Predictive maintenance** — detect bearing wear before failure
- **Structural health monitoring** — bridges, aircraft, industrial machines
- **Process control** — detect fouling in heat exchangers, valve degradation
- **Autonomous vehicles** — detect actuator degradation in flight/drive

---

## Architecture

```
PlantAgent  (physical, may drift)  ──▶  shared memory "twin_demo"
ControllerAgent  (PID)             ──▶  shared memory "twin_demo"
Main thread:
    ├── reads y_physical from bus
    ├── steps virtual twin with same u
    ├── computes divergence
    └── logs everything for final plot
```

The virtual twin is **not** an agent — it runs synchronously in the main thread via `plant_nominal.evolve()`. This keeps the comparison tight: every time the main thread reads from the bus, it immediately steps the twin with the same `u`.

---

## Wear injection

```python
def make_drifted_plant(extra_damping: float):
    A_drift = np.array([[-1.0 - extra_damping]])
    return c2d(ss(A_drift, B_nom, C_nom, D_nom), dt=DT)
```

The nominal plant has pole at s = -1 (G(s) = 1/(s+1)). After `DRIFT_AT = 3.0s`, the physical plant's pole shifts to s = -2 (extra damping +1.0) — simulating mechanical wear that makes the system respond faster but differently from the model.

The swap is done by stopping the `PlantAgent` and restarting it with the drifted model:

```python
if not drift_applied and elapsed >= DRIFT_AT:
    plant_agent.stop()
    plant_agent = PlantAgent("physical_plant_worn", make_drifted_plant(1.0), ...)
    plant_agent.start(blocking=False)
    drift_applied = True
```

This is a **hot swap** — the bus and controller keep running, only the plant model changes.

---

## Virtual twin evolution

```python
x_virtual, y_virtual_arr = plant_nominal.evolve(
    x_virtual, np.array([u_current])
)
y_virtual = float(y_virtual_arr[0])
```

`evolve(x, u)` advances the state-space model one step:
```
x(k+1) = A·x(k) + B·u(k)
y(k)   = C·x(k) + D·u(k)
```

The twin maintains its own state `x_virtual` — it is completely independent of the physical plant's internal state.

---

## Divergence metric

```python
divergence = abs(y_physical - y_virtual)

if divergence > ALERT_THR:
    alerts.append(elapsed)
    print(f"[t={elapsed:.2f}s] ALERT: divergence = {divergence:.4f}")
```

This is an L1 norm (absolute difference). More sophisticated implementations use:
- **L2 norm** over a sliding window (smoother, less sensitive to noise)
- **Kalman filter innovation** (statistically optimal anomaly detection)
- **Mahalanobis distance** (accounts for measurement covariance)

---

## Results plot

Three panels:
1. **Physical vs Virtual** — both outputs overlaid; divergence appears after the wear injection at t=3s
2. **Divergence metric** — red fill shows where `|y_p - y_v| > threshold`; the alert zone grows after wear
3. **Control signal** — PID output `u(t)`; it compensates more aggressively after wear because the plant responds differently

---

## How to run

Single terminal — self-contained, runs for 8 seconds then plots:

```bash
uv run python examples/advanced/05_digital_twin/05_digital_twin.py
```

Expected terminal output:
```
[t=3.00s] ⚠  Wear injected: plant pole drifted -1 → -2
[t=3.05s] 🔴 ALERT: divergence = 0.1823 > 0.15
...
Simulation complete. N ticks with divergence > 0.15.
```

After 8s the matplotlib figure appears showing all three panels.
