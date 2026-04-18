"""Quadcopter MIMO — Neural-LQR controller + PyVista real-time 3D animation.

Demonstrates
------------
* MIMO LTI modelling with synapsys  (12 states, 4 inputs, 4 outputs)
* LQR design via synapsys.algorithms.lqr() on the MIMO plant
* Residual Neural-LQR: δu = −K·e + MLP(e), residual zeroed at init
* Real-time 3D animation of drone pose + trajectory (PyVista, 50 Hz)
* Real-time 2D telemetry panels (matplotlib, 10 Hz, same main thread)
* Tkinter config GUI: simulation time, reference trajectory, parameters

Architecture
------------
  config GUI  : tkinter dialog (closes before simulation starts)
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
import tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path
from tkinter import ttk

_SAVE_MODE = "--save" in sys.argv   # choose backend before pyplot import
import matplotlib
matplotlib.use("Agg" if _SAVE_MODE else "TkAgg")
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

# ── Fixed rendering rates ─────────────────────────────────────────────────────
DT        = 0.01    # 100 Hz simulation
VIZ_HZ    = 50      # PyVista refresh rate
MPL_HZ    = 10      # matplotlib refresh rate
TRAIL_LEN = 500

# ── Thread-safe circular buffers ──────────────────────────────────────────────
_lock    = threading.Lock()
_states: collections.deque = collections.deque(maxlen=TRAIL_LEN)
_refs:   collections.deque = collections.deque()
_inputs: collections.deque = collections.deque()
_times:  collections.deque = collections.deque()
_done    = [False]


# ── Simulation config dataclass ───────────────────────────────────────────────

@dataclass
class SimConfig:
    t_total:       float = 45.0
    t_hover:       float = 3.0
    z_hover:       float = 1.50
    ref_type:      str   = "figure8"   # "figure8" | "circle" | "hover"
    fig8_amp:      float = 0.80
    fig8_omega:    float = 0.35
    circle_radius: float = 1.00
    circle_omega:  float = 0.30


# ── Reference trajectories ────────────────────────────────────────────────────

def circle_ref(t: float, radius: float, omega: float, z_hover: float) -> np.ndarray:
    ref = np.zeros(12)
    ref[0] = radius * np.cos(omega * t)
    ref[1] = radius * np.sin(omega * t)
    ref[2] = z_hover
    return ref


def get_ref(t: float, cfg: SimConfig) -> np.ndarray:
    if t < cfg.t_hover:
        ref = np.zeros(12)
        ref[2] = cfg.z_hover
        return ref
    t_track = t - cfg.t_hover
    if cfg.ref_type == "figure8":
        r = figure8_ref(t_track, amp=cfg.fig8_amp,
                        omega=cfg.fig8_omega, z_hover=cfg.z_hover)
    elif cfg.ref_type == "circle":
        r = circle_ref(t_track, cfg.circle_radius, cfg.circle_omega, cfg.z_hover)
    else:
        r = np.zeros(12)
        r[2] = cfg.z_hover
    return r


# ── Config GUI ────────────────────────────────────────────────────────────────

BG      = "#0f172a"
PANEL   = "#1e293b"
BORDER  = "#334155"
FG      = "#e2e8f0"
ACCENT  = "#38bdf8"
BTN_OK  = "#0ea5e9"
BTN_CAN = "#475569"
FONT    = ("Segoe UI", 10)
FONT_H  = ("Segoe UI", 11, "bold")
FONT_S  = ("Segoe UI", 9)


def _show_config_dialog() -> SimConfig | None:
    """Opens a tkinter config dialog. Returns SimConfig or None if cancelled."""
    result: list[SimConfig | None] = [None]

    root = tk.Tk()
    root.title("Quadcopter MIMO — Simulation Config")
    root.configure(bg=BG)
    root.resizable(False, False)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _label(parent: tk.Widget, text: str, font=FONT) -> tk.Label:
        return tk.Label(parent, text=text, bg=PANEL, fg=FG, font=font)

    def _frame(parent: tk.Widget, **kw) -> tk.Frame:
        return tk.Frame(parent, bg=PANEL, bd=1, relief="flat", **kw)

    def _section(parent: tk.Widget, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=BG, pady=4)
        outer.pack(fill="x", padx=14, pady=2)
        tk.Label(outer, text=title, bg=BG, fg=ACCENT, font=FONT_H).pack(anchor="w")
        inner = tk.Frame(outer, bg=PANEL, pady=6, padx=10,
                         highlightbackground=BORDER, highlightthickness=1)
        inner.pack(fill="x")
        return inner

    def _slider_row(parent: tk.Widget, label: str,
                    var: tk.DoubleVar | tk.IntVar,
                    lo: float, hi: float, step: float,
                    fmt: str = "{:.2f}") -> None:
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, bg=PANEL, fg=FG, font=FONT,
                 width=22, anchor="w").pack(side="left")
        val_lbl = tk.Label(row, text=fmt.format(var.get()),
                           bg=PANEL, fg=ACCENT, font=FONT, width=7)
        val_lbl.pack(side="right", padx=6)

        def _update(v: str) -> None:
            val_lbl.config(text=fmt.format(float(v)))

        sc = tk.Scale(
            row, variable=var, from_=lo, to=hi, resolution=step,
            orient="horizontal", length=260, bg=PANEL, fg=FG,
            troughcolor=BORDER, activebackground=ACCENT,
            highlightthickness=0, bd=0, showvalue=False, command=_update,
        )
        sc.pack(side="left", padx=4)

    # ── variables ─────────────────────────────────────────────────────────────
    v_ttotal  = tk.DoubleVar(value=45.0)
    v_thover  = tk.DoubleVar(value=3.0)
    v_zhover  = tk.DoubleVar(value=1.5)
    v_reftype = tk.StringVar(value="figure8")
    v_f8amp   = tk.DoubleVar(value=0.80)
    v_f8omega = tk.DoubleVar(value=0.35)
    v_crad    = tk.DoubleVar(value=1.00)
    v_comega  = tk.DoubleVar(value=0.30)

    # ── layout ────────────────────────────────────────────────────────────────
    tk.Label(root, text="Quadcopter MIMO — Simulation Config",
             bg=BG, fg=FG, font=("Segoe UI", 13, "bold")).pack(pady=(14, 4))
    tk.Label(root, text="Configure parameters and click  Run Simulation",
             bg=BG, fg=BORDER, font=FONT_S).pack(pady=(0, 8))

    # — Time section —
    sec_time = _section(root, "Simulation Time")
    _slider_row(sec_time, "Total time  (s)",        v_ttotal,  5.0, 120.0, 1.0, "{:.0f} s")
    _slider_row(sec_time, "Takeoff hover phase  (s)", v_thover, 1.0,  15.0, 0.5, "{:.1f} s")
    _slider_row(sec_time, "Hover altitude  z  (m)",  v_zhover, 0.5,   4.0, 0.1, "{:.1f} m")

    # — Reference trajectory section —
    sec_ref = _section(root, "Reference Trajectory")
    ref_frame = tk.Frame(sec_ref, bg=PANEL)
    ref_frame.pack(fill="x", pady=4)
    tk.Label(ref_frame, text="Trajectory type", bg=PANEL, fg=FG, font=FONT,
             width=22, anchor="w").pack(side="left")
    for val, txt in [("figure8", "Figure-8  (lemniscate)"),
                     ("circle",  "Circle"),
                     ("hover",   "Hover  (static)")]:
        tk.Radiobutton(
            ref_frame, text=txt, variable=v_reftype, value=val,
            bg=PANEL, fg=FG, selectcolor=BORDER, activebackground=PANEL,
            activeforeground=ACCENT, font=FONT_S,
        ).pack(side="left", padx=8)

    # — Figure-8 params —
    sec_f8 = _section(root, "Figure-8 Parameters")
    _slider_row(sec_f8, "Amplitude  A  (m)",        v_f8amp,   0.2, 2.0, 0.05, "{:.2f} m")
    _slider_row(sec_f8, "Angular speed  ω  (rad/s)", v_f8omega, 0.1, 0.8, 0.05, "{:.2f} r/s")

    # — Circle params —
    sec_ci = _section(root, "Circle Parameters")
    _slider_row(sec_ci, "Radius  R  (m)",            v_crad,   0.2, 3.0, 0.1,  "{:.1f} m")
    _slider_row(sec_ci, "Angular speed  ω  (rad/s)", v_comega, 0.1, 0.8, 0.05, "{:.2f} r/s")

    # — Buttons —
    btn_row = tk.Frame(root, bg=BG)
    btn_row.pack(pady=14, padx=14, fill="x")

    def _on_run() -> None:
        result[0] = SimConfig(
            t_total       = v_ttotal.get(),
            t_hover       = v_thover.get(),
            z_hover       = v_zhover.get(),
            ref_type      = v_reftype.get(),
            fig8_amp      = v_f8amp.get(),
            fig8_omega    = v_f8omega.get(),
            circle_radius = v_crad.get(),
            circle_omega  = v_comega.get(),
        )
        root.destroy()

    def _on_cancel() -> None:
        root.destroy()

    tk.Button(
        btn_row, text="  Run Simulation  ", command=_on_run,
        bg=BTN_OK, fg="white", font=FONT_H, relief="flat",
        activebackground="#0284c7", activeforeground="white",
        padx=12, pady=6, cursor="hand2",
    ).pack(side="right", padx=4)
    tk.Button(
        btn_row, text="  Cancel  ", command=_on_cancel,
        bg=BTN_CAN, fg=FG, font=FONT, relief="flat",
        activebackground="#64748b", activeforeground="white",
        padx=12, pady=6, cursor="hand2",
    ).pack(side="right", padx=4)

    # centre on screen
    root.update_idletasks()
    w, h = root.winfo_reqwidth(), root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    root.mainloop()
    return result[0]


# ── Neural-LQR ────────────────────────────────────────────────────────────────

def build_neural_lqr(K: np.ndarray) -> "nn.Module":
    """Residual MLP: δu = −K·e + net(e),  net initialised to zero."""

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
                nn.init.zeros_(self.residual[4].weight)
                nn.init.zeros_(self.residual[4].bias)

        def forward(self, e: "torch.Tensor") -> "torch.Tensor":
            return -(e @ self.K.T) + self.residual(e)

    return NeuralLQR(K).eval()


# ── Simulation thread ─────────────────────────────────────────────────────────

def _sim_thread(sys_d: object, K: np.ndarray, net: object | None,
                cfg: SimConfig) -> None:
    global _refs, _inputs, _times
    n_steps = int(cfg.t_total / DT)
    x = np.zeros(12)

    with _lock:
        _refs   = collections.deque(maxlen=n_steps)
        _inputs = collections.deque(maxlen=n_steps)
        _times  = collections.deque(maxlen=n_steps)

    for step in range(n_steps):
        t  = step * DT
        t0 = time.perf_counter()

        x_ref   = get_ref(t, cfg)
        e       = x - x_ref

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


# ── Fast (non-real-time) simulation ──────────────────────────────────────────

def _run_fast_sim(
    sys_d: object, K: np.ndarray, net: object | None, cfg: SimConfig
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Run full simulation without real-time pacing. Returns arrays (n, dim)."""
    n_steps = int(cfg.t_total / DT)
    states  = np.zeros((n_steps, 12))
    refs    = np.zeros((n_steps, 12))
    inputs  = np.zeros((n_steps,  4))
    times   = np.zeros( n_steps)
    x = np.zeros(12)

    for step in range(n_steps):
        t     = step * DT
        x_ref = get_ref(t, cfg)
        e     = x - x_ref
        if net is not None and HAS_TORCH:
            with torch.no_grad():
                t_in    = torch.tensor(e, dtype=torch.float32).unsqueeze(0)
                delta_u: np.ndarray = net(t_in).squeeze(0).numpy()
        else:
            delta_u = -(K @ e)
        delta_u = np.clip(delta_u, U_MIN, U_MAX)
        x_next, _ = sys_d.evolve(x, delta_u)  # type: ignore[union-attr]
        x = x_next
        states[step] = x
        refs[step]   = x_ref
        inputs[step] = delta_u
        times[step]  = t
        if step % 500 == 0:
            print(f"  sim {100 * step / n_steps:.0f}%  t={t:.1f}s", end="\r", flush=True)

    print(f"  sim 100%  t={cfg.t_total:.1f}s                    ")
    return states, refs, inputs, times


