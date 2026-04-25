"""Quadcopter MIMO — UI unificada PySide6: 3D PyVista + telemetria matplotlib.

Layout
------
  Janela única  ──  QSplitter horizontal
    ├── QtInteractor  (PyVista 3D, 55%)
    └── FigureCanvasQTAgg  (matplotlib, 45%)
  QStatusBar mostra t, modo, posição em tempo real.
  Diálogo de config em QDialog (substitui tkinter).

Run
---
  python 06c_unified_ui.py

Keys (dentro da view 3D)
  Q / Esc  — fechar
"""

from __future__ import annotations

import collections
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

# ── Qt backend para matplotlib ANTES de qualquer import pyplot ─────────────────
import matplotlib

matplotlib.use("QtAgg")
import matplotlib.gridspec as gridspec  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg  # noqa: E402

# ── PySide6 ───────────────────────────────────────────────────────────────────
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QRadioButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from scipy.spatial.transform import Rotation

# ── PyVista Qt widget ─────────────────────────────────────────────────────────
try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
except ImportError:
    print("Instale:  uv add pyvista pyvistaqt PySide6")
    sys.exit(1)

# ── torch (opcional) ──────────────────────────────────────────────────────────
try:
    import torch
    import torch.nn as nn

    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    print("[warn] PyTorch não encontrado — usando LQR puro.")

# ── Módulos locais ────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from quadcopter_dynamics import (
    ARM,
    Q_LQR,
    R_LQR,
    U_MAX,
    U_MIN,
    build_matrices,
    figure8_ref,
)

from synapsys.algorithms import lqr
from synapsys.api import c2d, ss
from synapsys.viz.palette import Dark

# ── Taxas de renderização ─────────────────────────────────────────────────────
DT = 0.01  # 100 Hz
VIZ_HZ = 50  # PyVista
MPL_HZ = 10  # matplotlib
TRAIL_LEN = 500

# ── Buffers thread-safe ───────────────────────────────────────────────────────
_lock = threading.Lock()
_states: collections.deque = collections.deque(maxlen=TRAIL_LEN)
_refs: collections.deque = collections.deque()
_inputs: collections.deque = collections.deque()
_times: collections.deque = collections.deque()
_done = [False]


# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SimConfig:
    t_total: float = 45.0
    t_hover: float = 3.0
    z_hover: float = 1.50
    ref_type: str = "figure8"
    fig8_amp: float = 0.80
    fig8_omega: float = 0.35
    circle_radius: float = 1.00
    circle_omega: float = 0.30


# ─────────────────────────────────────────────────────────────────────────────
# Reference trajectories
# ─────────────────────────────────────────────────────────────────────────────


def circle_ref(t: float, radius: float, omega: float, z_hover: float) -> np.ndarray:
    ref = np.zeros(12)
    ref[0] = radius * np.cos(omega * t)
    ref[1] = radius * np.sin(omega * t)
    ref[2] = z_hover
    return ref


def _wrap_angle(a: float) -> float:
    return (a + np.pi) % (2.0 * np.pi) - np.pi


def _yaw_ref_from_velocity(
    vx: float, vy: float, psi_current: float, min_speed: float = 0.08
) -> float:
    if np.hypot(vx, vy) < min_speed:
        return psi_current
    return np.arctan2(vy, vx)


def get_ref(t: float, cfg: SimConfig) -> np.ndarray:
    if t < cfg.t_hover:
        ref = np.zeros(12)
        ref[2] = cfg.z_hover
        return ref
    t_track = t - cfg.t_hover
    if cfg.ref_type == "figure8":
        return figure8_ref(
            t_track, amp=cfg.fig8_amp, omega=cfg.fig8_omega, z_hover=cfg.z_hover
        )
    if cfg.ref_type == "circle":
        return circle_ref(t_track, cfg.circle_radius, cfg.circle_omega, cfg.z_hover)
    ref = np.zeros(12)
    ref[2] = cfg.z_hover
    return ref


# ─────────────────────────────────────────────────────────────────────────────
# Config dialog (QDialog)
# ─────────────────────────────────────────────────────────────────────────────

