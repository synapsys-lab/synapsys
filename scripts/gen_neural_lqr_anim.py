"""Generate Neural-LQR 2-DOF animation and updated static image.

Outputs
-------
website/static/img/examples/03_sil_ai_controller.png  — static (high-res)
website/static/img/examples/03_sil_ai_controller.gif  — animated (4 panels)

Run with:
    MPLBACKEND=Agg uv run python scripts/gen_neural_lqr_anim.py
"""

import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
from pathlib import Path

import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

OUT = Path("website/static/img/examples")
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(Path(__file__).parent.parent))
from synapsys.algorithms import lqr
from synapsys.api import c2d, ss
from synapsys.utils import StateEquations

# ── System ────────────────────────────────────────────────────────────────────
M, C, K = 1.0, 0.1, 2.0
DT = 0.01
N = 1200  # 12 s simulation
X2_REF = 1.0

eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1)
    .eq("x2", v2=1)
    .eq("v1", x1=-2 * K / M, x2=K / M, v1=-C / M)
    .eq("v2", x1=K / M, x2=-2 * K / M, v2=-C / M, F=K / M)
)

K_lqr, _ = lqr(eqs.A, eqs.B, np.diag([1.0, 10.0, 0.5, 1.0]), np.array([[1.0]]))
A_cl = eqs.A - eqs.B @ K_lqr
Nbar = float(-1.0 / (np.array([[0, 1, 0, 0]]) @ np.linalg.inv(A_cl) @ eqs.B).squeeze())

G_d = c2d(ss(eqs.A, eqs.B, np.eye(4), np.zeros((4, 1))), dt=DT)

# ── Simulate ──────────────────────────────────────────────────────────────────
t = np.arange(N) * DT
x1 = np.zeros(N)
x2 = np.zeros(N)
v1 = np.zeros(N)
v2 = np.zeros(N)
u = np.zeros(N)
x = np.zeros(4)

for k in range(N):
    u_k = float(np.dot(-K_lqr.flatten(), x)) + Nbar * X2_REF
    u_k = np.clip(u_k, -20.0, 20.0)
    x, y = G_d.evolve(x, np.array([u_k]))
    x1[k] = float(y[0])
    x2[k] = float(y[1])
    v1[k] = float(y[2])
    v2[k] = float(y[3])
    u[k] = u_k

# settle time
tol = 0.02
settled = np.where(np.abs(x2 - X2_REF) <= tol)[0]
t_settle = t[settled[0]] if len(settled) else t[-1]
os_pct = (max(x2) - X2_REF) / X2_REF * 100 if max(x2) > X2_REF else 0.0

# ── Theme ─────────────────────────────────────────────────────────────────────
BG_FIG = "#0f172a"
BG_AX = "#1e293b"
COL_GRID = "#334155"
COL_TXT = "#e2e8f0"
COL_AX = "#cbd5e1"

BLUE = "#60a5fa"
RED = "#f87171"
GREEN = "#4ade80"
ORANGE = "#fb923c"
PURPLE = "#c084fc"
GRAY = "#94a3b8"

FS_TITLE = 14
FS_LABEL = 12
FS_TICK = 11
FS_LEGEND = 11
FS_SUPTITLE = 15


def _style_ax(ax, title, ylabel, xlabel=None):
    ax.set_facecolor(BG_AX)
    ax.tick_params(colors=COL_AX, labelsize=FS_TICK)
    for sp in ax.spines.values():
        sp.set_edgecolor(COL_GRID)
    ax.grid(True, color=COL_GRID, linewidth=0.6, alpha=0.7)
    ax.set_title(title, color=COL_TXT, fontsize=FS_TITLE, pad=7, fontweight="semibold")
    ax.set_ylabel(ylabel, color=COL_AX, fontsize=FS_LABEL, labelpad=6)
    if xlabel:
        ax.set_xlabel(xlabel, color=COL_AX, fontsize=FS_LABEL, labelpad=6)


def _legend(ax, **kw):
    leg = ax.legend(
        fontsize=FS_LEGEND,
        facecolor=BG_AX,
        edgecolor=COL_GRID,
        labelcolor=COL_TXT,
        **kw,
    )
    return leg


# ─────────────────────────────────────────────────────────────────────────────
# 1. STATIC IMAGE (high-res)
# ─────────────────────────────────────────────────────────────────────────────
print("Generating static 03_sil_ai_controller.png ...")

