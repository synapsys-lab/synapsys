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
    │  PlantAgent publishes "twin/y", reads "twin/u"         │
    └──────────────────────────┬────────────────────────────┘
                               │
    ┌──────────────────────────▼────────────────────────────┐
    │  ControllerAgent (PID) reads "twin/y", writes "twin/u" │
    └──────────────────────────┬────────────────────────────┘
                               │  same u fed to virtual twin
    ┌──────────────────────────▼────────────────────────────┐
    │  Virtual twin (main thread) — broker.read("twin/u")    │
    └──────────────────────────┬────────────────────────────┘
                               │
    ┌──────────────────────────▼────────────────────────────┐
    │  Divergence monitor — broker.read() for both signals   │
    └───────────────────────────────────────────────────────┘

Usage:
    python examples/advanced/05_digital_twin/05_digital_twin.py
"""

from __future__ import annotations

import time

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np

from synapsys.agents import ControllerAgent, PlantAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.api import c2d, ss
from synapsys.broker import MessageBroker, SharedMemoryBackend, Topic

# ── Parameters ────────────────────────────────────────────────────────────────
DT = 0.02
SIM_TIME = 8.0
SETPOINT = 3.0
DRIFT_AT = 3.0
ALERT_THR = 0.15

BUS = "twin_demo"

# ── Nominal model ─────────────────────────────────────────────────────────────
A_nom = np.array([[-1.0]])
B_nom = np.array([[1.0]])
C_nom = np.array([[1.0]])
D_nom = np.array([[0.0]])
plant_nominal = c2d(ss(A_nom, B_nom, C_nom, D_nom), dt=DT)


def make_drifted_plant(extra_damping: float) -> object:
    return c2d(ss(np.array([[-1.0 - extra_damping]]), B_nom, C_nom, D_nom), dt=DT)


# ── Broker + topics ────────────────────────────────────────────────────────────
topic_y = Topic("twin/y", shape=(1,))
topic_u = Topic("twin/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend(BUS, [topic_y, topic_u], create=True))

broker.publish("twin/y", np.zeros(1))
broker.publish("twin/u", np.zeros(1))

# ── Control law ───────────────────────────────────────────────────────────────
pid = PID(Kp=4.0, Ki=1.2, dt=DT, u_min=-15.0, u_max=15.0)


def law(y: np.ndarray) -> np.ndarray:
    return np.array([pid.compute(setpoint=SETPOINT, measurement=y[0])])


# ── Agents ────────────────────────────────────────────────────────────────────
def _make_plant_agent(extra_damping: float) -> PlantAgent:
    return PlantAgent(
        "physical_plant",
        make_drifted_plant(extra_damping),
        None,
        SyncEngine(SyncMode.WALL_CLOCK, dt=DT),
        channel_y="twin/y",
        channel_u="twin/u",
        broker=broker,
    )


plant_agent = _make_plant_agent(0.0)
ctrl_agent = ControllerAgent(
    "pid_ctrl",
    law,
    None,
    SyncEngine(SyncMode.WALL_CLOCK, dt=DT),
    channel_y="twin/y",
    channel_u="twin/u",
    broker=broker,
)

plant_agent.start(blocking=False)
ctrl_agent.start(blocking=False)

# ── Virtual twin state ────────────────────────────────────────────────────────
x_virtual = np.zeros(plant_nominal.n_states)

# ── Data collection ───────────────────────────────────────────────────────────
log_t: list[float] = []
log_yp: list[float] = []
log_yv: list[float] = []
log_u: list[float] = []
log_div: list[float] = []
alerts: list[float] = []

drift_applied = False
t0 = time.monotonic()

print(f"Digital Twin simulation running for {SIM_TIME}s ...")
print("  Nominal model: G(s) = 1/(s+1)")
print(f"  Wear injection at t={DRIFT_AT}s (extra damping +1.0)")
print(f"  Alert threshold: ||divergence|| > {ALERT_THR}\n")

while True:
    elapsed = time.monotonic() - t0
    if elapsed >= SIM_TIME:
        break

    if not drift_applied and elapsed >= DRIFT_AT:
        plant_agent.stop()
        plant_agent = _make_plant_agent(1.0)
        plant_agent.start(blocking=False)
        drift_applied = True
        print(f"[t={elapsed:.2f}s] Wear injected: plant pole drifted -1 -> -2")

    # Monitor reads directly from broker (no extra transport handle needed)
    y_physical = broker.read("twin/y")[0]
    u_current = broker.read("twin/u")[0]

    x_virtual, y_virtual_arr = plant_nominal.evolve(x_virtual, np.array([u_current]))
    y_virtual = float(y_virtual_arr[0])

    divergence = abs(y_physical - y_virtual)

    if divergence > ALERT_THR:
        alerts.append(elapsed)
        if len(alerts) == 1 or (elapsed - alerts[-2]) > 0.5:
            print(
                f"[t={elapsed:.2f}s] ALERT: divergence = {divergence:.4f} > {ALERT_THR}"
            )

    log_t.append(elapsed)
    log_yp.append(y_physical)
    log_yv.append(y_virtual)
    log_u.append(u_current)
    log_div.append(divergence)

    time.sleep(DT)

# ── Cleanup ───────────────────────────────────────────────────────────────────
plant_agent.stop()
ctrl_agent.stop()
broker.close()

# ── Plot results ──────────────────────────────────────────────────────────────
t_arr = np.array(log_t)
yp_arr = np.array(log_yp)
yv_arr = np.array(log_yv)
u_arr = np.array(log_u)
div_arr = np.array(log_div)

fig = plt.figure(figsize=(12, 8))
gs = gridspec.GridSpec(3, 1, hspace=0.45)

ax1 = fig.add_subplot(gs[0])
ax1.plot(t_arr, yp_arr, lw=1.8, color="steelblue", label="y_physical  (real plant)")
ax1.plot(
    t_arr,
    yv_arr,
    lw=1.5,
    color="darkorange",
    linestyle="--",
    label="y_virtual   (twin model)",
)
ax1.axhline(
    SETPOINT, color="k", linestyle=":", alpha=0.45, label=f"setpoint = {SETPOINT}"
)
ax1.axvline(
    DRIFT_AT,
    color="red",
    linestyle="--",
    alpha=0.5,
    lw=1.2,
    label=f"wear injected t={DRIFT_AT}s",
)
ax1.set_ylabel("Output y(t)")
ax1.set_title("Digital Twin — Physical vs Virtual Model")
ax1.legend(fontsize=8, loc="lower right")
ax1.grid(True, alpha=0.3)

ax2 = fig.add_subplot(gs[1])
ax2.plot(t_arr, div_arr, lw=1.6, color="crimson", label="|y_physical - y_virtual|")
ax2.axhline(
    ALERT_THR,
    color="red",
    linestyle="--",
    lw=1.2,
    alpha=0.7,
    label=f"alert threshold = {ALERT_THR}",
)
ax2.axvline(DRIFT_AT, color="red", linestyle="--", alpha=0.5, lw=1.2)
ax2.fill_between(
    t_arr,
    div_arr,
    ALERT_THR,
    where=(div_arr > ALERT_THR),
    alpha=0.25,
    color="red",
    label="divergence zone",
)
ax2.set_ylabel("Divergence")
ax2.set_title("Anomaly Detection — Divergence Metric")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

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