# ── GIF export ────────────────────────────────────────────────────────────────

def _save_pyvista_gif(
    states: np.ndarray, refs: np.ndarray, times: np.ndarray,
    cfg: SimConfig, path: Path, fps: int = 15,
) -> None:
    """Render every sim frame off-screen and write to a GIF via PyVista."""
    n     = len(states)
    skip  = max(1, round(1.0 / (DT * fps)))
    idxs  = list(range(0, n, skip))
    print(f"  PyVista GIF: {len(idxs)} frames @ {fps} fps → {path.name}")

    drone_mesh = _build_drone()
    pl = pv.Plotter(off_screen=True, window_size=(900, 820))
    actors = _setup_3d(pl, drone_mesh, cfg)
    pl.open_gif(str(path), fps=fps)

    for k, i in enumerate(idxs):
        trail_sl = slice(max(0, i - TRAIL_LEN + 1), i + 1)
        _update_pv(
            actors,
            list(states[trail_sl]),
            [float(times[i])],
            [refs[i]],
        )
        pl.write_frame()
        if k % 30 == 0:
            print(f"  PyVista {100 * k // len(idxs):3d}%", end="\r", flush=True)

    pl.close()
    size_kb = path.stat().st_size / 1024
    print(f"  PyVista 100% — saved {path}  ({size_kb:.0f} KB)")