fig = plt.figure(figsize=(15, 9), facecolor=BG_FIG)
fig.suptitle(
    "Neural-LQR  ·  2-DOF Mass-Spring-Damper  —  SIL batch simulation",
    color=COL_TXT,
    fontsize=FS_SUPTITLE,
    fontweight="bold",
    y=0.97,
)
gs = gridspec.GridSpec(
    3,
    2,
    figure=fig,
    hspace=0.52,
    wspace=0.32,
    left=0.07,
    right=0.97,
    top=0.92,
    bottom=0.07,
)

ax_p = fig.add_subplot(gs[0, :])
ax_v = fig.add_subplot(gs[1, 0])
ax_f = fig.add_subplot(gs[1, 1])
ax_ph = fig.add_subplot(gs[2, :])

for ax in [ax_p, ax_ph]:
    ax.set_facecolor(BG_AX)
    ax.tick_params(colors=COL_AX, labelsize=FS_TICK)
    for sp in ax.spines.values():
        sp.set_edgecolor(COL_GRID)
    ax.grid(True, color=COL_GRID, linewidth=0.6, alpha=0.7)

# ── Position ──
_style_ax(
    ax_p, "Position tracking — x₁(t) and x₂(t) → setpoint", "Position (m)", "Time (s)"
)
ax_p.axhline(
    X2_REF, color=GREEN, ls="--", lw=1.4, alpha=0.7, label=f"setpoint  r = {X2_REF} m"
)
ax_p.axhspan(X2_REF * 0.98, X2_REF * 1.02, alpha=0.07, color=GREEN)
ax_p.axvline(
    t_settle,
    color=ORANGE,
    ls="--",
    lw=1.4,
    alpha=0.85,
    label=f"settled at  t = {t_settle:.2f} s  (±2%)",
)
ax_p.plot(t, x1, color=BLUE, lw=1.8, label="x₁(t) — mass 1")
ax_p.plot(t, x2, color=RED, lw=2.2, label=f"x₂(t) — mass 2  [OS = {os_pct:.1f}%]")
_legend(ax_p, loc="lower right")

# ── Velocity ──
_style_ax(ax_v, "Velocities  v₁(t),  v₂(t)", "Velocity (m/s)", "Time (s)")
ax_v.axhline(0, color=GRAY, ls=":", lw=0.8, alpha=0.5)
ax_v.plot(t, v1, color=PURPLE, lw=1.6, label="v₁(t) — mass 1")
ax_v.plot(t, v2, color=ORANGE, lw=1.6, label="v₂(t) — mass 2")
_legend(ax_v, loc="upper right")

# ── Force ──
_style_ax(ax_f, "Control force  F(t)  [Neural-LQR]", "Force (N)", "Time (s)")
ax_f.axhline(0, color=GRAY, ls=":", lw=0.8, alpha=0.5)
ax_f.fill_between(t, 0, u, where=(u >= 0), alpha=0.18, color=GREEN)
ax_f.fill_between(t, 0, u, where=(u < 0), alpha=0.18, color=RED)
ax_f.plot(t, u, color=GREEN, lw=1.8, label="F(t) — Neural-LQR output")
_legend(ax_f, loc="upper right")

# ── Phase portrait ──
ax_ph.set_title(
    "Phase portrait  (x₁, x₂) — trajectory from rest to equilibrium",
    color=COL_TXT,
    fontsize=FS_TITLE,
    pad=7,
    fontweight="semibold",
)
ax_ph.set_xlabel("x₁  (m)", color=COL_AX, fontsize=FS_LABEL, labelpad=6)
ax_ph.set_ylabel("x₂  (m)", color=COL_AX, fontsize=FS_LABEL, labelpad=6)
cmap_arr = plt.cm.plasma(np.linspace(0, 0.85, N))
ax_ph.scatter(x1, x2, c=cmap_arr, s=2.0, alpha=0.75, rasterized=True)
ax_ph.plot(x1[0], x2[0], "o", ms=9, color=BLUE, zorder=5, label="initial state (0, 0)")
ax_ph.plot(
    x1[-1],
    x2[-1],
    "s",
    ms=9,
    color=ORANGE,
    zorder=5,
    label=f"final state ({x1[-1]:.2f}, {x2[-1]:.2f})",
)
ax_ph.axhline(
    X2_REF, color=GREEN, ls="--", lw=1.2, alpha=0.55, label=f"x₂ = {X2_REF}  (setpoint)"
)
_legend(ax_ph, loc="upper left")

