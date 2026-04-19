"""
Generate all documentation images for the examples section.
Run with: MPLBACKEND=Agg uv run python scripts/gen_docs_images.py
"""

import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

OUT = Path("website/static/img/examples")
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).parent.parent))
from synapsys.algorithms import PID
from synapsys.api import c2d, ss, step, tf

STYLE = {
    "blue": "#2563eb",
    "red": "#dc2626",
    "green": "#16a34a",
    "orange": "#ea580c",
    "gray": "#6b7280",
    "purple": "#7c3aed",
}

# ── 1. Step response ──────────────────────────────────────────────────────────
print("Generating 01_step_response.png ...")
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2 * zeta * wn, wn**2])
t, y = step(G)

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(t, y, color=STYLE["blue"], lw=2, label="y(t) — step response")
ax.axhline(1.0, color=STYLE["gray"], ls="--", lw=1.2, alpha=0.7, label="setpoint = 1")
ax.fill_between(
    t, y, 1.0, where=(y > 1.0), alpha=0.12, color=STYLE["red"], label="overshoot"
)
ax.fill_between(t, y, 1.0, where=(y < 1.0), alpha=0.08, color=STYLE["blue"])
ax.set_title(
    r"Step Response — $G(s) = \dfrac{100}{s^2 + 10s + 100}$  ($\zeta=0.5$, $\omega_n=10$)",
    fontsize=11,
)
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
ax1.plot(
    t_out,
    u_total,
    color=STYLE["orange"],
    lw=1.5,
    label="u(t) — sine (1.5 Hz) + step at t=5s",
)
ax1.axvline(5.0, color=STYLE["gray"], ls="--", lw=1, alpha=0.6)
ax1.set_ylabel("Input u(t)")
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

ax2.plot(t_out, y_out, color=STYLE["blue"], lw=2, label="y(t) — plant output")
ax2.axvline(
    5.0, color=STYLE["gray"], ls="--", lw=1, alpha=0.6, label="step injection at t=5s"
)
ax2.set_ylabel("Output y(t)")
ax2.set_xlabel("Time (s)")
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
fig.suptitle(
    r"Custom Signal Injection — $G(s) = \dfrac{10}{s^2 + 5s + 10}$", fontsize=11
)
fig.tight_layout()
fig.savefig(OUT / "02_custom_signals.png", dpi=150)
plt.close(fig)

# ── 3. SIL — Neural-LQR controller on 2-DOF mass-spring-damper ──────────────
print("Generating 03_sil_ai_controller.png ...")
from synapsys.algorithms import lqr
from synapsys.utils import StateEquations

M3, C3, K3 = 1.0, 0.1, 2.0
DT3 = 0.01
N3 = 1200
X2_REF3 = 1.0

eqs3 = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1)
    .eq("x2", v2=1)
    .eq("v1", x1=-2 * K3 / M3, x2=K3 / M3, v1=-C3 / M3)
    .eq("v2", x1=K3 / M3, x2=-2 * K3 / M3, v2=-C3 / M3, F=K3 / M3)
)
K_lqr, _ = lqr(eqs3.A, eqs3.B, np.diag([1.0, 10.0, 0.5, 1.0]), np.array([[1.0]]))
A_cl3 = eqs3.A - eqs3.B @ K_lqr
Nbar3 = float(
    -1.0 / (np.array([[0, 1, 0, 0]]) @ np.linalg.inv(A_cl3) @ eqs3.B).squeeze()
)

G3 = ss(eqs3.A, eqs3.B, np.eye(4), np.zeros((4, 1)))
G3d = c2d(G3, dt=DT3)
x3 = np.zeros(4)
t3 = np.arange(N3) * DT3
x1_3, x2_3, v1_3, v2_3, u3 = (np.zeros(N3) for _ in range(5))

for k in range(N3):
    u_k = float(np.dot(-K_lqr.flatten(), x3)) + Nbar3 * X2_REF3
    u_k = np.clip(u_k, -20.0, 20.0)
    x3, y3_arr = G3d.evolve(x3, np.array([u_k]))
    x1_3[k] = float(y3_arr[0])
    x2_3[k] = float(y3_arr[1])
    v1_3[k] = float(y3_arr[2])
    v2_3[k] = float(y3_arr[3])
    u3[k] = u_k

# ── Scientific dark-theme figure ──────────────────────────────────────────────
BG_FIG = "#0f172a"
BG_AX = "#1e293b"
COL_GRID = "#334155"
COL_TXT = "#e2e8f0"
COL_AX = "#94a3b8"

fig3 = plt.figure(figsize=(13, 8), facecolor=BG_FIG)
fig3.suptitle(
    "Neural-LQR — 2-DOF Mass-Spring-Damper  (SIL batch simulation)",
    color=COL_TXT,
    fontsize=13,
    fontweight="bold",
    y=0.97,
)
gs3 = gridspec.GridSpec(
    3,
    2,
    figure=fig3,
    hspace=0.48,
    wspace=0.35,
    left=0.08,
    right=0.97,
    top=0.91,
    bottom=0.08,
)


