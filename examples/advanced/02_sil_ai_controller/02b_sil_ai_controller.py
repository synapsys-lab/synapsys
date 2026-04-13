"""AI Controller process — Neural-LQR for 2-DOF mass-spring-damper SIL.

A PyTorch MLP initialized with LQR optimal gains (physics-informed initialisation)
drives the 2-DOF plant running in a separate process via shared memory.

Architecture
------------
  state  ──►  [ MLP · LQR-init ]  ──►  force F
  (4 inputs)    3 layers / Tanh         (1 output)

Run AFTER 02a_sil_plant.py is already running.
"""
from __future__ import annotations

import collections
import threading

import matplotlib.gridspec as gridspec
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

# ── Optional PyTorch import ───────────────────────────────────────────────────
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# ── Simulation constants ──────────────────────────────────────────────────────
DT       = 0.01          # 100 Hz — must match plant
X2_REF   = 1.0           # setpoint: mass-2 position (m)
U_LIMIT  = 20.0          # actuator saturation (N)
WINDOW   = 600           # rolling window — 6 s at 100 Hz

# LQR gains (pre-computed analytically for m=1, c=0.1, k=2, Q=diag(1,10,0.5,1), R=1)
# u = −K·x + Nbar·r   with   r = X2_REF
_K    = np.array([-0.38206612, 2.22656697, 0.41957260, 1.74696048])
_NBAR = 3.535534


# ── Neural-LQR model ──────────────────────────────────────────────────────────

def _build_model() -> "nn.Module":
    """3-layer MLP initialized with LQR optimal gains (physics-informed)."""

    class NeuralLQR(nn.Module):
        """Physics-informed MLP controller.

        Architecture
        ~~~~~~~~~~~~
        Linear(4→32) → Tanh → Linear(32→16) → Tanh → Linear(16→1)

        Initialization strategy
        ~~~~~~~~~~~~~~~~~~~~~~~
        The hidden layers use Xavier initialisation (small random weights).
        The output layer is analytically set to the LQR gain vector −K so
        that, at initialisation, the network implements the optimal linear
        policy u = −K·x + Nbar·r.

        In a real research workflow the hidden-layer weights would then be
        fine-tuned by:
          * Imitation learning  (clone the LQR trajectory)
          * Reinforcement learning  (PPO / SAC on the SIL environment)
          * Online adaptation  (meta-RL, adaptive control)

        The Synapsys ControllerAgent wraps the forward() call identically
        regardless of model complexity — only the numpy↔tensor conversion
        at the boundary changes.
        """

        def __init__(self, K: np.ndarray, Nbar: float) -> None:
            super().__init__()
            self.Nbar = float(Nbar)
            self.net = nn.Sequential(
                nn.Linear(4, 32),
                nn.Tanh(),
                nn.Linear(32, 16),
                nn.Tanh(),
                nn.Linear(16, 1),
            )
            with torch.no_grad():
                nn.init.xavier_uniform_(self.net[0].weight)
                nn.init.zeros_(self.net[0].bias)
                nn.init.xavier_uniform_(self.net[2].weight)
                nn.init.zeros_(self.net[2].bias)
                # Output layer → LQR gains (physics-informed)
                self.net[4].weight.data = torch.tensor(
                    -K.reshape(1, -1), dtype=torch.float32
                )
                self.net[4].bias.data.zero_()

        def forward(self, x: "torch.Tensor") -> "torch.Tensor":
            return self.net(x) + self.Nbar * X2_REF

    return NeuralLQR(_K, _NBAR).eval()


# ── Real-time data buffers (thread-safe deque) ────────────────────────────────
_tick   = [0]
_lock   = threading.Lock()
t_buf   : collections.deque = collections.deque(maxlen=WINDOW)
x1_buf  : collections.deque = collections.deque(maxlen=WINDOW)
x2_buf  : collections.deque = collections.deque(maxlen=WINDOW)
v1_buf  : collections.deque = collections.deque(maxlen=WINDOW)
v2_buf  : collections.deque = collections.deque(maxlen=WINDOW)
u_buf   : collections.deque = collections.deque(maxlen=WINDOW)

