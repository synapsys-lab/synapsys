"""Integrator benchmark — compare Euler, RK4, and RK45 on CartPoleSim.

Measures accuracy (pole angle error vs RK45 reference) and wall-clock time
for a fixed 5-second LQR simulation.

Run:
    python examples/simulators/04_integrator_benchmark.py
"""

import time

import matplotlib.pyplot as plt
import numpy as np

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import CartPoleSim

# ── setup ─────────────────────────────────────────────────────────────────────
m_c, m_p, l, g = 1.0, 0.1, 0.5, 9.81
dt = 0.02
T = 5.0
steps = int(T / dt)
x0 = np.array([0.0, 0.0, 0.18, 0.0])

# LQR designed on RK4 linearisation (reference integrator)
_ref_sim = CartPoleSim(m_c=m_c, m_p=m_p, l=l, g=g, integrator="rk4")
_ref_sim.reset()
ss_lin = _ref_sim.linearize(np.zeros(4), np.zeros(1))
Q = np.diag([1.0, 0.1, 100.0, 10.0])
R = np.eye(1) * 0.01
K, _ = lqr(ss_lin.A, ss_lin.B, Q, R)
print(f"LQR gain K = {K.ravel().round(3)}")


def _run(integrator: str) -> tuple[np.ndarray, float]:
    """Simulate and return (angle_history, wall_time_seconds)."""
    sim = CartPoleSim(m_c=m_c, m_p=m_p, l=l, g=g, integrator=integrator)
    sim.reset(x0=x0)
    angles = np.empty(steps)
    t0 = time.perf_counter()
    for i in range(steps):
        x = sim.state
        u = np.clip(-K @ x, -50, 50)
        y, _ = sim.step(u, dt)
        angles[i] = np.degrees(x[2])
    elapsed = time.perf_counter() - t0
    return angles, elapsed


# ── simulate all three integrators ────────────────────────────────────────────
results = {}
for name in ("rk45", "rk4", "euler"):
    ang, t_wall = _run(name)
    results[name] = {"angles": ang, "time": t_wall}
    print(f"{name:5s} | wall time: {t_wall * 1000:.1f} ms")

# ── accuracy: RMS error vs RK45 reference ─────────────────────────────────────
ref = results["rk45"]["angles"]
print("\nRMS pole-angle error vs RK45 (deg):")
for name in ("rk4", "euler"):
    rms = np.sqrt(np.mean((results[name]["angles"] - ref) ** 2))
    print(f"  {name:5s}: {rms:.4f} deg")

# ── plot ──────────────────────────────────────────────────────────────────────
t = np.arange(steps) * dt
colors = {"rk45": "#ef4444", "rk4": "#3b82f6", "euler": "#f97316"}
labels = {"rk45": "RK45 (reference)", "rk4": "RK4", "euler": "Euler"}

fig, (ax_ang, ax_err) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig.suptitle("Integrator Benchmark — Cart-Pole LQR (dt=0.02 s)", fontsize=13)

for name, color in colors.items():
    ax_ang.plot(t, results[name]["angles"], color=color, lw=1.5, label=labels[name])
ax_ang.set_ylabel("Pole angle (deg)")
ax_ang.axhline(0, color="k", lw=0.8)
ax_ang.legend()
ax_ang.grid(True, alpha=0.3)

for name in ("rk4", "euler"):
    err = results[name]["angles"] - ref
    ax_err.plot(
        t, err, color=colors[name], lw=1.5, label=f"{labels[name]} error vs RK45"
    )
ax_err.set_ylabel("Angle error (deg)")
ax_err.set_xlabel("Time (s)")
ax_err.axhline(0, color="k", lw=0.8)
ax_err.legend()
ax_err.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