fig.savefig(OUT / "03_sil_ai_controller.png", dpi=150)
plt.close(fig)
print("  → saved 03_sil_ai_controller.png")


# ─────────────────────────────────────────────────────────────────────────────
# 2. ANIMATED GIF
# ─────────────────────────────────────────────────────────────────────────────
print("Generating animated 03_sil_ai_controller.gif ...")

# Subsample: one frame every 6 steps → 200 frames at 20 fps ≈ 10 s loop
STEP = 6
FRAMES = N // STEP  # 200 frames
FPS = 20
TRAIL = 60  # how many past steps to draw as fading trail

fig2 = plt.figure(figsize=(15, 9), facecolor=BG_FIG)
fig2.suptitle(
    "Neural-LQR  ·  2-DOF Mass-Spring-Damper  —  real-time dynamics",
    color=COL_TXT,
    fontsize=FS_SUPTITLE,
    fontweight="bold",
    y=0.97,
)
gs2 = gridspec.GridSpec(
    3,
    2,
    figure=fig2,
    hspace=0.52,
    wspace=0.32,
    left=0.07,
    right=0.97,
    top=0.92,
    bottom=0.07,
)

ax2_p = fig2.add_subplot(gs2[0, :])
ax2_v = fig2.add_subplot(gs2[1, 0])
ax2_f = fig2.add_subplot(gs2[1, 1])
ax2_ph = fig2.add_subplot(gs2[2, :])

for ax in [ax2_p, ax2_ph]:
    ax.set_facecolor(BG_AX)
    ax.tick_params(colors=COL_AX, labelsize=FS_TICK)
    for sp in ax.spines.values():
        sp.set_edgecolor(COL_GRID)
    ax.grid(True, color=COL_GRID, linewidth=0.6, alpha=0.7)

_style_ax(
    ax2_p, "Position tracking — x₁(t) and x₂(t) → setpoint", "Position (m)", "Time (s)"
)
_style_ax(ax2_v, "Velocities  v₁(t),  v₂(t)", "Velocity (m/s)", "Time (s)")
_style_ax(ax2_f, "Control force  F(t)  [Neural-LQR]", "Force (N)", "Time (s)")

ax2_ph.set_facecolor(BG_AX)
ax2_ph.tick_params(colors=COL_AX, labelsize=FS_TICK)
for sp in ax2_ph.spines.values():
    sp.set_edgecolor(COL_GRID)
ax2_ph.grid(True, color=COL_GRID, linewidth=0.6, alpha=0.7)
ax2_ph.set_title(
    "Phase portrait  (x₁, x₂)",
    color=COL_TXT,
    fontsize=FS_TITLE,
    pad=7,
    fontweight="semibold",
)
ax2_ph.set_xlabel("x₁  (m)", color=COL_AX, fontsize=FS_LABEL, labelpad=6)
ax2_ph.set_ylabel("x₂  (m)", color=COL_AX, fontsize=FS_LABEL, labelpad=6)

# Static reference lines (drawn once)
ax2_p.axhline(
    X2_REF, color=GREEN, ls="--", lw=1.4, alpha=0.6, label=f"setpoint  r = {X2_REF} m"
)
ax2_p.axhspan(X2_REF * 0.98, X2_REF * 1.02, alpha=0.06, color=GREEN)
ax2_f.axhline(0, color=GRAY, ls=":", lw=0.8, alpha=0.5)
ax2_v.axhline(0, color=GRAY, ls=":", lw=0.8, alpha=0.5)
ax2_ph.axhline(X2_REF, color=GREEN, ls="--", lw=1.2, alpha=0.5, label=f"x₂ = {X2_REF}")

# Pre-set fixed axis limits (avoids rescaling per-frame)
T_MAX = t[-1]
ax2_p.set_xlim(0, T_MAX)
ax2_p.set_ylim(min(x1.min(), x2.min()) - 0.15, max(x1.max(), x2.max()) + 0.25)
ax2_v.set_xlim(0, T_MAX)
ax2_v.set_ylim(min(v1.min(), v2.min()) - 0.1, max(v1.max(), v2.max()) + 0.1)
ax2_f.set_xlim(0, T_MAX)
ax2_f.set_ylim(u.min() - 0.5, u.max() + 0.5)
ax2_ph.set_xlim(x1.min() - 0.05, x1.max() + 0.05)
ax2_ph.set_ylim(x2.min() - 0.05, x2.max() + 0.15)