def _save_matplotlib_gif(
    states: np.ndarray, refs: np.ndarray,
    inputs: np.ndarray, times: np.ndarray,
    cfg: SimConfig, path: Path, fps: int = 10,
) -> None:
    """Build matplotlib figure and save all frames as a GIF (Pillow writer)."""
    from matplotlib.animation import FuncAnimation, PillowWriter

    n    = len(states)
    skip = max(1, round(1.0 / (DT * fps)))
    idxs = list(range(0, n, skip))
    print(f"  matplotlib GIF: {len(idxs)} frames @ {fps} fps → {path.name}")

    fig, axes, lines = _build_mpl_figure(cfg)
    WIN = 500  # rolling window of steps shown

    def _frame(k: int) -> list:
        i  = idxs[k]
        sl = slice(max(0, i - WIN), i + 1)
        _update_mpl(axes, lines,
                    list(states[sl]), list(times[sl]),
                    list(refs[sl]),   list(inputs[sl]))
        return list(lines.values())

    def _progress(cur: int, total: int) -> None:
        print(f"  matplotlib {100 * cur // total:3d}%", end="\r", flush=True)

    ani = FuncAnimation(fig, _frame, frames=len(idxs),
                        interval=int(1000 / fps), blit=False)
    ani.save(str(path), writer=PillowWriter(fps=fps), dpi=100,
             progress_callback=_progress)
    plt.close(fig)
    size_kb = path.stat().st_size / 1024
    print(f"  matplotlib 100% — saved {path}  ({size_kb:.0f} KB)")


