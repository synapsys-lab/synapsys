"""
Advanced example 04 — Real-time oscilloscope with matplotlib.animation
======================================================================

Launches a PlantAgent + ControllerAgent on a shared-memory bus and opens a
live-updating plot WITHOUT blocking the simulation loop.

Architecture (three independent roles):
    Process / Thread A  →  PlantAgent       (physics engine)
    Process / Thread B  →  ControllerAgent  (PID law, sinusoidal reference)
    Main thread         →  Oscilloscope     (read-only monitor + matplotlib)

The oscilloscope attaches to the bus as a third read-only handle.  The two
simulation agents never know it exists and are not slowed down by GUI rendering.

The reference signal r(t) = SP_OFFSET + SP_AMP * sin(2π * SP_FREQ * t) is a
sinusoid shared between the control law (via closure over time.monotonic) and
the oscilloscope (recomputed each frame for the reference trace).

Usage:
    python examples/advanced/04_realtime_matplotlib.py

Dependencies:
    matplotlib (already in dev dependencies)
"""

from __future__ import annotations

import time
from collections import deque

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

from synapsys.api import ss, c2d
from synapsys.agents import PlantAgent, ControllerAgent, SyncEngine, SyncMode
from synapsys.algorithms import PID
from synapsys.transport import SharedMemoryTransport

# ── Simulation parameters ─────────────────────────────────────────────────────
BUS      = "scope_demo"
CHANNELS = {"y": 1, "u": 1}
DT       = 0.02       # 50 Hz
WINDOW   = 200        # samples shown in the rolling window
SCOPE_HZ = 30         # oscilloscope refresh rate (frames per second)

# Sinusoidal reference:  r(t) = SP_OFFSET + SP_AMP * sin(2π * SP_FREQ * t)
SP_AMP    = 2.0        # amplitude  [same units as y]
SP_FREQ   = 0.2        # frequency  [Hz]  → 5 s period
SP_OFFSET = 3.0        # DC offset  (keeps r(t) well above zero)

# ── 1. Build plant ────────────────────────────────────────────────────────────
plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT)

# ── 2. Create transport owner and initialise channels ─────────────────────────
owner = SharedMemoryTransport(BUS, CHANNELS, create=True)
owner.write("y", np.array([0.0]))
owner.write("u", np.array([0.0]))

# ── 3. Per-agent transport handles ────────────────────────────────────────────
t_plant = SharedMemoryTransport(BUS, CHANNELS)
t_ctrl  = SharedMemoryTransport(BUS, CHANNELS)

# ── 4. Reference + control law ────────────────────────────────────────────────
t_start = time.monotonic()

def _setpoint(t: float) -> float:
    """Sinusoidal reference evaluated at wall-clock time t (seconds)."""
    return SP_OFFSET + SP_AMP * np.sin(2.0 * np.pi * SP_FREQ * t)

pid = PID(Kp=6.0, Ki=2.0, dt=DT, u_min=-15.0, u_max=15.0)

def law(y: np.ndarray) -> np.ndarray:
    """PID law with time-varying setpoint sampled at call time."""
    r = _setpoint(time.monotonic() - t_start)
    return np.array([pid.compute(setpoint=r, measurement=y[0])])

# ── 5. Launch agents in background threads ────────────────────────────────────
plant_agent = PlantAgent("plant", plant_d, t_plant,
                         SyncEngine(SyncMode.WALL_CLOCK, dt=DT))
ctrl_agent  = ControllerAgent("ctrl", law, t_ctrl,
                              SyncEngine(SyncMode.WALL_CLOCK, dt=DT))
plant_agent.start(blocking=False)
ctrl_agent.start(blocking=False)

# ── 6. Read-only oscilloscope handle ─────────────────────────────────────────
scope = SharedMemoryTransport(BUS, CHANNELS)

# Rolling buffers
buf_t = deque([0.0] * WINDOW, maxlen=WINDOW)
buf_y = deque([0.0] * WINDOW, maxlen=WINDOW)
buf_r = deque([SP_OFFSET] * WINDOW, maxlen=WINDOW)   # reference trace
buf_u = deque([0.0] * WINDOW, maxlen=WINDOW)

# ── 7. Matplotlib figure ──────────────────────────────────────────────────────
fig, (ax_y, ax_u) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
fig.suptitle("Synapsys — Real-Time Oscilloscope (sinusoidal reference)", fontsize=13)

line_y,  = ax_y.plot([], [], lw=1.6, color="steelblue",
                     label="y(t) — output")
line_sp, = ax_y.plot([], [], lw=1.4, color="black", linestyle="--",
                     label=f"r(t) = {SP_OFFSET}+{SP_AMP}·sin(2π·{SP_FREQ}t)")
ax_y.set_ylabel("y(t)")
ax_y.set_ylim(SP_OFFSET - SP_AMP * 2.0, SP_OFFSET + SP_AMP * 2.0)
ax_y.legend(loc="upper left", fontsize=8)

line_u, = ax_u.plot([], [], lw=1.6, color="darkorange", label="u(t) — control")
ax_u.set_ylabel("u(t)")
ax_u.set_xlabel("Time (s)")
ax_u.set_ylim(-16, 16)
ax_u.legend(loc="upper left", fontsize=8)

for ax in (ax_y, ax_u):
    ax.grid(True, alpha=0.3)

fig.tight_layout()


def _update(_frame: int) -> tuple:
    """Called by FuncAnimation at SCOPE_HZ.  Reads bus, updates lines."""
    now   = time.monotonic() - t_start
    y_val = scope.read("y")[0]
    u_val = scope.read("u")[0]
    r_val = _setpoint(now)

    buf_t.append(now)
    buf_y.append(y_val)
    buf_r.append(r_val)
    buf_u.append(u_val)

    t_arr = list(buf_t)
    line_y.set_data(t_arr,  list(buf_y))
    line_sp.set_data(t_arr, list(buf_r))
    line_u.set_data(t_arr,  list(buf_u))

    # Slide x-axis window
    x_min = max(0.0, now - WINDOW * DT)
    x_max = x_min + WINDOW * DT
    ax_y.set_xlim(x_min, x_max)
    ax_u.set_xlim(x_min, x_max)

    return line_y, line_sp, line_u


ani = animation.FuncAnimation(
    fig,
    _update,
    interval=int(1000 / SCOPE_HZ),   # ms between frames
    blit=True,
    cache_frame_data=False,
)

print("Oscilloscope running — close the window to stop.")

try:
    plt.show(block=True)              # blocks until window is closed by user
    # Fallback: if show() returns immediately (headless CI), keep event loop alive
    while plt.get_fignums():
        plt.pause(0.1)
finally:
    plant_agent.stop()
    ctrl_agent.stop()
    scope.close()
    t_plant.close()
    t_ctrl.close()
    owner.close()
    print("Simulation stopped.")