# Moving lines
(l_x1,) = ax2_p.plot([], [], color=BLUE, lw=1.8, label="x₁(t) — mass 1")
(l_x2,) = ax2_p.plot([], [], color=RED, lw=2.2, label="x₂(t) — mass 2")
(l_v1,) = ax2_v.plot([], [], color=PURPLE, lw=1.6, label="v₁(t)")
(l_v2,) = ax2_v.plot([], [], color=ORANGE, lw=1.6, label="v₂(t)")
(l_u,) = ax2_f.plot([], [], color=GREEN, lw=1.8, label="F(t)")
(l_ph,) = ax2_ph.plot([], [], color=BLUE, lw=1.4, alpha=0.7)

# Dots for current state
(dot_x1,) = ax2_p.plot([], [], "o", ms=8, color=BLUE, zorder=6)
(dot_x2,) = ax2_p.plot([], [], "o", ms=8, color=RED, zorder=6)
(dot_ph,) = ax2_ph.plot(
    [], [], "o", ms=10, color=ORANGE, zorder=6, label="current state"
)

# Time annotation
time_ann = ax2_p.annotate(
    "t = 0.00 s",
    xy=(0.01, 0.94),
    xycoords="axes fraction",
    color=ORANGE,
    fontsize=FS_LABEL,
    fontweight="bold",
)

for ax in [ax2_p, ax2_v, ax2_f, ax2_ph]:
    _legend(ax, loc="upper right")

_legend(ax2_ph, loc="upper left")


def _update(frame: int):
    i = frame * STEP  # actual data index
    i0 = max(0, i - TRAIL * STEP)

    l_x1.set_data(t[:i], x1[:i])
    l_x2.set_data(t[:i], x2[:i])
    l_v1.set_data(t[:i], v1[:i])
    l_v2.set_data(t[:i], v2[:i])
    l_u.set_data(t[:i], u[:i])
    l_ph.set_data(x1[i0:i], x2[i0:i])

    if i > 0:
        dot_x1.set_data([t[i - 1]], [x1[i - 1]])
        dot_x2.set_data([t[i - 1]], [x2[i - 1]])
        dot_ph.set_data([x1[i - 1]], [x2[i - 1]])
        time_ann.set_text(f"t = {t[i - 1]:.2f} s")

    return l_x1, l_x2, l_v1, l_v2, l_u, l_ph, dot_x1, dot_x2, dot_ph, time_ann


ani = animation.FuncAnimation(
    fig2,
    _update,
    frames=FRAMES,
    interval=1000 // FPS,
    blit=True,
)

writer = animation.PillowWriter(fps=FPS)
ani.save(OUT / "03_sil_ai_controller.gif", writer=writer, dpi=100)
plt.close(fig2)
print(f"  → saved 03_sil_ai_controller.gif  ({FRAMES} frames @ {FPS} fps)")

# ─────────────────────────────────────────────────────────────────────────────
# 3. EXPORT SIMULATION DATA FOR REACT COMPONENT
# ─────────────────────────────────────────────────────────────────────────────
print("Exporting simulation data for MassSpringDamper React component ...")

SUB = 2  # keep every 2nd point → 600 pts, DT_OUT = 0.02 s
x1_e = x1[::SUB]
x2_e = x2[::SUB]
u_e = u[::SUB]
dt_e = DT * SUB


def _arr(a: np.ndarray) -> str:
    return "[" + ",".join(f"{float(v):.4f}" for v in a) + "]"


ts_dir = Path("website/src/data")
ts_dir.mkdir(parents=True, exist_ok=True)
(ts_dir / "lqr_sim_data.ts").write_text(
    "// Auto-generated by scripts/gen_neural_lqr_anim.py — do not edit manually\n"
    "// Regenerate: uv run python scripts/gen_neural_lqr_anim.py\n\n"
    f"export const SIM_DT     = {dt_e};\n"
    f"export const SIM_N      = {len(x1_e)};\n"
    f"export const SIM_X2_REF = {X2_REF};\n"
    f"export const SIM_U_MAX  = 20.0;\n"
    f"export const SIM_X1 = {_arr(x1_e)};\n"
    f"export const SIM_X2 = {_arr(x2_e)};\n"
    f"export const SIM_U  = {_arr(u_e)};\n"
)
print(f"  → exported {len(x1_e)} pts to website/src/data/lqr_sim_data.ts  (dt={dt_e}s)")

print(f"\nDone. Files in {OUT}/")