# ── PyVista 3-D drone mesh ────────────────────────────────────────────────────

def _build_drone() -> pv.PolyData:
    L = ARM / np.sqrt(2.0)
    motor_xy = [(L, L), (-L, L), (-L, -L), (L, -L)]
    body  = pv.Box(bounds=[-0.065, 0.065, -0.065, 0.065, -0.022, 0.022])
    parts: list[pv.PolyData] = [body]
    for mx, my in motor_xy:
        arm = pv.Cylinder(
            center=(mx / 2, my / 2, 0.0), direction=(mx, my, 0.0),
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

def _setup_3d(pl: pv.Plotter, drone_base: pv.PolyData, cfg: SimConfig) -> dict:
    actors: dict = {}

    pl.add_mesh(
        pv.Plane(center=(0, 0, 0), direction=(0, 0, 1),
                 i_size=8, j_size=8, i_resolution=16, j_resolution=16),
        color="#1e293b", style="wireframe", line_width=0.6, opacity=0.5,
    )
    pl.add_mesh(
        pv.Plane(center=(0, 0, cfg.z_hover), direction=(0, 0, 1),
                 i_size=3, j_size=3, i_resolution=6, j_resolution=6),
        color="#0ea5e9", style="wireframe", line_width=0.4, opacity=0.22,
    )

    # Reference curve (static preview)
    ts = np.linspace(0, 2 * np.pi / max(cfg.fig8_omega, cfg.circle_omega), 400)
    if cfg.ref_type == "figure8":
        denom   = 1.0 + np.sin(cfg.fig8_omega * ts) ** 2
        ref_pts = np.column_stack([
            cfg.fig8_amp * np.cos(cfg.fig8_omega * ts) / denom,
            cfg.fig8_amp * np.sin(cfg.fig8_omega * ts) * np.cos(cfg.fig8_omega * ts) / denom,
            np.full(400, cfg.z_hover),
        ])
    elif cfg.ref_type == "circle":
        ref_pts = np.column_stack([
            cfg.circle_radius * np.cos(cfg.circle_omega * ts),
            cfg.circle_radius * np.sin(cfg.circle_omega * ts),
            np.full(400, cfg.z_hover),
        ])
    else:
        ref_pts = np.column_stack([np.zeros(400), np.zeros(400),
                                   np.full(400, cfg.z_hover)])
    ref_poly       = pv.PolyData(ref_pts)
    ref_poly.lines = np.hstack([[400], np.arange(400)])
    pl.add_mesh(ref_poly, color="#22c55e", line_width=1.5, opacity=0.65)

    trail_pts        = np.zeros((TRAIL_LEN, 3))
    trail_poly       = pv.PolyData(trail_pts)
    trail_poly.lines = np.hstack([[TRAIL_LEN], np.arange(TRAIL_LEN)])
    actors["trail_actor"] = pl.add_mesh(trail_poly, color="#3b82f6",
                                        line_width=2.5, opacity=0.85)
    actors["trail_poly"]  = trail_poly

    actors["drone"] = pl.add_mesh(
        drone_base.copy(), color="#e11d48",
        specular=0.7, specular_power=15, smooth_shading=True,
    )

    ref_sphere = pv.Sphere(radius=0.055, center=(0, 0, cfg.z_hover))
    actors["ref_actor"]  = pl.add_mesh(ref_sphere, color="#4ade80", opacity=0.85)
    actors["ref_sphere"] = ref_sphere

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

    rot       = Rotation.from_euler("xyz", x[3:6]).as_matrix()
    T         = np.eye(4)
    T[:3, :3] = rot
    T[:3, 3]  = x[:3]
    actors["drone"].user_matrix = T

    pts = np.array([s[:3] for s in states], dtype=float)
    n   = len(pts)
    if n < TRAIL_LEN:
        pts = np.vstack([np.tile(pts[0:1], (TRAIL_LEN - n, 1)), pts])
    actors["trail_poly"].points = pts

    if refs:
        xr = refs[-1]
        actors["ref_actor"].SetPosition(xr[0], xr[1], xr[2])

    phi_d, theta_d, psi_d = np.degrees(x[3:6])
    mode = "Neural-LQR" if HAS_TORCH else "LQR"
    actors["hud"].SetInput(
        f"  {mode}  |  t = {t:6.2f} s\n"
        f"  x={x[0]:+.3f}  y={x[1]:+.3f}  z={x[2]:+.3f}  m\n"
        f"  phi={phi_d:+.1f}  theta={theta_d:+.1f}  psi={psi_d:+.1f}  deg\n"
        f"  xd={x[6]:+.3f}  yd={x[7]:+.3f}  zd={x[8]:+.3f}  m/s"
    )


# ── Matplotlib telemetry ──────────────────────────────────────────────────────

_DARK   = "#0f172a"
_PANEL  = "#1e293b"
_GRID   = "#334155"
_TEXT   = "#94a3b8"
_CYAN   = "#38bdf8"
_YELLOW = "#facc15"
_VIOLET = "#a78bfa"
_ORANGE = "#fb923c"
_TEAL   = "#34d399"
_RED    = "#ef4444"
_BLUE   = "#3b82f6"
_GREEN  = "#22c55e"
_AMBER  = "#f59e0b"


def _build_mpl_figure(cfg: SimConfig) -> tuple:
    fig = plt.figure(figsize=(13, 9), facecolor=_DARK)
    lbl = {"figure8": "Figure-8", "circle": "Circle", "hover": "Hover"}
    fig.suptitle(
        f"Quadcopter MIMO  —  Neural-LQR Telemetry  |  {lbl[cfg.ref_type]}  "
        f"  t={cfg.t_total:.0f} s",
        color="white", fontsize=13, fontweight="bold", y=0.98,
    )
    gs = gridspec.GridSpec(3, 2, figure=fig,
                           hspace=0.50, wspace=0.35,
                           left=0.07, right=0.97, top=0.93, bottom=0.07)

    def _ax(row: int, col: int, colspan: int = 1) -> plt.Axes:
        ax = fig.add_subplot(gs[row, col] if colspan == 1
                             else gs[row, slice(col, col + colspan)])
        ax.set_facecolor(_PANEL)
        ax.tick_params(colors=_TEXT, labelsize=8)
        for sp in ax.spines.values():
            sp.set_edgecolor(_GRID)
        ax.grid(True, color=_GRID, linewidth=0.5, alpha=0.7)
        return ax

    ax_xy  = _ax(0, 0)
    ax_z   = _ax(0, 1)
    ax_ang = _ax(1, 0, colspan=2)
    ax_u   = _ax(2, 0, colspan=2)

    ax_xy.set_title("Top-down  x-y  trajectory", color="#e2e8f0", fontsize=10, pad=5)
    ax_xy.set_xlabel("x  (m)", color=_TEXT, fontsize=9)
    ax_xy.set_ylabel("y  (m)", color=_TEXT, fontsize=9)
    ax_xy.set_aspect("equal")

    # Static reference preview
    ts_ref = np.linspace(0, 2 * np.pi / max(cfg.fig8_omega, cfg.circle_omega, 0.01), 300)
    if cfg.ref_type == "figure8":
        dn = 1.0 + np.sin(cfg.fig8_omega * ts_ref) ** 2
        x8 = cfg.fig8_amp * np.cos(cfg.fig8_omega * ts_ref) / dn
        y8 = cfg.fig8_amp * np.sin(cfg.fig8_omega * ts_ref) * np.cos(cfg.fig8_omega * ts_ref) / dn
    elif cfg.ref_type == "circle":
        x8 = cfg.circle_radius * np.cos(cfg.circle_omega * ts_ref)
        y8 = cfg.circle_radius * np.sin(cfg.circle_omega * ts_ref)
    else:
        x8 = np.zeros_like(ts_ref)
        y8 = np.zeros_like(ts_ref)
    ax_xy.plot(x8, y8, color=_GREEN, lw=1.0, ls="--", alpha=0.5, label="ref")
    l_traj,   = ax_xy.plot([], [], color=_BLUE,  lw=1.5, label="trajectory")
    l_dot_xy, = ax_xy.plot([], [], "o", color=_CYAN, ms=7, zorder=5)
    ax_xy.legend(fontsize=7, facecolor=_PANEL, edgecolor=_GRID,
                 labelcolor="#e2e8f0", loc="upper right")

    ax_z.set_title("Altitude  z(t)", color="#e2e8f0", fontsize=10, pad=5)
    ax_z.set_xlabel("t  (s)", color=_TEXT, fontsize=9)
    ax_z.set_ylabel("z  (m)", color=_TEXT, fontsize=9)
    ax_z.axhline(cfg.z_hover, color=_GREEN, ls="--", lw=1.0, alpha=0.5,
                 label=f"z_ref = {cfg.z_hover:.1f} m")
    l_z, = ax_z.plot([], [], color=_YELLOW, lw=1.8, label="z(t)")
    ax_z.legend(fontsize=7, facecolor=_PANEL, edgecolor=_GRID, labelcolor="#e2e8f0")

    ax_ang.set_title("Euler angles  phi, theta, psi", color="#e2e8f0", fontsize=10, pad=5)
    ax_ang.set_xlabel("t  (s)", color=_TEXT, fontsize=9)
    ax_ang.set_ylabel("deg", color=_TEXT, fontsize=9)
    ax_ang.axhline(0, color=_GRID, ls=":", lw=0.7, alpha=0.6)
    l_phi,   = ax_ang.plot([], [], color=_VIOLET, lw=1.5, label="phi  roll")
    l_theta, = ax_ang.plot([], [], color=_ORANGE, lw=1.5, label="theta  pitch")
    l_psi,   = ax_ang.plot([], [], color=_TEAL,   lw=1.5, label="psi  yaw")
    ax_ang.legend(fontsize=8, ncol=3, facecolor=_PANEL, edgecolor=_GRID,
                  labelcolor="#e2e8f0", loc="upper right")

    ax_u.set_title("Control deviations  delta_u", color="#e2e8f0", fontsize=10, pad=5)
    ax_u.set_xlabel("t  (s)", color=_TEXT, fontsize=9)
    ax_u.set_ylabel("N  /  Nm", color=_TEXT, fontsize=9)
    ax_u.axhline(0, color=_GRID, ls=":", lw=0.7, alpha=0.6)
    l_dF,    = ax_u.plot([], [], color=_RED,   lw=1.5, label="dF  (N)")
    l_tau_p, = ax_u.plot([], [], color=_BLUE,  lw=1.5, label="tau_phi  (Nm)")
    l_tau_q, = ax_u.plot([], [], color=_GREEN, lw=1.5, label="tau_theta  (Nm)")
    l_tau_r, = ax_u.plot([], [], color=_AMBER, lw=1.5, label="tau_psi  (Nm)")
    ax_u.legend(fontsize=8, ncol=4, facecolor=_PANEL, edgecolor=_GRID,
                labelcolor="#e2e8f0", loc="upper right")

    lines = dict(
        traj=l_traj, dot_xy=l_dot_xy, z=l_z,
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
        if key == "z":
            ax.set_ylim(-0.1, 2.5)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Quadcopter MIMO Neural-LQR — interactive or GIF export"
    )
    parser.add_argument(
        "--save", action="store_true",
        help="Run fast sim and save quadcopter_3d.gif + quadcopter_telemetry.gif",
    )
    parser.add_argument("--fps",  type=int, default=15,
                        help="GIF frames per second (default 15)")
    parser.add_argument("--out",  type=str, default=".",
                        help="Output directory for GIF files (default: current dir)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Quadcopter MIMO  —  Neural-LQR + PyVista 3D")
    if args.save:
        print("  MODE: GIF export")
    print("=" * 60)

    # Config dialog — skipped in save mode (uses SimConfig defaults)
    if args.save:
        cfg: SimConfig = SimConfig()
    else:
        cfg = _show_config_dialog()
        if cfg is None:
            print("Cancelled.")
            return

    print(f"\nConfig: t={cfg.t_total:.0f}s  hover={cfg.t_hover:.1f}s  "
          f"z={cfg.z_hover:.1f}m  ref={cfg.ref_type}")

    # Build model
    A, B, C, D = build_matrices()
    sys_c = ss(A, B, C, D)
    sys_d = c2d(sys_c, DT)
    print(f"Plant: {sys_c.n_states} states · {sys_c.n_inputs} inputs "
          f"· {sys_c.n_outputs} outputs")

    print("Solving LQR…")
    K, _ = lqr(A, B, Q_LQR, R_LQR)
    cl   = np.linalg.eigvals(A - B @ K)
    print(f"  K : {K.shape}    CL max Re = {max(np.real(cl)):.4f}  (< 0 ok)")

    net = None
    if HAS_TORCH:
        print("Building Neural-LQR (12->64->32->4)…")
        net = build_neural_lqr(K)

    # ── Save mode ─────────────────────────────────────────────────────────────
    if args.save:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nRunning fast simulation (no real-time pacing)…")
        states, refs, inputs, times = _run_fast_sim(sys_d, K, net, cfg)

        _save_pyvista_gif(
            states, refs, times, cfg,
            path=out_dir / "quadcopter_3d.gif",
            fps=args.fps,
        )
        _save_matplotlib_gif(
            states, refs, inputs, times, cfg,
            path=out_dir / "quadcopter_telemetry.gif",
            fps=args.fps,
        )
        print(f"\nDone. GIFs saved to: {out_dir.resolve()}/")
        return

    # ── Interactive mode ───────────────────────────────────────────────────────
    sim = threading.Thread(target=_sim_thread, args=(sys_d, K, net, cfg), daemon=True)
    sim.start()
    time.sleep(0.12)

    plt.ion()
    fig, axes, lines = _build_mpl_figure(cfg)
    plt.show(block=False)
    fig.canvas.draw()
    fig.canvas.flush_events()

    print("Opening PyVista 3D window…  (close window or Ctrl+C to exit)\n")
    drone_mesh = _build_drone()
    pl = pv.Plotter(
        window_size=(900, 820),
        title="Quadcopter MIMO — Neural-LQR  |  synapsys",
    )
    actors = _setup_3d(pl, drone_mesh, cfg)
    pl.show(auto_close=False, interactive_update=True)

    pv_dt    = 1.0 / VIZ_HZ
    mpl_dt   = 1.0 / MPL_HZ
    last_pv  = time.perf_counter()
    last_mpl = time.perf_counter()

    try:
        while not _done[0]:
            now = time.perf_counter()
            if now - last_pv >= pv_dt:
                with _lock:
                    states_s = list(_states)
                    times_s  = list(_times)
                    refs_s   = list(_refs)
                _update_pv(actors, states_s, times_s, refs_s)
                pl.update()
                last_pv = now
            if now - last_mpl >= mpl_dt:
                with _lock:
                    states_s = list(_states)
                    times_s  = list(_times)
                    refs_s   = list(_refs)
                    inputs_s = list(_inputs)
                _update_mpl(axes, lines, states_s, times_s, refs_s, inputs_s)
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
            final = list(_states)
        if final:
            f = final[-1]
            print(f"\nFinal:  x={f[0]:+.3f}  y={f[1]:+.3f}  z={f[2]:+.3f} m  "
                  f"| phi={np.degrees(f[3]):+.1f} theta={np.degrees(f[4]):+.1f} "
                  f"psi={np.degrees(f[5]):+.1f} deg")
    else:
        print("\nWindow closed early.")


if __name__ == "__main__":
    main()
