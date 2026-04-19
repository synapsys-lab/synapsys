"""
Advanced example 04 — Real-time oscilloscope with matplotlib.animation
======================================================================

Launches a PlantAgent + ControllerAgent on a MessageBroker (shared memory)
and opens a live-updating plot WITHOUT blocking the simulation loop.

Architecture (three independent roles):
    PlantAgent      → publishes "scope/y" at 50 Hz
    ControllerAgent → reads "scope/y", publishes "scope/u" at 50 Hz
    Oscilloscope    → reads both topics as a read-only observer via broker.read()

The reference signal r(t) = SP_OFFSET + SP_AMP * sin(2π * SP_FREQ * t).

Usage:
    python examples/advanced/04_realtime_oscilloscope/04_realtime_matplotlib.py

Dependencies:
    matplotlib (already in dev dependencies)
"""

from __future__ import annotations

import time
from collections import deque

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from synapsys.agents import ControllerAgent, PlantAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.api import c2d, ss
from synapsys.broker import MessageBroker, SharedMemoryBackend, Topic

# ── Simulation parameters ─────────────────────────────────────────────────────
BUS = "scope_demo"
DT = 0.02  # 50 Hz
WINDOW = 200  # samples shown in the rolling window
SCOPE_HZ = 30  # oscilloscope refresh rate (frames per second)

SP_AMP = 2.0
SP_FREQ = 0.2
SP_OFFSET = 3.0

# ── 1. Build plant ────────────────────────────────────────────────────────────
plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT)

# ── 2. Broker + topics ────────────────────────────────────────────────────────
topic_y = Topic("scope/y", shape=(1,))
topic_u = Topic("scope/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_y)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend(BUS, [topic_y, topic_u], create=True))

broker.publish("scope/y", np.zeros(1))
broker.publish("scope/u", np.zeros(1))

# ── 3. Reference + control law ────────────────────────────────────────────────
t_start = time.monotonic()


def _setpoint(t: float) -> float:
    return SP_OFFSET + SP_AMP * np.sin(2.0 * np.pi * SP_FREQ * t)


pid = PID(Kp=6.0, Ki=2.0, dt=DT, u_min=-15.0, u_max=15.0)


def law(y: np.ndarray) -> np.ndarray:
    r = _setpoint(time.monotonic() - t_start)
    return np.array([pid.compute(setpoint=r, measurement=y[0])])


# ── 4. Launch agents in background threads ────────────────────────────────────
plant_agent = PlantAgent(
    "plant",
    plant_d,
    None,
    SyncEngine(SyncMode.WALL_CLOCK, dt=DT),
    channel_y="scope/y",
    channel_u="scope/u",
    broker=broker,
)
ctrl_agent = ControllerAgent(
    "ctrl",
    law,
    None,
    SyncEngine(SyncMode.WALL_CLOCK, dt=DT),
    channel_y="scope/y",
    channel_u="scope/u",
    broker=broker,
)
plant_agent.start(blocking=False)
ctrl_agent.start(blocking=False)

# ── 5. Rolling buffers (oscilloscope reads directly from broker) ──────────────
buf_t = deque([0.0] * WINDOW, maxlen=WINDOW)
buf_y = deque([0.0] * WINDOW, maxlen=WINDOW)
buf_r = deque([SP_OFFSET] * WINDOW, maxlen=WINDOW)
buf_u = deque([0.0] * WINDOW, maxlen=WINDOW)

# ── 6. Matplotlib figure ──────────────────────────────────────────────────────
fig, (ax_y, ax_u) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
fig.suptitle("Synapsys — Real-Time Oscilloscope (sinusoidal reference)", fontsize=13)

(line_y,) = ax_y.plot([], [], lw=1.6, color="steelblue", label="y(t) — output")
(line_sp,) = ax_y.plot(
    [],
    [],
    lw=1.4,
    color="black",
    linestyle="--",
    label=f"r(t) = {SP_OFFSET}+{SP_AMP}·sin(2π·{SP_FREQ}t)",
)
ax_y.set_ylabel("y(t)")
ax_y.set_ylim(SP_OFFSET - SP_AMP * 2.0, SP_OFFSET + SP_AMP * 2.0)
ax_y.legend(loc="upper left", fontsize=8)

(line_u,) = ax_u.plot([], [], lw=1.6, color="darkorange", label="u(t) — control")
ax_u.set_ylabel("u(t)")
ax_u.set_xlabel("Time (s)")
ax_u.set_ylim(-16, 16)
ax_u.legend(loc="upper left", fontsize=8)

for ax in (ax_y, ax_u):
    ax.grid(True, alpha=0.3)

fig.tight_layout()


def _update(_frame: int) -> tuple:
    now = time.monotonic() - t_start
    y_val = broker.read("scope/y")[0]  # observer reads directly from broker
    u_val = broker.read("scope/u")[0]
    r_val = _setpoint(now)

    buf_t.append(now)
    buf_y.append(y_val)
    buf_r.append(r_val)
    buf_u.append(u_val)

    t_arr = list(buf_t)
    line_y.set_data(t_arr, list(buf_y))
    line_sp.set_data(t_arr, list(buf_r))
    line_u.set_data(t_arr, list(buf_u))

    x_min = max(0.0, now - WINDOW * DT)
    x_max = x_min + WINDOW * DT
    ax_y.set_xlim(x_min, x_max)
    ax_u.set_xlim(x_min, x_max)

    return line_y, line_sp, line_u


ani = animation.FuncAnimation(
    fig,
    _update,
    interval=int(1000 / SCOPE_HZ),
    blit=True,
    cache_frame_data=False,
)

print("Oscilloscope running — close the window to stop.")

try:
    plt.show(block=True)
    while plt.get_fignums():
        plt.pause(0.1)
finally:
    plant_agent.stop()
    ctrl_agent.stop()
    broker.close()
    print("Simulation stopped.")
