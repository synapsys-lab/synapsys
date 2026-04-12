"""Generate quickstart documentation images."""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

OUT = Path("website/static/img/quickstart")
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(Path(__file__).parent.parent))

from synapsys.api import tf, ss, step, feedback, c2d
from synapsys.algorithms import PID

BLUE   = "#2563eb"
RED    = "#dc2626"
GREEN  = "#16a34a"
ORANGE = "#ea580c"
GRAY   = "#6b7280"
PURPLE = "#7c3aed"

# ── 1. Step response: poles and metrics ──────────────────────────────────────
print("Generating qs_01_step_response.png ...")
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2*zeta*wn, wn**2])
t, y = step(G)

# find overshoot and rise time metrics
y_ss  = y[-1]
i_peak = int(np.argmax(y))
t_peak = t[i_peak]
y_peak = y[i_peak]
overshoot_pct = (y_peak - y_ss) / y_ss * 100

# 2% settling band
settled = np.where(np.abs(y - y_ss) <= 0.02 * y_ss)[0]
t_settle = t[settled[0]] if len(settled) else t[-1]

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(t, y, color=BLUE, lw=2, label="y(t)")
ax.axhline(y_ss, color=GRAY, ls="--", lw=1.2, alpha=0.7, label="setpoint")
ax.axhline(y_ss * 1.02, color=RED, ls=":", lw=1, alpha=0.5)
ax.axhline(y_ss * 0.98, color=RED, ls=":", lw=1, alpha=0.5, label="±2% band")
ax.axvline(t_peak, color=ORANGE, ls="--", lw=1.2, alpha=0.7, label=f"peak at t={t_peak:.2f}s ({overshoot_pct:.1f}% OS)")
ax.axvline(t_settle, color=GREEN, ls="--", lw=1.2, alpha=0.7, label=f"settled at t={t_settle:.2f}s")
ax.fill_between(t, y_ss * 0.98, y_ss * 1.02, alpha=0.07, color=GREEN)
ax.set_title(r"Step Response — $G(s)=\frac{100}{s^2+10s+100}$  ($\zeta=0.5$, $\omega_n=10$)", fontsize=11)
ax.set_xlabel("Time (s)"); ax.set_ylabel("y(t)")
ax.legend(fontsize=8, loc="lower right")
ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "qs_01_step_response.png", dpi=150)
plt.close(fig)

# ── 2. Open loop vs closed loop ──────────────────────────────────────────────
print("Generating qs_02_closed_loop.png ...")
G2  = tf([10], [1, 1])   # G(s) = 10/(s+1)
T2  = feedback(G2)        # T = 10/(s+11)

t_g, y_g = step(G2)
t_t, y_t = step(T2)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

ax1.plot(t_g, y_g, color=ORANGE, lw=2, label="G(s) open-loop")
ax1.axhline(10.0, color=GRAY, ls="--", lw=1.2, alpha=0.6, label="DC gain = 10")
ax1.set_title("Open-loop step response")
ax1.set_xlabel("Time (s)"); ax1.set_ylabel("y(t)")
ax1.legend(fontsize=9); ax1.grid(True, alpha=0.3)

ax2.plot(t_t, y_t, color=BLUE, lw=2, label="T(s) = feedback(G)")
ax2.axhline(10/11, color=GRAY, ls="--", lw=1.2, alpha=0.6, label=f"DC gain = {10/11:.4f}")
ax2.axhline(1.0, color=RED, ls=":", lw=1, alpha=0.5, label="setpoint = 1")
ax2.set_title("Closed-loop step response")
ax2.set_xlabel("Time (s)"); ax2.set_ylabel("y(t)")
ax2.legend(fontsize=9); ax2.grid(True, alpha=0.3)

fig.suptitle(r"$G(s)=\dfrac{10}{s+1}$ — open loop vs closed loop (unity negative feedback)", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "qs_02_closed_loop.png", dpi=150)
plt.close(fig)

# ── 3. Continuous vs discrete step response ──────────────────────────────────
print("Generating qs_03_discrete.png ...")
Gc = tf([1], [1, 2, 1])
Gd_fast = c2d(Gc, dt=0.05)    # Ts = 50 ms (fine)
Gd_slow = c2d(Gc, dt=0.5)     # Ts = 500 ms (coarse)

t_c, y_c     = step(Gc)
t_df, y_df   = step(Gd_fast, n=int(5/0.05))
t_ds, y_ds   = step(Gd_slow, n=int(5/0.5))

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(t_c,  y_c,  color=BLUE,   lw=2,   label="Continuous  G(s)")
ax.step(t_df, y_df, color=GREEN,  lw=1.5, where="post", label=f"ZOH Ts=0.05 s (20 Hz)")
ax.step(t_ds, y_ds, color=RED,    lw=1.5, where="post", linestyle="--", label=f"ZOH Ts=0.5 s  (2 Hz)")
ax.set_title(r"Discretisation — $G(s)=\dfrac{1}{(s+1)^2}$ — continuous vs ZOH", fontsize=11)
ax.set_xlabel("Time (s)"); ax.set_ylabel("y(t)")
ax.set_xlim(0, 5)
ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
fig.tight_layout()
fig.savefig(OUT / "qs_03_discrete.png", dpi=150)
plt.close(fig)

# ── 4. PID closed-loop ───────────────────────────────────────────────────────
print("Generating qs_04_pid.png ...")
# Plant: G(s) = 25/(s^2+5s+25), wn=5, zeta=0.5
# PID (PI): well-tuned, no derivative kick, converges to setpoint=1
DT   = 0.02
SETP = 1.0
N    = 400
plant4 = c2d(tf([25], [1, 5, 25]), dt=DT)
x4     = np.zeros(plant4.n_states)
pid4   = PID(Kp=3.0, Ki=1.5, Kd=0.0, dt=DT, u_min=-10.0, u_max=10.0)
t4     = np.arange(N) * DT
y4, u4 = np.zeros(N), np.zeros(N)

for k in range(N):
    u_prev = u4[k-1] if k > 0 else 0.0
    x4, y_arr = plant4.evolve(x4, np.array([u_prev]))
    y4[k] = float(y_arr[0])
    u4[k] = pid4.compute(setpoint=SETP, measurement=y4[k])

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
ax1.plot(t4, y4, color=BLUE, lw=2, label="y(t) — plant output")
ax1.axhline(SETP, color=GRAY, ls="--", lw=1.2, alpha=0.6, label=f"setpoint = {SETP}")
ax1.set_ylabel("y(t)"); ax1.legend(fontsize=9); ax1.grid(True, alpha=0.3)

ax2.plot(t4, u4, color=ORANGE, lw=1.8, label="u(t) — control action")
ax2.axhline(0, color=GRAY, ls=":", lw=1, alpha=0.4)
ax2.set_ylabel("u(t)"); ax2.set_xlabel("Time (s)")
ax2.legend(fontsize=9); ax2.grid(True, alpha=0.3)

fig.suptitle(r"PID closed-loop — $G(s)=\dfrac{25}{s^2+5s+25}$,  Kp=3, Ki=1.5, Kd=0", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "qs_04_pid.png", dpi=150)
plt.close(fig)

print(f"\nAll quickstart images saved to {OUT}/")
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name}")