def _ax3(r, c, title, ylabel, xlabel=None):
    ax = fig3.add_subplot(gs3[r, c])
    ax.set_facecolor(BG_AX)
    ax.tick_params(colors=COL_AX, labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor(COL_GRID)
    ax.grid(True, color=COL_GRID, linewidth=0.5, alpha=0.7)
    ax.set_title(title, color=COL_TXT, fontsize=9.5, pad=5)
    ax.set_ylabel(ylabel, color=COL_AX, fontsize=8.5)
    if xlabel:
        ax.set_xlabel(xlabel, color=COL_AX, fontsize=8.5)
    return ax


ax_p = fig3.add_subplot(gs3[0, :])  # positions — full width
ax_v = _ax3(1, 0, "Velocities  v₁(t), v₂(t)", "Velocity (m/s)", "Time (s)")
ax_f = _ax3(1, 1, "Control force  F(t)  [Neural-LQR output]", "Force (N)", "Time (s)")
ax_ph = fig3.add_subplot(gs3[2, :])  # phase portrait — full width

for ax in [ax_p, ax_ph]:
    ax.set_facecolor(BG_AX)
    ax.tick_params(colors=COL_AX, labelsize=8)
    for sp in ax.spines.values():
        sp.set_edgecolor(COL_GRID)
    ax.grid(True, color=COL_GRID, linewidth=0.5, alpha=0.7)

# ── settle index ──────────────────────────────────────────────────────────────
tol = 0.02
settled_idx = np.where(np.abs(x2_3 - X2_REF3) <= tol)[0]
t_settle = t3[settled_idx[0]] if len(settled_idx) else t3[-1]
os_pct = (max(x2_3) - X2_REF3) / X2_REF3 * 100 if max(x2_3) > X2_REF3 else 0.0

# ── Position panel ────────────────────────────────────────────────────────────
ax_p.set_title(
    "Position tracking — x₁(t) and x₂(t) → setpoint", color=COL_TXT, fontsize=10, pad=6
)
ax_p.set_ylabel("Position (m)", color=COL_AX, fontsize=9)
ax_p.set_xlabel("Time (s)", color=COL_AX, fontsize=9)
ax_p.axhline(
    X2_REF3,
    color=STYLE["green"],
    ls="--",
    lw=1.2,
    alpha=0.6,
    label=f"setpoint r = {X2_REF3} m",
)
ax_p.axhspan(X2_REF3 * 0.98, X2_REF3 * 1.02, alpha=0.07, color=STYLE["green"])
ax_p.axvline(
    t_settle,
    color=STYLE["orange"],
    ls="--",
    lw=1.2,
    alpha=0.8,
    label=f"settled at t={t_settle:.2f}s  (±2%)",
)
ax_p.plot(t3, x1_3, color=STYLE["blue"], lw=1.5, label="x₁(t) — mass 1")
ax_p.plot(
    t3, x2_3, color=STYLE["red"], lw=2.0, label=f"x₂(t) — mass 2  [OS={os_pct:.1f}%]"
)
ax_p.legend(
    fontsize=8,
    loc="lower right",
    facecolor=BG_AX,
    edgecolor=COL_GRID,
    labelcolor=COL_TXT,
)

# ── Velocity panel ────────────────────────────────────────────────────────────
ax_v.axhline(0, color=STYLE["gray"], ls=":", lw=0.8, alpha=0.5)
ax_v.plot(t3, v1_3, color=STYLE["purple"], lw=1.4, label="v₁(t)")
ax_v.plot(t3, v2_3, color=STYLE["orange"], lw=1.4, label="v₂(t)")
ax_v.legend(fontsize=8, facecolor=BG_AX, edgecolor=COL_GRID, labelcolor=COL_TXT)

# ── Force panel ───────────────────────────────────────────────────────────────
ax_f.axhline(0, color=STYLE["gray"], ls=":", lw=0.8, alpha=0.5)
ax_f.fill_between(t3, 0, u3, where=(u3 >= 0), alpha=0.15, color=STYLE["green"])
ax_f.fill_between(t3, 0, u3, where=(u3 < 0), alpha=0.15, color=STYLE["red"])
ax_f.plot(t3, u3, color=STYLE["green"], lw=1.5, label="F(t) — Neural-LQR output")
ax_f.legend(fontsize=8, facecolor=BG_AX, edgecolor=COL_GRID, labelcolor=COL_TXT)

# ── Phase portrait ────────────────────────────────────────────────────────────
ax_ph.set_title(
    "Phase portrait (x₁, x₂) — trajectory from rest to equilibrium",
    color=COL_TXT,
    fontsize=10,
    pad=6,
)
ax_ph.set_xlabel("x₁ (m)", color=COL_AX, fontsize=9)
ax_ph.set_ylabel("x₂ (m)", color=COL_AX, fontsize=9)
scatter_colors = plt.cm.plasma(np.linspace(0, 0.85, N3))
ax_ph.scatter(x1_3, x2_3, c=scatter_colors, s=1.5, alpha=0.7, rasterized=True)
ax_ph.plot(x1_3[0], x2_3[0], "o", ms=7, color=STYLE["blue"], zorder=5, label="start")
ax_ph.plot(
    x1_3[-1], x2_3[-1], "s", ms=7, color=STYLE["orange"], zorder=5, label="final state"
)
ax_ph.axhline(
    X2_REF3, color=STYLE["green"], ls="--", lw=1.0, alpha=0.5, label=f"x₂ = {X2_REF3}"
)
ax_ph.legend(fontsize=8, facecolor=BG_AX, edgecolor=COL_GRID, labelcolor=COL_TXT)

fig3.savefig(OUT / "03_sil_ai_controller.png", dpi=150)
plt.close(fig3)

# ── 4. Real-time oscilloscope — PID + sinusoidal reference ───────────────────
print("Generating 04_realtime_oscilloscope.png ...")
DT4 = 0.02
N4 = 500
t4 = np.arange(N4) * DT4

SP_AMP, SP_FREQ, SP_OFF = 2.0, 0.2, 3.0
r4 = SP_OFF + SP_AMP * np.sin(2 * np.pi * SP_FREQ * t4)

plant4 = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT4)
pid4 = PID(Kp=6.0, Ki=2.0, dt=DT4, u_min=-15.0, u_max=15.0)
x4 = np.zeros(plant4.n_states)
y4, u4 = np.zeros(N4), np.zeros(N4)