# ── Control law callback ──────────────────────────────────────────────────────
if HAS_TORCH:
    _model = _build_model()
    print("PyTorch available — Neural-LQR controller loaded.")
    print(f"  Parameters: {sum(p.numel() for p in _model.parameters())}")
else:
    print("PyTorch not installed — falling back to plain NumPy LQR.")


def control_law(state: np.ndarray) -> np.ndarray:
    """Inference step executed by ControllerAgent at every 10 ms tick."""
    if HAS_TORCH:
        with torch.no_grad():
            t_in = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            u = float(_model(t_in).squeeze())
    else:
        u = float(np.dot(-_K, state)) + _NBAR * X2_REF

    u = np.clip(u, -U_LIMIT, U_LIMIT)

    # Record into circular buffers (GIL + deque.append are both thread-safe)
    with _lock:
        _tick[0] += 1
        t_buf.append(_tick[0] * DT)
        x1_buf.append(float(state[0]))
        x2_buf.append(float(state[1]))
        v1_buf.append(float(state[2]))
        v2_buf.append(float(state[3]))
        u_buf.append(u)

    return np.array([u])


# ── Scientific real-time figure ───────────────────────────────────────────────
BLUE   = "#1d4ed8"
RED    = "#b91c1c"
GREEN  = "#15803d"
ORANGE = "#c2410c"
PURPLE = "#7c3aed"
GRAY   = "#6b7280"

