"""Quadcopter MIMO — Neural-LQR controller + PyVista real-time 3D animation.

Demonstrates
------------
* MIMO LTI modelling with synapsys  (12 states, 4 inputs, 4 outputs)
* LQR design via synapsys.algorithms.lqr() on the MIMO plant
* Residual Neural-LQR: δu = −K·e + MLP(e), residual zeroed at init so
  the network starts at the optimal linear policy and can be fine-tuned
* Real-time 3D animation of drone pose + trajectory (PyVista, 50 Hz)
* Real-time 2D telemetry panels (matplotlib, 10 Hz, same main thread)

Architecture
------------
  sim_thread  : StateSpace.evolve() at 100 Hz (real-time paced)
  main thread : manual update loop — PyVista 3D + matplotlib telemetry

Run
---
  pip install synapsys[viz] torch matplotlib
  python 06b_neural_lqr_3d.py
"""
from __future__ import annotations

import collections
import sys
import threading
import time
from pathlib import Path

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).parent))

try:
    import pyvista as pv
except ImportError:
    print("PyVista not found.  Install with:  pip install synapsys[viz]")
    sys.exit(1)

try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("[warn] PyTorch not found — running plain LQR.")

from synapsys.algorithms import lqr
from synapsys.api import c2d, ss

from quadcopter_dynamics import (
    ARM, Q_LQR, R_LQR, U_MAX, U_MIN,
    build_matrices, figure8_ref,
)

# ── Simulation parameters ─────────────────────────────────────────────────────
DT        = 0.01    # 100 Hz
T_TOTAL   = 45.0    # s
T_HOVER   = 3.0     # takeoff hover phase
N_STEPS   = int(T_TOTAL / DT)
VIZ_HZ    = 50      # PyVista 3D refresh rate
MPL_HZ    = 10      # matplotlib panels refresh rate
TRAIL_LEN = 500     # past positions kept for trail

# ── Thread-safe circular buffers ──────────────────────────────────────────────
_lock    = threading.Lock()
_states: collections.deque = collections.deque(maxlen=TRAIL_LEN)
_refs:   collections.deque = collections.deque(maxlen=N_STEPS)
_inputs: collections.deque = collections.deque(maxlen=N_STEPS)
_times:  collections.deque = collections.deque(maxlen=N_STEPS)
_done    = [False]


# ── Neural-LQR ────────────────────────────────────────────────────────────────

def build_neural_lqr(K: np.ndarray) -> "nn.Module":
    """Residual MLP: δu = −K·e + net(e),  net initialised to zero.

    At t=0 the residual is zero → network == optimal LQR.
    Fine-tune via RL / imitation learning without API changes.
    """

    class NeuralLQR(nn.Module):
        def __init__(self, K_np: np.ndarray) -> None:
            super().__init__()
            self.register_buffer("K", torch.tensor(K_np, dtype=torch.float32))
            self.residual = nn.Sequential(
                nn.Linear(12, 64), nn.Tanh(),
                nn.Linear(64, 32), nn.Tanh(),
                nn.Linear(32,  4),
            )
            with torch.no_grad():
                nn.init.xavier_uniform_(self.residual[0].weight)
                nn.init.zeros_(self.residual[0].bias)
                nn.init.xavier_uniform_(self.residual[2].weight)
                nn.init.zeros_(self.residual[2].bias)
                nn.init.zeros_(self.residual[4].weight)   # residual starts at 0
                nn.init.zeros_(self.residual[4].bias)

        def forward(self, e: "torch.Tensor") -> "torch.Tensor":
            return -(e @ self.K.T) + self.residual(e)

    return NeuralLQR(K).eval()


# ── Simulation thread ─────────────────────────────────────────────────────────

def _sim_thread(sys_d: object, K: np.ndarray, net: object | None) -> None:
    x = np.zeros(12)

    for step in range(N_STEPS):
        t    = step * DT
        t0   = time.perf_counter()

        x_ref = np.zeros(12)
        if t < T_HOVER:
            x_ref[2] = 1.50
        else:
            x_ref = figure8_ref(t - T_HOVER)

        e = x - x_ref
        if net is not None and HAS_TORCH:
            with torch.no_grad():
                t_in    = torch.tensor(e, dtype=torch.float32).unsqueeze(0)
                delta_u: np.ndarray = net(t_in).squeeze(0).numpy()
        else:
            delta_u = -(K @ e)

        delta_u = np.clip(delta_u, U_MIN, U_MAX)
        x_next, _ = sys_d.evolve(x, delta_u)  # type: ignore[union-attr]
        x = x_next

        with _lock:
            _states.append(x.copy())
            _refs.append(x_ref.copy())
            _inputs.append(delta_u.copy())
            _times.append(t)

        elapsed = time.perf_counter() - t0
        if elapsed < DT:
            time.sleep(DT - elapsed)

    _done[0] = True