_DARK = Dark.BG
_PANEL = Dark.SURFACE
_BORDER = Dark.BORDER
_FG = Dark.FG
_ACCENT = Dark.SIG_CYAN


def _apply_dark(widget: QWidget) -> None:
    """Minimal dark palette for a widget subtree."""
    pal = widget.palette()
    pal.setColor(QPalette.Window, QColor(_DARK))
    pal.setColor(QPalette.WindowText, QColor(_FG))
    pal.setColor(QPalette.Base, QColor(_PANEL))
    pal.setColor(QPalette.AlternateBase, QColor(_PANEL))
    pal.setColor(QPalette.Text, QColor(_FG))
    pal.setColor(QPalette.Button, QColor(_PANEL))
    pal.setColor(QPalette.ButtonText, QColor(_FG))
    pal.setColor(QPalette.Highlight, QColor(_ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor(_DARK))
    widget.setPalette(pal)
    widget.setAutoFillBackground(True)


class ConfigDialog(QDialog):
    """Diálogo de configuração da simulação."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Quadcopter MIMO — Config")
        self.setModal(True)
        _apply_dark(self)
        self.setStyleSheet(f"""
            QDialog      {{ background:{_DARK}; }}
            QGroupBox    {{ color:{_ACCENT}; border:1px solid {_BORDER};
                           border-radius:4px; margin-top:8px; padding:6px; }}
            QGroupBox::title {{ subcontrol-origin:margin; left:8px; }}
            QLabel       {{ color:{_FG}; }}
            QRadioButton {{ color:{_FG}; }}
            QDoubleSpinBox {{ background:{_PANEL}; color:{_FG};
                              border:1px solid {_BORDER}; border-radius:3px;
                              padding:2px 4px; }}
            QPushButton  {{ background:#0ea5e9; color:white; border:none;
                           border-radius:4px; padding:6px 18px; font-weight:bold; }}
            QPushButton:hover {{ background:#0284c7; }}
            QPushButton[flat="true"] {{ background:{_BORDER}; }}
        """)
        self._build_ui()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _spin(
        self, value: float, lo: float, hi: float, step: float, suffix: str = ""
    ) -> QDoubleSpinBox:
        sb = QDoubleSpinBox()
        sb.setRange(lo, hi)
        sb.setSingleStep(step)
        sb.setValue(value)
        if suffix:
            sb.setSuffix(f"  {suffix}")
        sb.setFixedWidth(130)
        return sb

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        title = QLabel("Quadcopter MIMO — Simulação")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        # — Tempo ——————————————————————————————————————————————————————————
        grp_time = QGroupBox("Tempo de simulação")
        form_time = QFormLayout(grp_time)
        self.sb_total = self._spin(45, 5, 180, 1, "s")
        self.sb_hover = self._spin(3, 1, 15, 0.5, "s")
        self.sb_z = self._spin(1.5, 0.5, 4.0, 0.1, "m")
        form_time.addRow("Duração total:", self.sb_total)
        form_time.addRow("Fase hover:", self.sb_hover)
        form_time.addRow("Altitude hover z:", self.sb_z)
        root.addWidget(grp_time)

        # — Trajetória ─────────────────────────────────────────────────────
        grp_ref = QGroupBox("Trajetória de referência")
        vb_ref = QVBoxLayout(grp_ref)
        self.rb_fig8 = QRadioButton("Figure-8  (lemniscata)")
        self.rb_circle = QRadioButton("Círculo")
        self.rb_hover = QRadioButton("Hover estático")
        self.rb_fig8.setChecked(True)
        for rb in (self.rb_fig8, self.rb_circle, self.rb_hover):
            vb_ref.addWidget(rb)
        root.addWidget(grp_ref)

        # — Figure-8 ───────────────────────────────────────────────────────
        grp_f8 = QGroupBox("Parâmetros Figure-8")
        form_f8 = QFormLayout(grp_f8)
        self.sb_f8amp = self._spin(0.80, 0.2, 2.0, 0.05, "m")
        self.sb_f8omega = self._spin(0.35, 0.1, 0.8, 0.05, "rad/s")
        form_f8.addRow("Amplitude A:", self.sb_f8amp)
        form_f8.addRow("Velocidade ω:", self.sb_f8omega)
        root.addWidget(grp_f8)

        # — Círculo ────────────────────────────────────────────────────────
        grp_ci = QGroupBox("Parâmetros Círculo")
        form_ci = QFormLayout(grp_ci)
        self.sb_cr = self._spin(1.0, 0.2, 3.0, 0.1, "m")
        self.sb_comega = self._spin(0.3, 0.1, 0.8, 0.05, "rad/s")
        form_ci.addRow("Raio R:", self.sb_cr)
        form_ci.addRow("Velocidade ω:", self.sb_comega)
        root.addWidget(grp_ci)

        # — Botões ─────────────────────────────────────────────────────────
        btns = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        btns.button(QDialogButtonBox.Ok).setText("  Iniciar simulação  ")
        btns.button(QDialogButtonBox.Cancel).setText("Cancelar")
        btns.button(QDialogButtonBox.Cancel).setProperty("flat", True)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    def config(self) -> SimConfig:
        ref = (
            "figure8"
            if self.rb_fig8.isChecked()
            else "circle"
            if self.rb_circle.isChecked()
            else "hover"
        )
        return SimConfig(
            t_total=self.sb_total.value(),
            t_hover=self.sb_hover.value(),
            z_hover=self.sb_z.value(),
            ref_type=ref,
            fig8_amp=self.sb_f8amp.value(),
            fig8_omega=self.sb_f8omega.value(),
            circle_radius=self.sb_cr.value(),
            circle_omega=self.sb_comega.value(),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Neural-LQR
# ─────────────────────────────────────────────────────────────────────────────


def build_neural_lqr(K: np.ndarray) -> "nn.Module":
    class NeuralLQR(nn.Module):
        def __init__(self, K_np: np.ndarray) -> None:
            super().__init__()
            self.register_buffer("K", torch.tensor(K_np, dtype=torch.float32))
            self.residual = nn.Sequential(
                nn.Linear(12, 64),
                nn.Tanh(),
                nn.Linear(64, 32),
                nn.Tanh(),
                nn.Linear(32, 4),
            )
            with torch.no_grad():
                for layer in self.residual:
                    if isinstance(layer, nn.Linear):
                        nn.init.xavier_uniform_(layer.weight)
                        nn.init.zeros_(layer.bias)
                nn.init.zeros_(self.residual[-1].weight)

        def forward(self, e: "torch.Tensor") -> "torch.Tensor":
            return -(e @ self.K.T) + self.residual(e)

    return NeuralLQR(K).eval()


# ─────────────────────────────────────────────────────────────────────────────
# Thread de simulação
# ─────────────────────────────────────────────────────────────────────────────


def _sim_thread(
    sys_d: object, K: np.ndarray, net: object | None, cfg: SimConfig
) -> None:
    global _refs, _inputs, _times
    n_steps = int(cfg.t_total / DT)
    x = np.zeros(12)

    with _lock:
        _refs = collections.deque(maxlen=n_steps)
        _inputs = collections.deque(maxlen=n_steps)
        _times = collections.deque(maxlen=n_steps)

    for step in range(n_steps):
        t = step * DT
        t0 = time.perf_counter()
        x_ref = get_ref(t, cfg)
        if t >= cfg.t_hover:
            x_ref[5] = _yaw_ref_from_velocity(x[6], x[7], x[5])
        e = x - x_ref
        e[5] = _wrap_angle(e[5])

        if net is not None and HAS_TORCH:
            with torch.no_grad():
                t_in = torch.tensor(e, dtype=torch.float32).unsqueeze(0)
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


# ─────────────────────────────────────────────────────────────────────────────
# Cena PyVista
# ─────────────────────────────────────────────────────────────────────────────


def _build_drone() -> pv.PolyData:
    L = ARM / np.sqrt(2.0)
    motor_xy = [(L, L), (-L, L), (-L, -L), (L, -L)]
    body = pv.Box(bounds=[-0.065, 0.065, -0.065, 0.065, -0.022, 0.022])
    parts: list[pv.PolyData] = [body]
    for mx, my in motor_xy:
        arm = pv.Cylinder(
            center=(mx / 2, my / 2, 0.0),
            direction=(mx, my, 0.0),
            radius=0.007,
            height=ARM,
            resolution=8,
            capping=True,
        )
        rotor = pv.Disc(
            center=(mx, my, 0.014),
            normal=(0, 0, 1),
            inner=0.0,
            outer=0.058,
            r_res=1,
            c_res=24,
        )
        parts += [arm, rotor]
    mesh: pv.PolyData = parts[0]
    for p in parts[1:]:
        mesh = mesh.merge(p)
    return mesh


def _setup_3d(pl: pv.Plotter, drone_base: pv.PolyData, cfg: SimConfig) -> dict:
    actors: dict = {}

    pl.set_background("#0f172a")
    pl.add_light(pv.Light(position=(2, -2, 4), color="white", intensity=0.8))

    pl.add_mesh(
        pv.Plane(
            center=(0, 0, 0),
            direction=(0, 0, 1),
            i_size=8,
            j_size=8,
            i_resolution=16,
            j_resolution=16,
        ),
        color="#1e293b",
        style="wireframe",
        line_width=0.6,
        opacity=0.5,
    )
    pl.add_mesh(
        pv.Plane(
            center=(0, 0, cfg.z_hover),
            direction=(0, 0, 1),
            i_size=3,
            j_size=3,
            i_resolution=6,
            j_resolution=6,
        ),
        color="#0ea5e9",
        style="wireframe",
        line_width=0.4,
        opacity=0.22,
    )

    # Curva de referência (preview estático)
    ts = np.linspace(0, 2 * np.pi / max(cfg.fig8_omega, cfg.circle_omega), 400)
    if cfg.ref_type == "figure8":
        denom = 1.0 + np.sin(cfg.fig8_omega * ts) ** 2
        ref_pts = np.column_stack(
            [
                cfg.fig8_amp * np.cos(cfg.fig8_omega * ts) / denom,
                cfg.fig8_amp
                * np.sin(cfg.fig8_omega * ts)
                * np.cos(cfg.fig8_omega * ts)
                / denom,
                np.full(400, cfg.z_hover),
            ]
        )
    elif cfg.ref_type == "circle":
        ref_pts = np.column_stack(
            [
                cfg.circle_radius * np.cos(cfg.circle_omega * ts),
                cfg.circle_radius * np.sin(cfg.circle_omega * ts),
                np.full(400, cfg.z_hover),
            ]
        )
    else:
        ref_pts = np.column_stack(
            [np.zeros(400), np.zeros(400), np.full(400, cfg.z_hover)]
        )
    ref_poly = pv.PolyData(ref_pts)
    ref_poly.lines = np.hstack([[400], np.arange(400)])
    pl.add_mesh(ref_poly, color="#22c55e", line_width=1.5, opacity=0.65)

    trail_pts = np.zeros((TRAIL_LEN, 3))
    trail_poly = pv.PolyData(trail_pts)
    trail_poly.lines = np.hstack([[TRAIL_LEN], np.arange(TRAIL_LEN)])
    actors["trail_actor"] = pl.add_mesh(
        trail_poly, color="#3b82f6", line_width=2.5, opacity=0.85
    )
    actors["trail_poly"] = trail_poly

    actors["drone"] = pl.add_mesh(
        drone_base.copy(),
        color="#e11d48",
        specular=0.7,
        specular_power=15,
        smooth_shading=True,
    )

    ref_sphere = pv.Sphere(radius=0.055, center=(0, 0, cfg.z_hover))
    actors["ref_actor"] = pl.add_mesh(ref_sphere, color="#4ade80", opacity=0.85)
    actors["ref_sphere"] = ref_sphere

    actors["hud"] = pl.add_text(
        "Inicializando…",
        position=(0.01, 0.90),
        font_size=9,
        color="#e2e8f0",
        font="courier",
    )

    pl.camera.position = (4.5, -4.0, 3.5)
    pl.camera.focal_point = (0.0, 0.0, 1.0)
    pl.camera.up = (0.0, 0.0, 1.0)
    return actors


def _update_pv(actors: dict, states: list, times: list, refs: list) -> None:
    if not states:
        return
    x = states[-1]
    t = times[-1] if times else 0.0

    rot = Rotation.from_euler("xyz", x[3:6]).as_matrix()
    T = np.eye(4)
    T[:3, :3] = rot
    T[:3, 3] = x[:3]
    actors["drone"].user_matrix = T

    pts = np.array([s[:3] for s in states], dtype=float)
    n = len(pts)
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


# ─────────────────────────────────────────────────────────────────────────────
# Figura matplotlib
# ─────────────────────────────────────────────────────────────────────────────

_MPL_DARK = Dark.BG
_MPL_PANEL = Dark.SURFACE
_MPL_GRID = Dark.GRID
_MPL_TEXT = Dark.MUTED
_MPL_CYAN = Dark.SIG_CYAN
_MPL_YELLOW = Dark.SIG_ALT
_MPL_VIOLET = Dark.SIG_CH1
_MPL_ORANGE = Dark.SIG_CH2
_MPL_TEAL = Dark.SIG_CH3
_MPL_RED = Dark.SIG_CTRL
_MPL_BLUE = Dark.SIG_POS
_MPL_GREEN = Dark.SIG_REF
_MPL_AMBER = Dark.SIG_CH4


def _build_mpl_figure(cfg: SimConfig) -> tuple:
    fig = plt.figure(figsize=(7, 9), facecolor=_MPL_DARK)
    lbl = {"figure8": "Figure-8", "circle": "Círculo", "hover": "Hover"}
    fig.suptitle(
        f"Telemetria  |  {lbl[cfg.ref_type]}",
        color="white",
        fontsize=11,
        fontweight="bold",
        y=0.99,
    )
    gs = gridspec.GridSpec(
        3,
        2,
        figure=fig,
        hspace=0.55,
        wspace=0.38,
        left=0.10,
        right=0.97,
        top=0.94,
        bottom=0.07,
    )

    def _ax(row: int, col: int, colspan: int = 1) -> plt.Axes:
        ax = fig.add_subplot(
            gs[row, col] if colspan == 1 else gs[row, slice(col, col + colspan)]
        )
        ax.set_facecolor(_MPL_PANEL)
        ax.tick_params(colors=_MPL_TEXT, labelsize=7)
        for sp in ax.spines.values():
            sp.set_edgecolor(_MPL_GRID)
        ax.grid(True, color=_MPL_GRID, linewidth=0.5, alpha=0.7)
        return ax

    ax_xy = _ax(0, 0)
    ax_z = _ax(0, 1)
    ax_ang = _ax(1, 0, colspan=2)
    ax_u = _ax(2, 0, colspan=2)

    ax_xy.set_title("x-y  (top-down)", color="#e2e8f0", fontsize=9, pad=4)
    ax_xy.set_xlabel("x (m)", color=_MPL_TEXT, fontsize=8)
    ax_xy.set_ylabel("y (m)", color=_MPL_TEXT, fontsize=8)
    ax_xy.set_aspect("equal")

    ts_ref = np.linspace(
        0, 2 * np.pi / max(cfg.fig8_omega, cfg.circle_omega, 0.01), 300
    )
    if cfg.ref_type == "figure8":
        dn = 1.0 + np.sin(cfg.fig8_omega * ts_ref) ** 2
        x8 = cfg.fig8_amp * np.cos(cfg.fig8_omega * ts_ref) / dn
        y8 = (
            cfg.fig8_amp
            * np.sin(cfg.fig8_omega * ts_ref)
            * np.cos(cfg.fig8_omega * ts_ref)
            / dn
        )
    elif cfg.ref_type == "circle":
        x8 = cfg.circle_radius * np.cos(cfg.circle_omega * ts_ref)
        y8 = cfg.circle_radius * np.sin(cfg.circle_omega * ts_ref)
    else:
        x8 = y8 = np.zeros_like(ts_ref)
    ax_xy.plot(x8, y8, color=_MPL_GREEN, lw=1.0, ls="--", alpha=0.5, label="ref")
    (l_traj,) = ax_xy.plot([], [], color=_MPL_BLUE, lw=1.5, label="pos")
    (l_dot_xy,) = ax_xy.plot([], [], "o", color=_MPL_CYAN, ms=6, zorder=5)
    ax_xy.legend(
        fontsize=7,
        facecolor=_MPL_PANEL,
        edgecolor=_MPL_GRID,
        labelcolor="#e2e8f0",
        loc="upper right",
    )

    ax_z.set_title("Altitude z(t)", color="#e2e8f0", fontsize=9, pad=4)
    ax_z.set_xlabel("t (s)", color=_MPL_TEXT, fontsize=8)
    ax_z.set_ylabel("z (m)", color=_MPL_TEXT, fontsize=8)
    ax_z.axhline(
        cfg.z_hover,
        color=_MPL_GREEN,
        ls="--",
        lw=1.0,
        alpha=0.5,
        label=f"ref={cfg.z_hover:.1f}",
    )
    (l_z,) = ax_z.plot([], [], color=_MPL_YELLOW, lw=1.8, label="z(t)")
    ax_z.legend(
        fontsize=7, facecolor=_MPL_PANEL, edgecolor=_MPL_GRID, labelcolor="#e2e8f0"
    )

    ax_ang.set_title("Ângulos de Euler", color="#e2e8f0", fontsize=9, pad=4)
    ax_ang.set_xlabel("t (s)", color=_MPL_TEXT, fontsize=8)
    ax_ang.set_ylabel("graus", color=_MPL_TEXT, fontsize=8)
    ax_ang.axhline(0, color=_MPL_GRID, ls=":", lw=0.7, alpha=0.6)
    (l_phi,) = ax_ang.plot([], [], color=_MPL_VIOLET, lw=1.5, label="φ roll")
    (l_theta,) = ax_ang.plot([], [], color=_MPL_ORANGE, lw=1.5, label="θ pitch")
    (l_psi,) = ax_ang.plot([], [], color=_MPL_TEAL, lw=1.5, label="ψ yaw")
    ax_ang.legend(
        fontsize=7,
        ncol=3,
        facecolor=_MPL_PANEL,
        edgecolor=_MPL_GRID,
        labelcolor="#e2e8f0",
        loc="upper right",
    )

    ax_u.set_title("Desvios de controle δu", color="#e2e8f0", fontsize=9, pad=4)
    ax_u.set_xlabel("t (s)", color=_MPL_TEXT, fontsize=8)
    ax_u.set_ylabel("N / Nm", color=_MPL_TEXT, fontsize=8)
    ax_u.axhline(0, color=_MPL_GRID, ls=":", lw=0.7, alpha=0.6)
    (l_dF,) = ax_u.plot([], [], color=_MPL_RED, lw=1.5, label="δF (N)")
    (l_tau_p,) = ax_u.plot([], [], color=_MPL_BLUE, lw=1.5, label="τφ (Nm)")
    (l_tau_q,) = ax_u.plot([], [], color=_MPL_GREEN, lw=1.5, label="τθ (Nm)")
    (l_tau_r,) = ax_u.plot([], [], color=_MPL_AMBER, lw=1.5, label="τψ (Nm)")
    ax_u.legend(
        fontsize=7,
        ncol=4,
        facecolor=_MPL_PANEL,
        edgecolor=_MPL_GRID,
        labelcolor="#e2e8f0",
        loc="upper right",
    )

    lines = dict(
        traj=l_traj,
        dot_xy=l_dot_xy,
        z=l_z,
        phi=l_phi,
        theta=l_theta,
        psi=l_psi,
        dF=l_dF,
        tau_p=l_tau_p,
        tau_q=l_tau_q,
        tau_r=l_tau_r,
    )
    axes = dict(xy=ax_xy, z=ax_z, ang=ax_ang, u=ax_u)
    return fig, axes, lines


def _update_mpl(
    axes: dict, lines: dict, states: list, times: list, refs: list, inputs: list
) -> None:
    n = min(len(times), len(states), len(refs), len(inputs))
    if n < 3:
        return
    t_arr = np.asarray(times[-n:], dtype=float)
    s_arr = np.asarray(states[-n:], dtype=float)
    u_arr = np.asarray(inputs[-n:], dtype=float)

    lines["traj"].set_data(s_arr[:, 0], s_arr[:, 1])
    lines["dot_xy"].set_data([s_arr[-1, 0]], [s_arr[-1, 1]])
    lines["z"].set_data(t_arr, s_arr[:, 2])
    lines["phi"].set_data(t_arr, np.degrees(s_arr[:, 3]))
    lines["theta"].set_data(t_arr, np.degrees(s_arr[:, 4]))
    lines["psi"].set_data(t_arr, np.degrees(s_arr[:, 5]))
    lines["dF"].set_data(t_arr, u_arr[:, 0])
    lines["tau_p"].set_data(t_arr, u_arr[:, 1])
    lines["tau_q"].set_data(t_arr, u_arr[:, 2])
    lines["tau_r"].set_data(t_arr, u_arr[:, 3])

    for key, ax in axes.items():
        ax.relim()
        ax.autoscale_view()
        if key == "z":
            ax.set_ylim(-0.1, 2.5)


# ─────────────────────────────────────────────────────────────────────────────
# Janela principal
# ─────────────────────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    """Janela unificada: 3D PyVista + telemetria matplotlib + status bar."""

    def __init__(
        self, sys_d: object, K: np.ndarray, net: object | None, cfg: SimConfig
    ) -> None:
        super().__init__()
        self.setWindowTitle("Quadcopter MIMO — Neural-LQR  |  synapsys")
        self.resize(1400, 800)
        self._cfg = cfg
        self._axes: dict = {}
        self._lines: dict = {}
        self._actors: dict = {}
        self._last_mpl = 0.0

        self._build_layout()
        self._build_status_bar()
        self._start_simulation(sys_d, K, net, cfg)
        self._start_timers()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background:{_DARK};")

        splitter = QSplitter(Qt.Horizontal, central)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"QSplitter::handle {{ background:{_BORDER}; }}")
        QHBoxLayout(central).addWidget(splitter)

        # — Painel 3D (PyVista) ───────────────────────────────────────────
        self._vtk_frame = QFrame()
        self._vtk_frame.setFrameShape(QFrame.NoFrame)
        vtk_layout = QVBoxLayout(self._vtk_frame)
        vtk_layout.setContentsMargins(0, 0, 0, 0)

        self._pl = QtInteractor(self._vtk_frame)
        self._pl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vtk_layout.addWidget(self._pl)

        drone_mesh = _build_drone()
        self._actors = _setup_3d(self._pl, drone_mesh, self._cfg)

        splitter.addWidget(self._vtk_frame)

        # — Painel matplotlib ─────────────────────────────────────────────
        mpl_frame = QFrame()
        mpl_frame.setFrameShape(QFrame.NoFrame)
        mpl_frame.setStyleSheet(f"background:{_DARK};")
        mpl_layout = QVBoxLayout(mpl_frame)
        mpl_layout.setContentsMargins(4, 4, 4, 4)

        fig, self._axes, self._lines = _build_mpl_figure(self._cfg)
        self._canvas = FigureCanvasQTAgg(fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mpl_layout.addWidget(self._canvas)

        splitter.addWidget(mpl_frame)

        # Proporção inicial: 55% / 45%
        total = 1400
        splitter.setSizes([int(total * 0.55), int(total * 0.45)])

    def _build_status_bar(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet(f"background:{_PANEL}; color:{_FG}; font-family:Courier;")
        self.setStatusBar(sb)
        self._status_lbl = QLabel("Inicializando…")
        self._status_lbl.setStyleSheet(f"color:{_FG};")
        sb.addWidget(self._status_lbl)
        mode = "Neural-LQR" if HAS_TORCH else "LQR puro"
        self._mode_lbl = QLabel(
            f"  Modo: {mode}  |  ref: {self._cfg.ref_type}  |  t_total: {self._cfg.t_total:.0f} s"
        )
        self._mode_lbl.setStyleSheet(f"color:{_ACCENT};")
        sb.addPermanentWidget(self._mode_lbl)

    # ── Simulação ─────────────────────────────────────────────────────────────
    def _start_simulation(
        self, sys_d: object, K: np.ndarray, net: object | None, cfg: SimConfig
    ) -> None:
        self._sim_thread = threading.Thread(
            target=_sim_thread, args=(sys_d, K, net, cfg), daemon=True
        )
        self._sim_thread.start()

    # ── Timers ────────────────────────────────────────────────────────────────
    def _start_timers(self) -> None:
        self._timer_viz = QTimer(self)
        self._timer_viz.timeout.connect(self._update_viz)
        self._timer_viz.start(int(1000 / VIZ_HZ))  # ms

        self._timer_mpl = QTimer(self)
        self._timer_mpl.timeout.connect(self._update_mpl_slot)
        self._timer_mpl.start(int(1000 / MPL_HZ))

    def _update_viz(self) -> None:
        with _lock:
            states_s = list(_states)
            times_s = list(_times)
            refs_s = list(_refs)

        _update_pv(self._actors, states_s, times_s, refs_s)
        self._pl.render()

        if states_s and times_s:
            x = states_s[-1]
            t = times_s[-1]
            self._status_lbl.setText(
                f"  t = {t:6.2f} s  |  "
                f"pos = ({x[0]:+.3f}, {x[1]:+.3f}, {x[2]:+.3f}) m  |  "
                f"z err = {(x[2] - self._cfg.z_hover):+.3f} m"
            )

        if _done[0]:
            self._timer_viz.stop()
            self._timer_mpl.stop()
            self._status_lbl.setText(
                f"  Simulação concluída  (t = {self._cfg.t_total:.0f} s)"
            )

    def _update_mpl_slot(self) -> None:
        with _lock:
            states_s = list(_states)
            times_s = list(_times)
            refs_s = list(_refs)
            inputs_s = list(_inputs)

        _update_mpl(self._axes, self._lines, states_s, times_s, refs_s, inputs_s)
        self._canvas.draw()

    # ── Fechar ────────────────────────────────────────────────────────────────
    def closeEvent(self, event) -> None:
        self._timer_viz.stop()
        self._timer_mpl.stop()
        self._pl.close()
        event.accept()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Paleta dark global
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(_DARK))
    pal.setColor(QPalette.WindowText, QColor(_FG))
    pal.setColor(QPalette.Base, QColor(_PANEL))
    pal.setColor(QPalette.Text, QColor(_FG))
    pal.setColor(QPalette.Button, QColor(_PANEL))
    pal.setColor(QPalette.ButtonText, QColor(_FG))
    pal.setColor(QPalette.Highlight, QColor(_ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor(_DARK))
    app.setPalette(pal)

    print("=" * 60)
    print("  Quadcopter MIMO — Neural-LQR + UI Unificada PySide6")
    print("=" * 60)

    # — Config dialog —
    dlg = ConfigDialog()
    if dlg.exec() != QDialog.Accepted:
        print("Cancelado.")
        return
    cfg = dlg.config()
    print(
        f"\nConfig: t={cfg.t_total:.0f}s  hover={cfg.t_hover:.1f}s  "
        f"z={cfg.z_hover:.1f}m  ref={cfg.ref_type}"
    )

    # — Modelo —
    A, B, C, D = build_matrices()
    sys_c = ss(A, B, C, D)
    sys_d = c2d(sys_c, DT)
    print(f"Planta: {sys_c.n_states} estados · {sys_c.n_inputs} entradas")

    print("Calculando LQR…")
    K, _ = lqr(A, B, Q_LQR, R_LQR)
    cl = np.linalg.eigvals(A - B @ K)
    print(f"  K: {K.shape}    CL max Re = {max(np.real(cl)):.4f}  (< 0 ok)")

    net = None
    if HAS_TORCH:
        print("Construindo Neural-LQR (12→64→32→4)…")
        net = build_neural_lqr(K)

    # — Janela principal —
    win = MainWindow(sys_d, K, net, cfg)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