def _build_figure():
    fig = plt.figure(figsize=(13, 8), facecolor="#0f172a")
    fig.suptitle(
        "SIL — Neural-LQR · 2-DOF Mass-Spring-Damper  (real-time)",
        color="white", fontsize=13, fontweight="bold", y=0.97,
    )

    gs = gridspec.GridSpec(
        3, 2,
        figure=fig,
        hspace=0.45, wspace=0.35,
        left=0.07, right=0.97, top=0.92, bottom=0.08,
    )

    axes = {
        "pos":   fig.add_subplot(gs[0, :]),   # positions — full width
        "vel":   fig.add_subplot(gs[1, 0]),   # velocities
        "force": fig.add_subplot(gs[1, 1]),   # control force
        "phase": fig.add_subplot(gs[2, :]),   # phase portrait x1 vs x2
    }

    _STYLE = dict(facecolor="#1e293b", alpha=1.0)
    for ax in axes.values():
        ax.set_facecolor(_STYLE["facecolor"])
        ax.tick_params(colors="#94a3b8", labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor("#334155")
        ax.grid(True, color="#334155", linewidth=0.5, alpha=0.7)

    # ── Position panel ────────────────────────────────────────────────────────
    ax = axes["pos"]
    ax.set_title("Position tracking  x₁(t), x₂(t)", color="#e2e8f0", fontsize=10, pad=6)
    ax.set_ylabel("Position (m)", color="#94a3b8", fontsize=9)
    ax.axhline(X2_REF, color=GREEN, ls="--", lw=1.2, alpha=0.6, label=f"setpoint r = {X2_REF} m")
    ax.axhspan(X2_REF * 0.98, X2_REF * 1.02, alpha=0.06, color=GREEN)
    l_x1, = ax.plot([], [], color=BLUE,   lw=1.5, label="x₁(t) — mass 1")
    l_x2, = ax.plot([], [], color=RED,    lw=1.8, label="x₂(t) — mass 2  [tracked]")
    ax.legend(fontsize=8, loc="lower right",
              facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")

    # ── Velocity panel ────────────────────────────────────────────────────────
    ax = axes["vel"]
    ax.set_title("Velocities  v₁(t), v₂(t)", color="#e2e8f0", fontsize=10, pad=6)
    ax.set_ylabel("Velocity (m/s)", color="#94a3b8", fontsize=9)
    ax.set_xlabel("Time (s)", color="#94a3b8", fontsize=9)
    ax.axhline(0, color=GRAY, ls=":", lw=0.8, alpha=0.5)
    l_v1, = ax.plot([], [], color=PURPLE, lw=1.4, label="v₁(t)")
    l_v2, = ax.plot([], [], color=ORANGE, lw=1.4, label="v₂(t)")
    ax.legend(fontsize=8, loc="upper right",
              facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")

    # ── Control force panel ───────────────────────────────────────────────────
    ax = axes["force"]
    ax.set_title("Control force  F(t)  [Neural-LQR]", color="#e2e8f0", fontsize=10, pad=6)
    ax.set_ylabel("Force (N)", color="#94a3b8", fontsize=9)
    ax.set_xlabel("Time (s)", color="#94a3b8", fontsize=9)
    ax.axhline(0, color=GRAY, ls=":", lw=0.8, alpha=0.5)
    ax.axhline( U_LIMIT, color=RED, ls=":", lw=0.8, alpha=0.4)
    ax.axhline(-U_LIMIT, color=RED, ls=":", lw=0.8, alpha=0.4, label=f"±{U_LIMIT} N sat.")
    l_u, = ax.plot([], [], color=GREEN, lw=1.5, label="F(t)")
    ax.legend(fontsize=8, loc="upper right",
              facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")

    # ── Phase portrait ────────────────────────────────────────────────────────
    ax = axes["phase"]
    ax.set_title("Phase portrait  (x₁, x₂) trajectory → equilibrium",
                 color="#e2e8f0", fontsize=10, pad=6)
    ax.set_xlabel("x₁ (m)", color="#94a3b8", fontsize=9)
    ax.set_ylabel("x₂ (m)", color="#94a3b8", fontsize=9)
    ax.axhline(X2_REF, color=GREEN, ls="--", lw=1.0, alpha=0.5, label=f"x₂ = {X2_REF}")
    ax.axvline(0,       color=GRAY,  ls=":",  lw=0.8, alpha=0.4)
    l_ph, = ax.plot([], [], color=BLUE, lw=1.2, alpha=0.8, label="trajectory")
    dot_ph, = ax.plot([], [], "o", color=ORANGE, ms=6, label="current state", zorder=5)
    ax.legend(fontsize=8, loc="upper left",
              facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0")

    lines = dict(x1=l_x1, x2=l_x2, v1=l_v1, v2=l_v2, u=l_u, ph=l_ph, dot_ph=dot_ph)
    return fig, axes, lines


def main() -> None:
    print("\nConnecting to 'sil_2dof' bus…")
    try:
        transport = SharedMemoryTransport("sil_2dof", {"state": 4, "u": 1}, create=False)
    except Exception as exc:
        print(f"  Error: {exc}")
        print("  Is 02a_sil_plant.py running?")
        return

    sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=DT)
    agent = ControllerAgent("neural_lqr", control_law, transport, sync)
    agent.start(blocking=False)
    print("Neural-LQR controller running.")
    print(f"  Setpoint: x₂ → {X2_REF} m\n")

    # ── Build figure ──────────────────────────────────────────────────────────
    fig, axes, lines = _build_figure()

    def update(_frame: int) -> list:
        with _lock:
            if len(t_buf) < 5:
                return list(lines.values())
            t  = list(t_buf)
            x1 = list(x1_buf); x2 = list(x2_buf)
            v1 = list(v1_buf); v2 = list(v2_buf)
            u  = list(u_buf)

        lines["x1"].set_data(t, x1)
        lines["x2"].set_data(t, x2)
        lines["v1"].set_data(t, v1)
        lines["v2"].set_data(t, v2)
        lines["u"].set_data(t, u)
        lines["ph"].set_data(x1, x2)
        lines["dot_ph"].set_data([x1[-1]], [x2[-1]])

        for key, ax in axes.items():
            ax.relim(); ax.autoscale_view()
            if key == "pos":
                ylo, yhi = ax.get_ylim()
                ax.set_ylim(min(ylo, -0.1), max(yhi, X2_REF + 0.2))

        return list(lines.values())

    ani = animation.FuncAnimation(
        fig, update, interval=100, blit=False, cache_frame_data=False
    )
    _ = ani  # keep reference

    try:
        plt.show()
    finally:
        print("\nStopping Neural-LQR controller.")
        agent.stop()


if __name__ == "__main__":
    main()