# ── PyVista 3-D drone mesh ────────────────────────────────────────────────────

def _build_drone() -> pv.PolyData:
    """X-configuration quadcopter mesh centred at origin."""
    L = ARM / np.sqrt(2.0)
    motor_xy = [(L, L), (-L, L), (-L, -L), (L, -L)]

    body  = pv.Box(bounds=[-0.065, 0.065, -0.065, 0.065, -0.022, 0.022])
    parts: list[pv.PolyData] = [body]

    for mx, my in motor_xy:
        arm = pv.Cylinder(
            center=(mx / 2, my / 2, 0.0),
            direction=(mx, my, 0.0),
            radius=0.007, height=ARM, resolution=8, capping=True,
        )
        rotor = pv.Disc(
            center=(mx, my, 0.014), normal=(0, 0, 1),
            inner=0.0, outer=0.058, r_res=1, c_res=24,
        )
        parts += [arm, rotor]

    mesh: pv.PolyData = parts[0]
    for p in parts[1:]:
        mesh = mesh.merge(p)
    return mesh


# ── PyVista scene ─────────────────────────────────────────────────────────────

def _setup_3d(pl: pv.Plotter, drone_base: pv.PolyData) -> dict:
    actors: dict = {}

    # Ground grid
    ground = pv.Plane(center=(0, 0, 0), direction=(0, 0, 1),
                      i_size=8, j_size=8, i_resolution=16, j_resolution=16)
    pl.add_mesh(ground, color="#1e293b", style="wireframe",
                line_width=0.6, opacity=0.5)

    # Hover altitude reference plane
    hover_plane = pv.Plane(center=(0, 0, 1.5), direction=(0, 0, 1),
                           i_size=3, j_size=3, i_resolution=6, j_resolution=6)
    pl.add_mesh(hover_plane, color="#0ea5e9", style="wireframe",
                line_width=0.4, opacity=0.22)

    # Figure-8 reference curve (static)
    ts    = np.linspace(0, 2 * np.pi / 0.35, 400)
    denom = 1.0 + np.sin(0.35 * ts) ** 2
    ref_pts = np.column_stack([
        0.80 * np.cos(0.35 * ts) / denom,
        0.80 * np.sin(0.35 * ts) * np.cos(0.35 * ts) / denom,
        np.full(400, 1.50),
    ])
    ref_poly        = pv.PolyData(ref_pts)
    ref_poly.lines  = np.hstack([[400], np.arange(400)])
    pl.add_mesh(ref_poly, color="#22c55e", line_width=1.5, opacity=0.65)

    # Trajectory trail
    trail_pts        = np.zeros((TRAIL_LEN, 3))
    trail_poly       = pv.PolyData(trail_pts)
    trail_poly.lines = np.hstack([[TRAIL_LEN], np.arange(TRAIL_LEN)])
    actors["trail_actor"] = pl.add_mesh(
        trail_poly, color="#3b82f6", line_width=2.5, opacity=0.85,
    )
    actors["trail_poly"] = trail_poly

    # Drone
    actors["drone"] = pl.add_mesh(
        drone_base.copy(),
        color="#e11d48", specular=0.7, specular_power=15, smooth_shading=True,
    )

    # Reference marker
    ref_sphere = pv.Sphere(radius=0.055, center=(0, 0, 1.5))
    actors["ref_actor"]  = pl.add_mesh(ref_sphere, color="#4ade80", opacity=0.85)
    actors["ref_sphere"] = ref_sphere

    # HUD text — use tuple position to get vtkTextActor (has SetInput)
    actors["hud"] = pl.add_text(
        "Initialising…",
        position=(0.01, 0.90), font_size=9, color="#e2e8f0", font="courier",
    )

    pl.set_background("#0f172a")
    pl.add_light(pv.Light(position=(2, -2, 4), color="white", intensity=0.8))
    pl.camera.position    = (4.5, -4.0, 3.5)
    pl.camera.focal_point = (0.0,  0.0, 1.0)
    pl.camera.up          = (0.0,  0.0, 1.0)
    return actors


