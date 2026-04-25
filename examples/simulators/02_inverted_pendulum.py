"""Inverted Pendulum: open-loop fall vs LQR stabilisation + phase portrait.

Run:
    python examples/simulators/02_inverted_pendulum.py
"""

import matplotlib.pyplot as plt
import numpy as np

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import InvertedPendulumSim

m, l, g, b = 1.0, 1.0, 9.81, 0.1
dt = 0.005
T = 5.0
steps = int(T / dt)
t = np.arange(steps) * dt

# ── Linearise and design LQR ──────────────────────────────────────────────────
sim = InvertedPendulumSim(m=m, l=l, g=g, b=b)
sim.reset()
ss = sim.linearize(np.zeros(2), np.zeros(1))
Q = np.diag([50.0, 1.0])  # penalise angle heavily
R = np.eye(1)
K, _ = lqr(ss.A, ss.B, Q, R)
print(f"LQR gain K = {K.ravel()}")
print(f"Closed-loop poles: {np.linalg.eigvals(ss.A - ss.B @ K).round(3)}")

# ── Open-loop (small perturbation, no control) ────────────────────────────────
sim.reset(x0=np.array([0.05, 0.0]))
x_ol, y_ol = [], []
for _ in range(steps):
    y, info = sim.step(np.zeros(1), dt)
    y_ol.append(y[0])
    x_ol.append(info["x"].copy())
x_ol = np.array(x_ol)

# ── Closed-loop LQR ───────────────────────────────────────────────────────────
sim.reset(x0=np.array([0.2, 0.0]))  # larger perturbation
x_cl, y_cl, u_cl = [], [], []
for _ in range(steps):
    x = sim.state
    u = -K @ x
    u = np.clip(u, -20, 20)  # actuator saturation
    y, info = sim.step(u, dt)
    y_cl.append(y[0])
    x_cl.append(info["x"].copy())
    u_cl.append(u[0])
x_cl = np.array(x_cl)

# ── Phase portrait: closed-loop trajectories from different ICs ───────────────
ics = [np.array([th, 0.0]) for th in np.linspace(-0.4, 0.4, 9)]
phase_trajs = []
for x0 in ics:
    sim.reset(x0=x0)
    traj = []
    for _ in range(steps):
        x = sim.state
        u = -K @ x
        u = np.clip(u, -20, 20)
        sim.step(u, dt)
        traj.append(sim.state.copy())
    phase_trajs.append(np.array(traj))

# ── Plot ──────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 9))
fig.suptitle(
    f"Inverted Pendulum  (m={m} kg, l={l} m, b={b})   "
    f"λ_unstable = +{sim.unstable_pole():.3f} rad/s",
    fontsize=13,
)
gs = fig.add_gridspec(2, 3)

ax1 = fig.add_subplot(gs[0, :2])
ax1.plot(t, np.degrees(y_ol), color="tab:red", lw=2, label="Open-loop (x₀=0.05 rad)")
ax1.plot(t, np.degrees(y_cl), color="tab:green", lw=2, label="LQR (x₀=0.2 rad)")
ax1.set_ylabel("Angle θ (deg)")
ax1.set_title("Angle vs Time")
ax1.legend()
ax1.grid(True, alpha=0.3)
ax1.axhline(0, color="k", lw=0.8)

ax2 = fig.add_subplot(gs[1, :2])
ax2.plot(t, u_cl, color="tab:purple", lw=1.5)
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Torque τ (N·m)")
ax2.set_title("LQR Control Effort")
ax2.grid(True, alpha=0.3)
ax2.axhline(0, color="k", lw=0.8)

ax3 = fig.add_subplot(gs[:, 2])
for traj in phase_trajs:
    ax3.plot(
        np.degrees(traj[:, 0]),
        np.degrees(traj[:, 1]),
        color="tab:green",
        lw=1.2,
        alpha=0.7,
    )
    ax3.plot(
        np.degrees(traj[0, 0]), np.degrees(traj[0, 1]), "o", color="tab:blue", ms=5
    )
ax3.plot(0, 0, "*", color="gold", ms=14, zorder=5, label="Equilibrium")
ax3.set_xlabel("θ (deg)")
ax3.set_ylabel("θ̇ (deg/s)")
ax3.set_title("Phase Portrait (LQR)")
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
