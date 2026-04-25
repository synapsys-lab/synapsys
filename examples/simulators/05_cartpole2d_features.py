"""05_cartpole2d_features.py — CartPole2DView: light theme, save=, custom controller.

Demonstrates new features added in v0.2.7 that work in headless environments
(no Qt / PyVista required):

    1. mpl_theme("light") — white-background matplotlib theme
    2. CartPole2DView().simulate() — headless data collection
    3. CartPole2DView().animate(save=) — export animation to GIF
    4. Custom controller wired into CartPole2DView

Run:
    uv run python examples/simulators/05_cartpole2d_features.py
"""

import matplotlib.pyplot as plt
import numpy as np

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import CartPoleSim
from synapsys.viz import CartPole2DView
from synapsys.viz.palette import Dark, Light, mpl_theme

# ── 1. Light theme ────────────────────────────────────────────────────────────

print("=== 1. Light vs Dark palette comparison ===")

mpl_theme("light")

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
fig.suptitle("Synapsys palette comparison", color=Light.FG)

# Light panel
ax = axes[0]
ax.set_facecolor(Light.SURFACE)
ax.set_title("Light theme", color=Light.FG)
t = np.linspace(0, 2 * np.pi, 200)
ax.plot(t, np.sin(t), color=Light.SIG_POS, label="position")
ax.plot(t, np.cos(t), color=Light.SIG_VEL, label="velocity")
ax.plot(t, 0.5 * np.sin(2 * t), color=Light.SIG_CTRL, label="control")
ax.set_xlabel("t (s)", color=Light.MUTED)
ax.legend()
ax.grid(True, color=Light.GRID)

# Dark panel
ax = axes[1]
ax.set_facecolor(Dark.SURFACE)
ax.set_title("Dark theme", color=Dark.FG)
ax.plot(t, np.sin(t), color=Dark.SIG_POS, label="position")
ax.plot(t, np.cos(t), color=Dark.SIG_VEL, label="velocity")
ax.plot(t, 0.5 * np.sin(2 * t), color=Dark.SIG_CTRL, label="control")
ax.set_xlabel("t (s)", color=Dark.MUTED)
ax.legend()
ax.grid(True, color=Dark.GRID)

fig.tight_layout()
plt.savefig("/tmp/palette_comparison.png", dpi=120)
print("  → saved: /tmp/palette_comparison.png")
plt.close()

# ── 2. Headless simulation ────────────────────────────────────────────────────

print("\n=== 2. Headless simulation (simulate()) ===")

view = CartPole2DView(dt=0.02, duration=5.0)
hist = view.simulate()

print(f"  steps     : {len(hist['t'])}")
print(f"  final pos : {hist['pos'][-1]:.4f} m")
print(f"  final angle: {np.degrees(hist['angle'][-1]):.2f}°")
print(f"  max force : {np.max(np.abs(hist['force'])):.2f} N")

# ── 3. Export animation to GIF ────────────────────────────────────────────────

print("\n=== 3. Export animation (animate(save=)) ===")

import matplotlib

matplotlib.use("Agg")  # headless backend for saving without a display

view2 = CartPole2DView(dt=0.02, duration=3.0)
anim = view2.animate(save="/tmp/cartpole2d.gif")
print("  → saved: /tmp/cartpole2d.gif")
plt.close("all")

# ── 4. Custom LQR controller ──────────────────────────────────────────────────

print("\n=== 4. Custom controller ===")

sim = CartPoleSim()
sim.reset()
ss = sim.linearize(np.zeros(4), np.zeros(1))

# aggressive angle penalty
Q = np.diag([0.1, 0.01, 500.0, 50.0])
R = np.eye(1) * 0.001
K, _ = lqr(ss.A, ss.B, Q, R)

view3 = CartPole2DView(
    controller=lambda x: np.clip(-K @ x, -100, 100),
    dt=0.02,
    duration=5.0,
    x0=np.array([0.0, 0.0, 0.25, 0.0]),  # larger initial angle
)
hist3 = view3.simulate()
print(f"  custom K    : {K.ravel()}")
print(f"  final angle : {np.degrees(hist3['angle'][-1]):.3f}°")
print(f"  max force   : {np.max(np.abs(hist3['force'])):.2f} N")

# ── summary plot ─────────────────────────────────────────────────────────────

mpl_theme("light")
fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
fig.suptitle("CartPole2DView — custom aggressive LQR", color=Light.FG)

axes[0].plot(hist3["t"], np.degrees(hist3["angle"]), color=Light.SIG_ANG)
axes[0].set_ylabel("angle (°)", color=Light.MUTED)
axes[0].axhline(0, color=Light.SIG_REF, lw=1, ls="--")
axes[0].grid(True, color=Light.GRID)

axes[1].plot(hist3["t"], hist3["force"], color=Light.SIG_CTRL)
axes[1].set_ylabel("force (N)", color=Light.MUTED)
axes[1].set_xlabel("time (s)", color=Light.MUTED)
axes[1].grid(True, color=Light.GRID)

fig.tight_layout()
plt.savefig("/tmp/cartpole2d_custom.png", dpi=120)
print("  → saved: /tmp/cartpole2d_custom.png")
plt.close()

print("\nDone. Outputs saved to /tmp/")