# ── PyVista actor update ──────────────────────────────────────────────────────

def _update_pv(actors: dict, states: list, times: list, refs: list) -> None:
    if not states:
        return
    x = states[-1]
    t = times[-1] if times else 0.0

    # Drone transform
    rot       = Rotation.from_euler("xyz", x[3:6]).as_matrix()
    T         = np.eye(4)
    T[:3, :3] = rot
    T[:3, 3]  = x[:3]
    actors["drone"].user_matrix = T

    # Trail
    pts = np.array([s[:3] for s in states], dtype=float)
    n   = len(pts)
    if n < TRAIL_LEN:
        pts = np.vstack([np.tile(pts[0:1], (TRAIL_LEN - n, 1)), pts])
    actors["trail_poly"].points = pts

    # Reference marker
    if refs:
        xr = refs[-1]
        actors["ref_actor"].SetPosition(xr[0], xr[1], xr[2])

    # HUD
    phi_d, theta_d, psi_d = np.degrees(x[3:6])
    mode = "Neural-LQR" if HAS_TORCH else "LQR"
    actors["hud"].SetInput(
        f"  {mode}  |  t = {t:6.2f} s\n"
        f"  x={x[0]:+.3f}  y={x[1]:+.3f}  z={x[2]:+.3f}  m\n"
        f"  phi={phi_d:+.1f}  theta={theta_d:+.1f}  psi={psi_d:+.1f}  deg\n"
        f"  xd={x[6]:+.3f}  yd={x[7]:+.3f}  zd={x[8]:+.3f}  m/s"
    )


# ── Matplotlib telemetry window ───────────────────────────────────────────────

DARK_BG   = "#0f172a"
PANEL_BG  = "#1e293b"
GRID_COL  = "#334155"
TEXT_COL  = "#94a3b8"

CYAN    = "#38bdf8"
PINK    = "#f472b6"
YELLOW  = "#facc15"
VIOLET  = "#a78bfa"
ORANGE  = "#fb923c"
TEAL    = "#34d399"
RED     = "#ef4444"
BLUE    = "#3b82f6"
GREEN   = "#22c55e"
AMBER   = "#f59e0b"