for k in range(N4):
    x4, y_arr = plant4.evolve(x4, np.array([u4[k - 1] if k > 0 else 0.0]))
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
DT5 = 0.02
SIM5 = 8.0
DRIFT_AT = 3.0
SETP5 = 3.0
N5 = int(SIM5 / DT5)
t5 = np.arange(N5) * DT5

plant_nom5 = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT5)
plant_drift5 = c2d(ss([[-2.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT5)
pid5 = PID(Kp=4.0, Ki=1.2, dt=DT5, u_min=-15.0, u_max=15.0)

x_phys = np.zeros(plant_nom5.n_states)
x_virt = np.zeros(plant_nom5.n_states)
yp5, yv5, u5, div5 = np.zeros(N5), np.zeros(N5), np.zeros(N5), np.zeros(N5)

for k in range(N5):
    plant_k = plant_drift5 if t5[k] >= DRIFT_AT else plant_nom5
    x_phys, y_p = plant_k.evolve(x_phys, np.array([u5[k - 1] if k > 0 else 0.0]))
    x_virt, y_v = plant_nom5.evolve(x_virt, np.array([u5[k - 1] if k > 0 else 0.0]))
    yp5[k] = float(y_p[0])
    yv5[k] = float(y_v[0])
    div5[k] = abs(yp5[k] - yv5[k])
    u5[k] = pid5.compute(setpoint=SETP5, measurement=yp5[k])

ALERT_THR = 0.15
fig = plt.figure(figsize=(10, 7))
gs = gridspec.GridSpec(3, 1, hspace=0.5)

ax1 = fig.add_subplot(gs[0])
ax1.plot(t5, yp5, color=STYLE["blue"], lw=1.8, label="y_physical (drifting)")
ax1.plot(
    t5, yv5, color=STYLE["orange"], lw=1.5, ls="--", label="y_virtual (nominal twin)"
)
ax1.axhline(SETP5, color=STYLE["gray"], ls=":", alpha=0.5, label=f"setpoint = {SETP5}")
ax1.axvline(
    DRIFT_AT, color=STYLE["red"], ls="--", lw=1.2, alpha=0.6, label="wear injected"
)
ax1.set_ylabel("Output y(t)")
ax1.set_title("Digital Twin — Physical vs Virtual")
ax1.legend(fontsize=8, loc="lower right")
ax1.grid(True, alpha=0.3)

ax2 = fig.add_subplot(gs[1])
ax2.plot(t5, div5, color="crimson", lw=1.8, label="|y_physical − y_virtual|")
ax2.axhline(
    ALERT_THR,
    color="red",
    ls="--",
    lw=1.2,
    alpha=0.7,
    label=f"alert threshold = {ALERT_THR}",
)
ax2.axvline(DRIFT_AT, color=STYLE["red"], ls="--", lw=1.2, alpha=0.6)
ax2.fill_between(
    t5,
    div5,
    ALERT_THR,
    where=(div5 > ALERT_THR),
    alpha=0.25,
    color="red",
    label="alert zone",
)
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
