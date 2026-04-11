"""
Advanced example 05 — Digital Twin with divergence detection
=============================================================

Demonstrates the Digital Twin pattern:

    Physical plant   →  emulated here by a StateSpace with an injected
                        parameter drift (increasing damping) to simulate
                        mechanical wear.

    Virtual twin     →  the original (nominal) StateSpace model running
                        in parallel, fed with the SAME control input u(t).

    Divergence monitor → computes ||y_physical - y_virtual|| at every tick.
                         When divergence exceeds a threshold, an alert fires.

Architecture:
    ┌───────────────────────────────────────────────────────┐
    │  "Physical" plant  (drifting model, hidden from twin)  │
    │  PlantAgent on bus  "physical_bus"                     │
    └──────────────────────────┬────────────────────────────┘
                               │  y_physical, u
    ┌──────────────────────────▼────────────────────────────┐
    │  ControllerAgent  (PID)  on bus  "physical_bus"        │
    └──────────────────────────┬────────────────────────────┘
                               │  (same u fed to twin)
    ┌──────────────────────────▼────────────────────────────┐
    │  Virtual twin  (nominal model, step-by-step in main)   │
    │  Receives the same u each tick, evolves independently  │
    └──────────────────────────┬────────────────────────────┘
                               │
    ┌──────────────────────────▼────────────────────────────┐
    │  Divergence monitor — plots both signals + error       │
    └───────────────────────────────────────────────────────┘

Usage:
    python examples/advanced/05_digital_twin.py
"""

from __future__ import annotations

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import SharedMemoryTransport

# ── Parameters ────────────────────────────────────────────────────────────────
DT        = 0.02      # 50 Hz
SIM_TIME  = 8.0       # seconds
SETPOINT  = 3.0
DRIFT_AT  = 3.0       # seconds at which mechanical wear begins
ALERT_THR = 0.15      # divergence threshold that fires alert

BUS      = "twin_demo"
CHANNELS = {"y": 1, "u": 1}

# ── Nominal model (what engineers designed against) ───────────────────────────
# G(s) = 1/(s + 1)
A_nom = np.array([[-1.0]])
B_nom = np.array([[1.0]])
C_nom = np.array([[1.0]])
D_nom = np.array([[0.0]])
plant_nominal = c2d(ss(A_nom, B_nom, C_nom, D_nom), dt=DT)

# ── "Physical" plant (hidden from twin — adds damping drift after DRIFT_AT s) ─
# Same structure, but A gradually drifts from -1 → -2 after 3 s
def make_drifted_plant(extra_damping: float) -> object:
    """Return a discretised plant with extra_damping added to pole."""
    A_drift = np.array([[-1.0 - extra_damping]])
    return c2d(ss(A_drift, B_nom, C_nom, D_nom), dt=DT)

# ── Transport & agents ────────────────────────────────────────────────────────
owner = SharedMemoryTransport(BUS, CHANNELS, create=True)
owner.write("y", np.array([0.0]))
owner.write("u", np.array([0.0]))

t_plant = SharedMemoryTransport(BUS, CHANNELS)
t_ctrl  = SharedMemoryTransport(BUS, CHANNELS)
monitor = SharedMemoryTransport(BUS, CHANNELS)

pid = PID(Kp=4.0, Ki=1.2, dt=DT, u_min=-15.0, u_max=15.0)
law = lambda y: np.array([pid.compute(setpoint=SETPOINT, measurement=y[0])])

# Start with nominal plant
plant_agent = PlantAgent(
    "physical_plant",
    make_drifted_plant(0.0),      # no drift initially
    t_plant,
    SyncEngine(SyncMode.WALL_CLOCK, dt=DT),
)
ctrl_agent = ControllerAgent(
    "pid_ctrl", law, t_ctrl, SyncEngine(SyncMode.WALL_CLOCK, dt=DT)
)

plant_agent.start(blocking=False)
ctrl_agent.start(blocking=False)

# ── Virtual twin state (evolves in main thread) ───────────────────────────────
x_virtual = np.zeros(plant_nominal.n_states)

# ── Data collection ───────────────────────────────────────────────────────────
log_t:    list[float] = []
log_yp:   list[float] = []   # physical y
log_yv:   list[float] = []   # virtual twin y
log_u:    list[float] = []
log_div:  list[float] = []   # ||y_physical - y_virtual||
alerts:   list[float] = []   # timestamps where divergence exceeded threshold

drift_applied = False
t0 = time.monotonic()

print(f"Digital Twin simulation running for {SIM_TIME}s ...")
print(f"  Nominal model: G(s) = 1/(s+1)")
print(f"  Wear injection at t={DRIFT_AT}s (extra damping +1.0)")
print(f"  Alert threshold: ||divergence|| > {ALERT_THR}\n")