def _build_mpl_figure() -> tuple:
    fig = plt.figure(figsize=(13, 9), facecolor=DARK_BG)
    fig.suptitle(
        "Quadcopter MIMO  —  Neural-LQR Telemetry",
        color="white", fontsize=13, fontweight="bold", y=0.98,
    )

    gs = gridspec.GridSpec(3, 2, figure=fig,
                           hspace=0.50, wspace=0.35,
                           left=0.07, right=0.97, top=0.93, bottom=0.07)

    def _ax(row, col, colspan=1):
        ax = fig.add_subplot(gs[row, col] if colspan == 1
                             else gs[row, slice(col, col + colspan)])
        ax.set_facecolor(PANEL_BG)
        ax.tick_params(colors=TEXT_COL, labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor(GRID_COL)
        ax.grid(True, color=GRID_COL, linewidth=0.5, alpha=0.7)
        return ax

    ax_xy  = _ax(0, 0)
    ax_z   = _ax(0, 1)
    ax_ang = _ax(1, 0, colspan=2)
    ax_u   = _ax(2, 0, colspan=2)

    ax_xy.set_title("Top-down  x-y  trajectory", color="#e2e8f0", fontsize=10, pad=5)
    ax_xy.set_xlabel("x  (m)", color=TEXT_COL, fontsize=9)
    ax_xy.set_ylabel("y  (m)", color=TEXT_COL, fontsize=9)
    ax_xy.set_aspect("equal")
    ts_ref   = np.linspace(0, 2 * np.pi / 0.35, 300)
    dn_ref   = 1.0 + np.sin(0.35 * ts_ref) ** 2
    x8 = 0.80 * np.cos(0.35 * ts_ref) / dn_ref
    y8 = 0.80 * np.sin(0.35 * ts_ref) * np.cos(0.35 * ts_ref) / dn_ref
    ax_xy.plot(x8, y8, color=GREEN, lw=1.0, ls="--", alpha=0.5, label="ref figure-8")
    l_traj,   = ax_xy.plot([], [], color=BLUE,  lw=1.5, label="trajectory")
    l_dot_xy, = ax_xy.plot([], [], "o", color=CYAN, ms=7, zorder=5)
    ax_xy.legend(fontsize=7, facecolor=PANEL_BG, edgecolor=GRID_COL,
                 labelcolor="#e2e8f0", loc="upper right")

    ax_z.set_title("Altitude  z(t)", color="#e2e8f0", fontsize=10, pad=5)
    ax_z.set_xlabel("t  (s)", color=TEXT_COL, fontsize=9)
    ax_z.set_ylabel("z  (m)", color=TEXT_COL, fontsize=9)
    ax_z.axhline(1.5, color=GREEN, ls="--", lw=1.0, alpha=0.5, label="z_ref = 1.5 m")
    l_z,      = ax_z.plot([], [], color=YELLOW, lw=1.8, label="z(t)")
    ax_z.legend(fontsize=7, facecolor=PANEL_BG, edgecolor=GRID_COL,
                labelcolor="#e2e8f0")

    ax_ang.set_title("Euler angles  phi, theta, psi", color="#e2e8f0", fontsize=10, pad=5)
    ax_ang.set_xlabel("t  (s)", color=TEXT_COL, fontsize=9)
    ax_ang.set_ylabel("deg", color=TEXT_COL, fontsize=9)
    ax_ang.axhline(0, color=GRID_COL, ls=":", lw=0.7, alpha=0.6)
    l_phi,    = ax_ang.plot([], [], color=VIOLET, lw=1.5, label="phi  roll")
    l_theta,  = ax_ang.plot([], [], color=ORANGE, lw=1.5, label="theta  pitch")
    l_psi,    = ax_ang.plot([], [], color=TEAL,   lw=1.5, label="psi  yaw")
    ax_ang.legend(fontsize=8, ncol=3, facecolor=PANEL_BG, edgecolor=GRID_COL,
                  labelcolor="#e2e8f0", loc="upper right")

    ax_u.set_title("Control deviations  delta_u", color="#e2e8f0", fontsize=10, pad=5)
    ax_u.set_xlabel("t  (s)", color=TEXT_COL, fontsize=9)
    ax_u.set_ylabel("N  /  Nm", color=TEXT_COL, fontsize=9)
    ax_u.axhline(0, color=GRID_COL, ls=":", lw=0.7, alpha=0.6)
    l_dF,     = ax_u.plot([], [], color=RED,   lw=1.5, label="dF  (N)")
    l_tau_p,  = ax_u.plot([], [], color=BLUE,  lw=1.5, label="tau_phi  (Nm)")
    l_tau_q,  = ax_u.plot([], [], color=GREEN, lw=1.5, label="tau_theta  (Nm)")
    l_tau_r,  = ax_u.plot([], [], color=AMBER, lw=1.5, label="tau_psi  (Nm)")
    ax_u.legend(fontsize=8, ncol=4, facecolor=PANEL_BG, edgecolor=GRID_COL,
                labelcolor="#e2e8f0", loc="upper right")

    lines = dict(
        traj=l_traj, dot_xy=l_dot_xy,
        z=l_z,
        phi=l_phi, theta=l_theta, psi=l_psi,
        dF=l_dF, tau_p=l_tau_p, tau_q=l_tau_q, tau_r=l_tau_r,
    )
    axes = dict(xy=ax_xy, z=ax_z, ang=ax_ang, u=ax_u)
    return fig, axes, lines


def _update_mpl(axes: dict, lines: dict,
                states: list, times: list, refs: list, inputs: list) -> None:
    n = min(len(times), len(states), len(refs), len(inputs))
    if n < 3:
        return

    t_arr = np.asarray(times[-n:],  dtype=float)
    s_arr = np.asarray(states[-n:], dtype=float)
    u_arr = np.asarray(inputs[-n:], dtype=float)

    lines["traj"].set_data(s_arr[:, 0], s_arr[:, 1])
    lines["dot_xy"].set_data([s_arr[-1, 0]], [s_arr[-1, 1]])
    lines["z"].set_data(t_arr, s_arr[:, 2])
    lines["phi"].set_data(t_arr,   np.degrees(s_arr[:, 3]))
    lines["theta"].set_data(t_arr, np.degrees(s_arr[:, 4]))
    lines["psi"].set_data(t_arr,   np.degrees(s_arr[:, 5]))
    lines["dF"].set_data(t_arr,    u_arr[:, 0])
    lines["tau_p"].set_data(t_arr, u_arr[:, 1])
    lines["tau_q"].set_data(t_arr, u_arr[:, 2])
    lines["tau_r"].set_data(t_arr, u_arr[:, 3])

    for key, ax in axes.items():
        ax.relim()
        ax.autoscale_view()
        if key == "xy":
            ax.set_xlim(-1.1, 1.1)
            ax.set_ylim(-1.1, 1.1)
        if key == "z":
            ax.set_ylim(-0.1, 2.0)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("  Quadcopter MIMO  —  Neural-LQR + PyVista 3D")
    print("=" * 60)

    A, B, C, D = build_matrices()
    sys_c = ss(A, B, C, D)
    sys_d = c2d(sys_c, DT)
    print(f"\nPlant: {sys_c.n_states} states · {sys_c.n_inputs} inputs "
          f"· {sys_c.n_outputs} outputs")
    print(f"Open-loop: max Re(poles) = {max(np.real(sys_c.poles())):.4f}")

    print("\nSolving LQR…")
    K, _ = lqr(A, B, Q_LQR, R_LQR)
    cl   = np.linalg.eigvals(A - B @ K)
    print(f"  K : {K.shape}    CL max Re = {max(np.real(cl)):.4f}  (< 0 ok)")

    net = None
    if HAS_TORCH:
        print("\nBuilding Neural-LQR (residual MLP 12->64->32->4)…")
        net = build_neural_lqr(K)
        n_p = sum(p.numel() for p in net.parameters())
        print(f"  {n_p:,} parameters   |   residual init to 0 -> starts at LQR")

    print(f"\nSimulation: {T_TOTAL:.0f} s @ {int(1/DT)} Hz…")
    sim = threading.Thread(target=_sim_thread, args=(sys_d, K, net), daemon=True)
    sim.start()
    time.sleep(0.12)

    # ── Matplotlib (non-blocking) ─────────────────────────────────────────────
    plt.ion()
    fig, axes, lines = _build_mpl_figure()
    plt.show(block=False)
    fig.canvas.draw()
    fig.canvas.flush_events()

    # ── PyVista (non-blocking interactive_update) ─────────────────────────────
    print("Opening PyVista 3D window…  (close window or Ctrl+C to exit)\n")
    drone_mesh = _build_drone()
    pl = pv.Plotter(
        window_size=(900, 820),
        title="Quadcopter MIMO — Neural-LQR  |  synapsys",
    )
    actors = _setup_3d(pl, drone_mesh)
    pl.show(auto_close=False, interactive_update=True)

    # ── Main update loop ──────────────────────────────────────────────────────
    pv_dt   = 1.0 / VIZ_HZ
    mpl_dt  = 1.0 / MPL_HZ
    last_pv  = time.perf_counter()
    last_mpl = time.perf_counter()

    try:
        while not _done[0]:
            now = time.perf_counter()

            if now - last_pv >= pv_dt:
                with _lock:
                    states = list(_states)
                    times  = list(_times)
                    refs   = list(_refs)
                _update_pv(actors, states, times, refs)
                pl.update()
                last_pv = now

            if now - last_mpl >= mpl_dt:
                with _lock:
                    states = list(_states)
                    times  = list(_times)
                    refs   = list(_refs)
                    inputs = list(_inputs)
                _update_mpl(axes, lines, states, times, refs, inputs)
                fig.canvas.draw()
                fig.canvas.flush_events()
                last_mpl = now

            time.sleep(0.004)

    except KeyboardInterrupt:
        print("\nInterrupted.")
    finally:
        pl.close()
        plt.close("all")

    sim.join(timeout=2.0)
    if _done[0]:
        with _lock:
            states = list(_states)
        if states:
            f = states[-1]
            print(f"\nFinal:  x={f[0]:+.3f}  y={f[1]:+.3f}  z={f[2]:+.3f} m  "
                  f"| phi={np.degrees(f[3]):+.1f} theta={np.degrees(f[4]):+.1f} "
                  f"psi={np.degrees(f[5]):+.1f} deg")
    else:
        print("\nWindow closed early.")


if __name__ == "__main__":
    main()
