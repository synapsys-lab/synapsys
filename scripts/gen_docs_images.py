"""
Generate all documentation images for the examples section.
Run with: MPLBACKEND=Agg uv run python scripts/gen_docs_images.py
"""

import sys
import time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

OUT = Path("website/static/img/examples")
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).parent.parent))
from synapsys.api import tf, ss, c2d, step
from synapsys.algorithms import PID

STYLE = {
    "blue":   "#2563eb",
    "red":    "#dc2626",
    "green":  "#16a34a",
    "orange": "#ea580c",
    "gray":   "#6b7280",
    "purple": "#7c3aed",
}

# ── 1. Step response ──────────────────────────────────────────────────────────
print("Generating 01_step_response.png ...")
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2*zeta*wn, wn**2])
t, y = step(G)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(t, y, color=STYLE["blue"], lw=2, label="y(t) — step response")
ax.axhline(1.0, color=STYLE["gray"], ls="--", lw=1.2, alpha=0.7, label="setpoint = 1")
ax.fill_between(t, y, 1.0, where=(y > 1.0), alpha=0.12, color=STYLE["red"], label="overshoot")
ax.fill_between(t, y, 1.0, where=(y < 1.0), alpha=0.08, color=STYLE["blue"])
ax.set_title(r"Step Response — $G(s) = \dfrac{100}{s^2 + 10s + 100}$  ($\zeta=0.5$, $\omega_n=10$)", fontsize=11)
ax.set_xlabel("Time (s)")
ax.set_ylabel("y(t)")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "01_step_response.png", dpi=150)
plt.close(fig)

# ── 2. Custom signals ─────────────────────────────────────────────────────────
print("Generating 02_custom_signals.png ...")
G2 = tf([10], [1, 5, 10])
t2 = np.linspace(0, 10, 1000)
u_sine = np.sin(2 * np.pi * 1.5 * t2)
u_step = np.where(t2 >= 5, 2.0, 0.0)
u_total = u_sine + u_step
t_out, y_out = G2.simulate(t2, u_total)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
ax1.plot(t_out, u_total, color=STYLE["orange"], lw=1.5, label="u(t) — sine (1.5 Hz) + step at t=5s")
ax1.axvline(5.0, color=STYLE["gray"], ls="--", lw=1, alpha=0.6)
ax1.set_ylabel("Input u(t)")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.plot(t_out, y_out, color=STYLE["blue"], lw=2, label="y(t) — plant output")
ax2.axvline(5.0, color=STYLE["gray"], ls="--", lw=1, alpha=0.6, label="step injection at t=5s")
ax2.set_ylabel("Output y(t)")
ax2.set_xlabel("Time (s)")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
fig.suptitle(r"Custom Signal Injection — $G(s) = \dfrac{10}{s^2 + 5s + 10}$", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "02_custom_signals.png", dpi=150)
plt.close(fig)

# ── 3. SIL AI controller (batch simulation) ───────────────────────────────────
print("Generating 03_sil_ai_controller.png ...")
# Simulate the closed loop manually for documentation
plant_c = tf([10], [1, 3, 10])
plant_d = c2d(plant_c, dt=0.01)
x = np.zeros(plant_d.n_states)

N = 800
t3 = np.arange(N) * 0.01
y3, u3 = np.zeros(N), np.zeros(N)

for k in range(N):
    _, y_arr = plant_d.evolve(x, np.array([u3[k-1] if k > 0 else 0.0]))
    y3[k] = float(y_arr[0])
    x, _ = plant_d.evolve(x, np.array([u3[k-1] if k > 0 else 0.0]))
    # AI (linear): u = -0.5*y + 1.0
    u3[k] = -0.5 * y3[k] + 1.0

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
ax1.plot(t3, y3, color=STYLE["blue"], lw=1.8, label="y(t) — plant output")
ax1.set_ylabel("y(t)")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.plot(t3, u3, color=STYLE["red"], lw=1.8, label="u(t) — AI control action")
ax2.set_ylabel("u(t)")
ax2.set_xlabel("Time (s)")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
fig.suptitle("SIL — AI Controller (DummyRLController, PyTorch linear layer)", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "03_sil_ai_controller.png", dpi=150)
plt.close(fig)

# ── 4. Real-time oscilloscope — PID + sinusoidal reference ───────────────────
print("Generating 04_realtime_oscilloscope.png ...")
DT4 = 0.02
N4  = 500
t4  = np.arange(N4) * DT4

SP_AMP, SP_FREQ, SP_OFF = 2.0, 0.2, 3.0
r4 = SP_OFF + SP_AMP * np.sin(2 * np.pi * SP_FREQ * t4)

plant4 = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT4)
pid4   = PID(Kp=6.0, Ki=2.0, dt=DT4, u_min=-15.0, u_max=15.0)
x4     = np.zeros(plant4.n_states)
y4, u4 = np.zeros(N4), np.zeros(N4)

