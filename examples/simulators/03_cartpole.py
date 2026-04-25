"""Cart-Pole: LQR stabilisation with animated cart-pole visualisation.

Run:
    python examples/simulators/03_cartpole.py
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import CartPoleSim

m_c, m_p, l, g = 1.0, 0.1, 0.5, 9.81
dt = 0.02
T = 8.0
steps = int(T / dt)
t = np.arange(steps) * dt

# ── Design LQR on linearised model ───────────────────────────────────────────
sim = CartPoleSim(m_c=m_c, m_p=m_p, l=l, g=g)
sim.reset()
ss = sim.linearize(np.zeros(4), np.zeros(1))
Q = np.diag([1.0, 0.1, 100.0, 10.0])  # penalise angle heavily
R = np.eye(1) * 0.01
K, _ = lqr(ss.A, ss.B, Q, R)
print(f"LQR gain K = {K.ravel().round(3)}")
print(f"Closed-loop poles: {np.linalg.eigvals(ss.A - ss.B @ K).round(3)}")

# ── Simulate ──────────────────────────────────────────────────────────────────
x0 = np.array([0.0, 0.0, 0.15, 0.0])  # pole tilted 0.15 rad
sim.reset(x0=x0)
history = {"pos": [], "angle": [], "force": [], "x_full": []}

for _ in range(steps):
    x = sim.state
    u = np.clip(-K @ x, -50, 50)
    y, info = sim.step(u, dt)
    history["pos"].append(x[0])
    history["angle"].append(np.degrees(x[2]))
    history["force"].append(u[0])
    history["x_full"].append(info["x"].copy())

pos = np.array(history["pos"])
angle = np.array(history["angle"])
force = np.array(history["force"])
states = np.array(history["x_full"])

# ── Static plots ──────────────────────────────────────────────────────────────
fig_static, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
fig_static.suptitle(
    f"Cart-Pole LQR  (m_c={m_c} kg, m_p={m_p} kg, l={l} m)   x₀ = [0, 0, 0.15 rad, 0]",
    fontsize=12,
)

axes[0].plot(t, pos, color="tab:blue", lw=2, label="Cart position")
axes[0].set_ylabel("Cart position (m)")
axes[0].grid(True, alpha=0.3)
axes[0].axhline(0, color="k", lw=0.8)
axes[0].legend()

axes[1].plot(t, angle, color="tab:orange", lw=2, label="Pole angle")
axes[1].set_ylabel("Pole angle (deg)")
axes[1].grid(True, alpha=0.3)
axes[1].axhline(0, color="k", lw=0.8)
axes[1].legend()

axes[2].plot(t, force, color="tab:red", lw=1.5, label="Control force")
axes[2].set_xlabel("Time (s)")
axes[2].set_ylabel("Force F (N)")
axes[2].grid(True, alpha=0.3)
axes[2].axhline(0, color="k", lw=0.8)
axes[2].legend()
plt.tight_layout()

# ── Animation ─────────────────────────────────────────────────────────────────
fig_anim, ax_anim = plt.subplots(figsize=(9, 4))
ax_anim.set_xlim(-3, 3)
ax_anim.set_ylim(-0.3, 1.2)
ax_anim.set_aspect("equal")
ax_anim.grid(True, alpha=0.3)
ax_anim.axhline(0, color="k", lw=1)
ax_anim.set_title("Cart-Pole Animation (LQR)")

cart_w, cart_h = 0.4, 0.15
cart_patch = patches.FancyBboxPatch(
    (-cart_w / 2, -cart_h / 2),
    cart_w,
    cart_h,
    boxstyle="round,pad=0.02",
    fc="#2563eb",
    ec="white",
    lw=1.5,
)
ax_anim.add_patch(cart_patch)
(pole_line,) = ax_anim.plot([], [], "o-", color="#c8a870", lw=3, ms=10)
time_text = ax_anim.text(0.02, 0.92, "", transform=ax_anim.transAxes, fontsize=10)


def _update(frame):
    p, theta = states[frame, 0], states[frame, 2]
    cart_patch.set_xy((p - cart_w / 2, -cart_h / 2))
    tip_x = p + l * np.sin(theta)
    tip_y = l * np.cos(theta)
    pole_line.set_data([p, tip_x], [0, tip_y])
    time_text.set_text(f"t = {t[frame]:.2f} s   θ = {np.degrees(theta):.1f}°")
    return cart_patch, pole_line, time_text


anim = FuncAnimation(fig_anim, _update, frames=steps, interval=dt * 1000, blit=True)
plt.tight_layout()
plt.show()