step = 0
while True:
    elapsed = time.monotonic() - t0
    if elapsed >= SIM_TIME:
        break

    # ── Inject wear at DRIFT_AT seconds ──────────────────────────────────
    # In a real digital twin the physical plant changes by itself;
    # here we simulate it by swapping the PlantAgent's internal model.
    # We do this by stopping and restarting the agent (graceful swap).
    if not drift_applied and elapsed >= DRIFT_AT:
        plant_agent.stop()
        plant_agent = PlantAgent(
            "physical_plant_worn",
            make_drifted_plant(1.0),   # pole at -2 instead of -1
            t_plant,
            SyncEngine(SyncMode.WALL_CLOCK, dt=DT),
        )
        plant_agent.start(blocking=False)
        drift_applied = True
        print(f"[t={elapsed:.2f}s] ⚠  Wear injected: plant pole drifted -1 → -2")

    # ── Read from physical bus ────────────────────────────────────────────
    y_physical = monitor.read("y")[0]
    u_current  = monitor.read("u")[0]

    # ── Step virtual twin with the SAME u ────────────────────────────────
    x_virtual, y_virtual_arr = plant_nominal.evolve(
        x_virtual, np.array([u_current])
    )
    y_virtual = float(y_virtual_arr[0])

    # ── Divergence ────────────────────────────────────────────────────────
    divergence = abs(y_physical - y_virtual)

    if divergence > ALERT_THR:
        alerts.append(elapsed)
        if len(alerts) == 1 or (elapsed - alerts[-2]) > 0.5:
            print(f"[t={elapsed:.2f}s] 🔴 ALERT: divergence = {divergence:.4f} > {ALERT_THR}")

    log_t.append(elapsed)
    log_yp.append(y_physical)
    log_yv.append(y_virtual)
    log_u.append(u_current)
    log_div.append(divergence)

    step += 1
    time.sleep(DT)

# ── Cleanup ───────────────────────────────────────────────────────────────────
plant_agent.stop()
ctrl_agent.stop()
monitor.close()
t_plant.close()
t_ctrl.close()
owner.close()

# ── Plot results ──────────────────────────────────────────────────────────────
t_arr   = np.array(log_t)
yp_arr  = np.array(log_yp)
yv_arr  = np.array(log_yv)
u_arr   = np.array(log_u)
div_arr = np.array(log_div)

fig = plt.figure(figsize=(12, 8))
gs  = gridspec.GridSpec(3, 1, hspace=0.45)

# ── Panel 1: physical vs virtual ─────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0])
ax1.plot(t_arr, yp_arr,  lw=1.8,  color="steelblue",  label="y_physical  (real plant)")
ax1.plot(t_arr, yv_arr,  lw=1.5,  color="darkorange", linestyle="--", label="y_virtual   (twin model)")
ax1.axhline(SETPOINT, color="k", linestyle=":", alpha=0.45, label=f"setpoint = {SETPOINT}")
ax1.axvline(DRIFT_AT, color="red", linestyle="--", alpha=0.5, lw=1.2, label=f"wear injected t={DRIFT_AT}s")
ax1.set_ylabel("Output y(t)")
ax1.set_title("Digital Twin — Physical vs Virtual Model")
ax1.legend(fontsize=8, loc="lower right")
ax1.grid(True, alpha=0.3)

# ── Panel 2: divergence ───────────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1])
ax2.plot(t_arr, div_arr, lw=1.6, color="crimson", label="|y_physical − y_virtual|")
ax2.axhline(ALERT_THR, color="red", linestyle="--", lw=1.2, alpha=0.7,
            label=f"alert threshold = {ALERT_THR}")
ax2.axvline(DRIFT_AT, color="red", linestyle="--", alpha=0.5, lw=1.2)
ax2.fill_between(t_arr, div_arr, ALERT_THR,
                 where=(div_arr > ALERT_THR), alpha=0.25, color="red",
                 label="divergence zone")
ax2.set_ylabel("Divergence")
ax2.set_title("Anomaly Detection — Divergence Metric")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

# ── Panel 3: control signal ───────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[2])
ax3.plot(t_arr, u_arr, lw=1.4, color="seagreen", label="u(t) — PID output")
ax3.axvline(DRIFT_AT, color="red", linestyle="--", alpha=0.5, lw=1.2)
ax3.set_ylabel("Control u(t)")
ax3.set_xlabel("Time (s)")
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3)

plt.suptitle("Synapsys — Digital Twin + Mechanical Wear Detection", fontsize=13)
fig.subplots_adjust(top=0.93, hspace=0.50)
plt.show()

total_alerts = sum(1 for i, t in enumerate(log_t) if log_div[i] > ALERT_THR)
print(f"\nSimulation complete. {total_alerts} ticks with divergence > {ALERT_THR}.")
