"""Mass-Spring-Damper: step response comparison and free vibration.

Run:
    python examples/simulators/01_mass_spring_damper.py
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import lti
from scipy.signal import step as scipy_step

from synapsys.simulators import MassSpringDamperSim

m, c, k = 1.0, 0.5, 2.0
F = 1.0
dt = 0.001
T = 10.0
steps = int(T / dt)
t = np.arange(steps) * dt

# ── Simulation: step response ─────────────────────────────────────────────────
sim = MassSpringDamperSim(m=m, c=c, k=k, integrator="rk4")
sim.reset()
y_step = [sim.step(np.array([F]), dt)[0][0] for _ in range(steps)]

# ── Analytical step response (scipy reference) ────────────────────────────────
sys_ct = lti([1 / m], [1, c / m, k / m])
t_ref, y_ref = scipy_step(sys_ct, T=t)
y_ref *= F  # scale by force magnitude

# ── Free vibration from x0=[1, 0] ────────────────────────────────────────────
sim.reset(x0=np.array([1.0, 0.0]))
y_free = [sim.step(np.zeros(1), dt)[0][0] for _ in range(steps)]

# ── PD feedback ──────────────────────────────────────────────────────────────
ss = sim.linearize(np.zeros(2), np.zeros(1))
# Simple PD via pole placement: place poles at -3, -4
Kp, Kd = 10.0, 5.0  # K = [Kp, Kd] → u = -Kp*q - Kd*q_dot
sim.reset(x0=np.array([1.0, 0.0]))
y_pd = []
for _ in range(steps):
    x = sim.state
    u = np.array([-Kp * x[0] - Kd * x[1]])
    y_pd.append(sim.step(u, dt)[0][0])

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=False)
fig.suptitle(
    f"Mass-Spring-Damper  (m={m} kg, c={c} N·s/m, k={k} N/m)\n"
    f"ωₙ={sim.natural_frequency():.2f} rad/s,  ζ={sim.damping_ratio():.3f}",
    fontsize=13,
)

axes[0].plot(t, y_step, label="Synapsys RK4", lw=2)
axes[0].plot(t_ref, y_ref, "--", label="SciPy (reference)", lw=1.5)
axes[0].set_ylabel("Position q (m)")
axes[0].set_title(f"Step Response  (F={F} N)")
axes[0].legend()
axes[0].grid(True, alpha=0.3)
axes[0].axhline(F / k, color="gray", ls=":", label="q_ss = F/k")

axes[1].plot(t, y_free, color="tab:orange", lw=2)
axes[1].set_ylabel("Position q (m)")
axes[1].set_title("Free Vibration  (x₀ = [1 m, 0])")
axes[1].grid(True, alpha=0.3)
axes[1].axhline(0, color="k", lw=0.8)

axes[2].plot(t, y_pd, color="tab:green", lw=2)
axes[2].set_ylabel("Position q (m)")
axes[2].set_xlabel("Time (s)")
axes[2].set_title(f"PD Control  (Kp={Kp}, Kd={Kd})  —  x₀ = [1 m, 0]")
axes[2].grid(True, alpha=0.3)
axes[2].axhline(0, color="k", lw=0.8)

plt.tight_layout()
plt.show()