for k in range(N4):
    x4, y_arr = plant4.evolve(x4, np.array([u4[k-1] if k > 0 else 0.0]))
    y4[k] = float(y_arr[0])
    u4[k] = pid4.compute(setpoint=r4[k], measurement=y4[k])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
ax1.plot(t4, r4, color=STYLE["gray"], lw=1.4, ls="--", label="r(t) — reference")
ax1.plot(t4, y4, color=STYLE["blue"], lw=2.0, label="y(t) — plant output")
ax1.set_ylabel("y(t)")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.plot(t4, u4, color=STYLE["orange"], lw=1.8, label="u(t) — PID output")
ax2.set_ylabel("u(t)")
ax2.set_xlabel("Time (s)")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
fig.suptitle("Real-Time Oscilloscope — PID tracking sinusoidal reference", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "04_realtime_oscilloscope.png", dpi=150)
plt.close(fig)

# ── 5. Digital Twin ───────────────────────────────────────────────────────────
print("Generating 05_digital_twin.png ...")
DT5      = 0.02
SIM5     = 8.0
DRIFT_AT = 3.0
SETP5    = 3.0
N5       = int(SIM5 / DT5)
t5       = np.arange(N5) * DT5

plant_nom5   = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT5)
plant_drift5 = c2d(ss([[-2.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT5)
pid5 = PID(Kp=4.0, Ki=1.2, dt=DT5, u_min=-15.0, u_max=15.0)

x_phys = np.zeros(plant_nom5.n_states)
x_virt = np.zeros(plant_nom5.n_states)
yp5, yv5, u5, div5 = np.zeros(N5), np.zeros(N5), np.zeros(N5), np.zeros(N5)

for k in range(N5):
    plant_k = plant_drift5 if t5[k] >= DRIFT_AT else plant_nom5
    x_phys, y_p = plant_k.evolve(x_phys, np.array([u5[k-1] if k > 0 else 0.0]))
    x_virt, y_v = plant_nom5.evolve(x_virt, np.array([u5[k-1] if k > 0 else 0.0]))
    yp5[k] = float(y_p[0])
    yv5[k] = float(y_v[0])
    div5[k] = abs(yp5[k] - yv5[k])
    u5[k]  = pid5.compute(setpoint=SETP5, measurement=yp5[k])

ALERT_THR = 0.15
fig = plt.figure(figsize=(10, 7))
gs  = gridspec.GridSpec(3, 1, hspace=0.5)

ax1 = fig.add_subplot(gs[0])
ax1.plot(t5, yp5, color=STYLE["blue"],   lw=1.8, label="y_physical (drifting)")
ax1.plot(t5, yv5, color=STYLE["orange"], lw=1.5, ls="--", label="y_virtual (nominal twin)")
ax1.axhline(SETP5, color=STYLE["gray"], ls=":", alpha=0.5, label=f"setpoint = {SETP5}")
ax1.axvline(DRIFT_AT, color=STYLE["red"], ls="--", lw=1.2, alpha=0.6, label="wear injected")
ax1.set_ylabel("Output y(t)")
ax1.set_title("Digital Twin — Physical vs Virtual")
ax1.legend(fontsize=8, loc="lower right")
ax1.grid(True, alpha=0.3)

ax2 = fig.add_subplot(gs[1])
ax2.plot(t5, div5, color="crimson", lw=1.8, label="|y_physical − y_virtual|")
ax2.axhline(ALERT_THR, color="red", ls="--", lw=1.2, alpha=0.7, label=f"alert threshold = {ALERT_THR}")
ax2.axvline(DRIFT_AT, color=STYLE["red"], ls="--", lw=1.2, alpha=0.6)
ax2.fill_between(t5, div5, ALERT_THR, where=(div5 > ALERT_THR), alpha=0.25, color="red", label="alert zone")
ax2.set_ylabel("Divergence")
ax2.set_title("Anomaly Detection")
ax2.legend(fontsize=8)
ax2.grid(True, alpha=0.3)

ax3 = fig.add_subplot(gs[2])
ax3.plot(t5, u5, color=STYLE["green"], lw=1.5, label="u(t) — PID")
ax3.axvline(DRIFT_AT, color=STYLE["red"], ls="--", lw=1.2, alpha=0.6)
ax3.set_ylabel("u(t)")
ax3.set_xlabel("Time (s)")
ax3.legend(fontsize=8)
ax3.grid(True, alpha=0.3)

fig.suptitle("Synapsys — Digital Twin + Mechanical Wear Detection", fontsize=12)
fig.savefig(OUT / "05_digital_twin.png", dpi=150)
plt.close(fig)

print(f"\nAll images saved to {OUT}/")
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name}")
