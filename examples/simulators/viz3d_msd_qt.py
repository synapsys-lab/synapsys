"""Mass-Spring-Damper — UI unificada PySide6: 3D PyVista + telemetria matplotlib.

Run:
    python examples/simulators/viz3d_msd_qt.py

Teclas (qualquer foco):
  A / D (hold) — força externa  |  1/2/3 — setpoint  |  R — reset
  SPACE — pausa/retoma          |  Q / Esc — fechar
"""

from __future__ import annotations

import collections
import sys

import matplotlib

matplotlib.use("QtAgg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
import vtk
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import MassSpringDamperSim
from synapsys.viz.palette import Dark

# ── Parâmetros físicos ────────────────────────────────────────────────────────
M, C, K_SPR = 1.0, 0.5, 2.0
DT = 0.01  # 100 Hz
PERT_MAX = 15.0
HIST_LEN = 600  # pontos de histórico (~6 s)
MPL_SKIP = 5  # atualiza matplotlib a cada N ticks (20 Hz)
SETPOINTS = {"1": 0.0, "2": 1.5, "3": -1.5}

# ── Aliases de paleta ─────────────────────────────────────────────────────────
_DARK, _PANEL, _BORDER = Dark.BG, Dark.SURFACE, Dark.BORDER
_FG, _ACCENT = Dark.FG, Dark.SIG_CYAN
_GRD, _TXT = Dark.GRID, Dark.MUTED

# ── Geometria da cena ─────────────────────────────────────────────────────────
WALL_X = -2.5
MASS_W, MASS_D, MASS_H = 0.45, 0.45, 0.45
N_COILS, SPRING_R = 8, 0.07
SPRING_WIRE_R = 0.015
DAMP_W, DAMP_H = 0.12, 0.35
FLOOR_Y = -0.3


# ─────────────────────────────────────────────────────────────────────────────
# Geometria da mola
# ─────────────────────────────────────────────────────────────────────────────


def _spring_polydata(
    x_wall: float,
    x_mass: float,
    radius: float = SPRING_R,
    n_coils: int = N_COILS,
    n_pts: int = 400,
) -> pv.PolyData:
    z_c = FLOOR_Y + MASS_H / 2
    x0 = x_wall + 0.05
    x1 = x_mass - MASS_W / 2 - 0.02
    straight = (x1 - x0) * 0.06

    n_str = 12
    n_coil = n_pts - 2 * n_str

    xs = np.linspace(x0, x0 + straight, n_str)

    t = np.linspace(np.pi / 2, np.pi / 2 + n_coils * 2 * np.pi, n_coil)
    xc = np.linspace(x0 + straight, x1 - straight, n_coil)
    yc = radius * np.sin(t)
    zc = radius * np.cos(t) + z_c

    xe = np.linspace(x1 - straight, x1, n_str)

    x_all = np.concatenate([xs, xc, xe])
    y_all = np.concatenate([np.zeros(n_str), yc, np.zeros(n_str)])
    z_all = np.concatenate([np.full(n_str, z_c), zc, np.full(n_str, z_c)])

    pts = np.column_stack([x_all, y_all, z_all])
    return pv.Spline(pts, n_pts).tube(radius=SPRING_WIRE_R, n_sides=12)


# ─────────────────────────────────────────────────────────────────────────────
# Janela principal
# ─────────────────────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Mass-Spring-Damper LQR — UI Unificada")
        self.resize(1400, 720)

        # ── Estado de controle ────────────────────────────────────────────
        self._paused = False
        self._pert = 0.0
        self._setpoint = 0.0
        self._tick = 0

        # ── Simulador + LQR ───────────────────────────────────────────────
        self._sim = MassSpringDamperSim(m=M, c=C, k=K_SPR)
        self._sim.reset()
        ss = self._sim.linearize(np.zeros(2), np.zeros(1))
        self._K, _ = lqr(ss.A, ss.B, np.diag([20.0, 5.0]), np.eye(1))
        self._sim.reset(x0=np.zeros(2))

        # ── Histórico matplotlib ──────────────────────────────────────────
        self._hist = {
            k: collections.deque(maxlen=HIST_LEN) for k in ("t", "q", "qdot", "u")
        }
        self._t = 0.0
        self._pert_max = PERT_MAX

        self._build_layout()
        self._build_3d()
        self._build_mpl()
        self._build_controls()
        self._build_status()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(int(DT * 1000))

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background:{_DARK};")

        self._root_vb = QVBoxLayout(central)
        self._root_vb.setContentsMargins(0, 0, 0, 0)
        self._root_vb.setSpacing(0)

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet(f"QSplitter::handle{{background:{_BORDER};}}")
        self._root_vb.addWidget(self._splitter, stretch=1)

    def _build_3d(self) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        vb = QVBoxLayout(frame)
        vb.setContentsMargins(0, 0, 0, 0)

        self._pl = QtInteractor(frame)
        self._pl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vb.addWidget(self._pl)
        self._splitter.addWidget(frame)

        pl = self._pl
        pl.set_background(_DARK)
        pl.add_light(pv.Light(position=(2, -5, 6), intensity=0.9))
        pl.add_light(pv.Light(position=(-4, -2, 4), intensity=0.35))

        # Chão, parede, trilho
        pl.add_mesh(
            pv.Box(bounds=(-3.5, 3.5, -0.5, 0.5, FLOOR_Y - 0.06, FLOOR_Y)),
            color="#1e293b",
            smooth_shading=True,
        )
        pl.add_mesh(
            pv.Box(bounds=(WALL_X - 0.15, WALL_X, -0.5, 0.5, FLOOR_Y, 0.8)),
            color="#334155",
            smooth_shading=True,
        )
        pl.add_mesh(
            pv.Box(bounds=(-2.4, 2.4, -0.04, 0.04, FLOOR_Y, FLOOR_Y + 0.04)),
            color="#475569",
            smooth_shading=True,
        )

        # Amortecedor
        damp = pv.Box(
            bounds=(-DAMP_W / 2, DAMP_W / 2, -DAMP_W / 2, DAMP_W / 2, 0.0, DAMP_H)
        )
        self._damp_actor = pl.add_mesh(
            damp, color="#64748b", smooth_shading=True, opacity=0.7
        )

        # Mola (rebuilt cada frame)
        self._spring_mesh = _spring_polydata(WALL_X, 0.0)
        self._spring_actor = pl.add_mesh(
            self._spring_mesh, color="#c8a870", smooth_shading=True
        )

        # Massa
        mass = pv.Box(
            bounds=(
                -MASS_W / 2,
                MASS_W / 2,
                -MASS_D / 2,
                MASS_D / 2,
                FLOOR_Y,
                FLOOR_Y + MASS_H,
            )
        )
        self._mass_actor = pl.add_mesh(mass, color="#2563eb", smooth_shading=True)

        # Setpoint
        setpt = pv.Box(
            bounds=(-0.015, 0.015, -0.3, 0.3, FLOOR_Y - 0.02, FLOOR_Y + MASS_H + 0.1)
        )
        self._setpt_actor = pl.add_mesh(setpt, color="#16a34a", opacity=0.6)

        self._hud = pl.add_text(
            "", position=(12, 480), font_size=10, color="white", font="courier"
        )
        pl.add_text(
            "A/D=força  1/2/3=setpoint  R=reset  SPACE=pausa  Q=fechar",
            position=(12, 12),
            font_size=8,
            color="#94a3b8",
        )
        pl.camera_position = [(0, -6, 0.4), (0, 0, 0.1), (0, 0, 1)]

    def _build_mpl(self) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setStyleSheet(f"background:{_DARK};")
        vb = QVBoxLayout(frame)
        vb.setContentsMargins(4, 4, 4, 4)

        fig = plt.figure(figsize=(6, 9), facecolor=_DARK)
        fig.suptitle(
            "Telemetria — Mass-Spring-Damper LQR",
            color="white",
            fontsize=11,
            fontweight="bold",
            y=0.99,
        )
        gs = gridspec.GridSpec(
            4, 1, figure=fig, hspace=0.60, left=0.12, right=0.97, top=0.94, bottom=0.06
        )

        def _ax(row: int) -> plt.Axes:
            ax = fig.add_subplot(gs[row])
            ax.set_facecolor(_PANEL)
            ax.tick_params(colors=_TXT, labelsize=7)
            for sp in ax.spines.values():
                sp.set_edgecolor(_GRD)
            ax.grid(True, color=_GRD, linewidth=0.5, alpha=0.7)
            return ax

        ax_q = _ax(0)
        ax_v = _ax(1)
        ax_u = _ax(2)
        ax_ph = _ax(3)

        ax_q.set_title("Posição q(t)", color="#e2e8f0", fontsize=9, pad=3)
        ax_q.set_ylabel("m", color=_TXT, fontsize=8)
        (self._sp_line,) = ax_q.plot([], [], "--", color="#16a34a", lw=1.0, label="sp")
        (self._q_line,) = ax_q.plot([], [], color="#3b82f6", lw=1.5, label="q")
        ax_q.legend(fontsize=7, facecolor=_PANEL, edgecolor=_GRD, labelcolor="#e2e8f0")

        ax_v.set_title("Velocidade q̇(t)", color="#e2e8f0", fontsize=9, pad=3)
        ax_v.set_ylabel("m/s", color=_TXT, fontsize=8)
        (self._v_line,) = ax_v.plot([], [], color="#f97316", lw=1.5)

        ax_u.set_title("Força de controle u(t)", color="#e2e8f0", fontsize=9, pad=3)
        ax_u.set_xlabel("t (s)", color=_TXT, fontsize=8)
        ax_u.set_ylabel("N", color=_TXT, fontsize=8)
        ax_u.axhline(0, color=_GRD, lw=0.7, ls=":")
        (self._u_line,) = ax_u.plot([], [], color="#ef4444", lw=1.5)

        ax_ph.set_title("Retrato de fase", color="#e2e8f0", fontsize=9, pad=3)
        ax_ph.set_xlabel("q (m)", color=_TXT, fontsize=8)
        ax_ph.set_ylabel("q̇ (m/s)", color=_TXT, fontsize=8)
        ax_ph.axhline(0, color=_GRD, lw=0.7, ls=":")
        ax_ph.axvline(0, color=_GRD, lw=0.7, ls=":")
        (self._ph_line,) = ax_ph.plot([], [], color="#a78bfa", lw=1.0, alpha=0.8)
        (self._ph_dot,) = ax_ph.plot([], [], "o", color="#38bdf8", ms=5, zorder=5)

        self._ax_q, self._ax_v, self._ax_u, self._ax_ph = ax_q, ax_v, ax_u, ax_ph

        self._canvas = FigureCanvasQTAgg(fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vb.addWidget(self._canvas)
        self._splitter.addWidget(frame)
        self._splitter.setSizes([770, 630])

    def _build_controls(self) -> None:
        bar = QFrame()
        bar.setFixedHeight(80)
        bar.setStyleSheet(f"background:{_PANEL}; border-top:1px solid {_BORDER};")
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(12, 8, 12, 8)
        hb.setSpacing(10)

        _PUSH = f"""
            QPushButton {{
                background:#1e3a5f; color:{_FG}; border:1px solid #2563eb;
                border-radius:6px; padding:8px 22px; font-size:13px; font-weight:bold;
            }}
            QPushButton:pressed {{ background:#2563eb; border-color:#60a5fa; }}
            QPushButton:hover   {{ background:#1d4ed8; }}
        """
        _ACT = f"""
            QPushButton {{
                background:{_PANEL}; color:{_FG}; border:1px solid {_BORDER};
                border-radius:6px; padding:8px 16px; font-size:11px;
            }}
            QPushButton:hover    {{ background:#334155; }}
            QPushButton:checked  {{ background:#065f46; border-color:#10b981; color:#4ade80; }}
        """
        _SP = f"""
            QPushButton {{
                background:{_DARK}; color:{_FG}; border:1px solid {_BORDER};
                border-radius:5px; padding:6px 12px; font-size:11px;
            }}
            QPushButton:checked  {{ background:#14532d; border-color:#16a34a; color:#4ade80; }}
            QPushButton:hover    {{ background:#1e293b; }}
        """

        # ── Botões de perturbação (hold) ───────────────────────────────────
        btn_left = QPushButton("◀  Empurrar")
        btn_left.setStyleSheet(_PUSH)
        btn_left.pressed.connect(lambda: self._set_pert(-self._pert_max))
        btn_left.released.connect(lambda: self._set_pert(0.0))
        hb.addWidget(btn_left)

        # ── Slider de magnitude ────────────────────────────────────────────
        mag_vb = QVBoxLayout()
        mag_vb.setSpacing(2)
        self._mag_lbl = QLabel(f"Magnitude: {int(self._pert_max)} N")
        self._mag_lbl.setStyleSheet(f"color:{_ACCENT}; font-size:10px;")
        self._mag_lbl.setAlignment(Qt.AlignCenter)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(1, 30)
        sl.setValue(int(self._pert_max))
        sl.setFixedWidth(120)
        sl.setStyleSheet(f"""
            QSlider::groove:horizontal {{ height:4px; background:{_BORDER}; border-radius:2px; }}
            QSlider::handle:horizontal {{
                width:14px; height:14px; margin:-5px 0;
                background:{_ACCENT}; border-radius:7px;
            }}
            QSlider::sub-page:horizontal {{ background:{_ACCENT}; border-radius:2px; }}
        """)
        sl.valueChanged.connect(self._on_mag_changed)
        mag_vb.addWidget(self._mag_lbl)
        mag_vb.addWidget(sl)
        hb.addLayout(mag_vb)

        btn_right = QPushButton("Empurrar  ▶")
        btn_right.setStyleSheet(_PUSH)
        btn_right.pressed.connect(lambda: self._set_pert(+self._pert_max))
        btn_right.released.connect(lambda: self._set_pert(0.0))
        hb.addWidget(btn_right)

        # ── Separador ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{_BORDER};")
        hb.addWidget(sep)

        # ── Setpoints ─────────────────────────────────────────────────────
        sp_lbl = QLabel("Setpoint:")
        sp_lbl.setStyleSheet(f"color:{_TXT}; font-size:10px;")
        hb.addWidget(sp_lbl)

        self._sp_group = QButtonGroup(self)
        self._sp_group.setExclusive(True)
        for label, val in [("0 m", 0.0), ("+1.5 m", 1.5), ("−1.5 m", -1.5)]:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setStyleSheet(_SP)
            b.clicked.connect(lambda _, v=val: self._set_setpoint(v))
            self._sp_group.addButton(b)
            hb.addWidget(b)
        self._sp_group.buttons()[0].setChecked(True)

        # ── Separador ─────────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet(f"color:{_BORDER};")
        hb.addWidget(sep2)

        # ── Pausa e Reset ─────────────────────────────────────────────────
        self._pause_btn = QPushButton("⏸  Pausa")
        self._pause_btn.setCheckable(True)
        self._pause_btn.setStyleSheet(_ACT)
        self._pause_btn.toggled.connect(self._toggle_pause)
        hb.addWidget(self._pause_btn)

        btn_reset = QPushButton("↺  Reset")
        btn_reset.setStyleSheet(_ACT)
        btn_reset.clicked.connect(self._reset_sim)
        hb.addWidget(btn_reset)

        hb.addStretch()
        self._root_vb.addWidget(bar)

    def _set_pert(self, value: float) -> None:
        self._pert = value

    def _set_setpoint(self, value: float) -> None:
        self._setpoint = value

    def _on_mag_changed(self, value: int) -> None:
        self._pert_max = float(value)
        self._mag_lbl.setText(f"Magnitude: {value} N")

    def _toggle_pause(self, checked: bool) -> None:
        self._paused = checked
        self._pause_btn.setText("▶  Retomar" if checked else "⏸  Pausa")

    def _reset_sim(self) -> None:
        self._sim.reset(x0=np.zeros(2))
        self._t = 0.0
        for d in self._hist.values():
            d.clear()

    def _build_status(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet(f"background:{_PANEL}; color:{_FG}; font-family:Courier;")
        self.setStatusBar(sb)
        self._status = QLabel("Pronto")
        self._status.setStyleSheet(f"color:{_FG};")
        sb.addWidget(self._status)
        info = QLabel(
            f"  m={M} kg  c={C}  k={K_SPR}  |  "
            f"ωₙ={self._sim.natural_frequency():.2f} rad/s  "
            f"ζ={self._sim.damping_ratio():.3f}"
        )
        info.setStyleSheet(f"color:{_ACCENT};")
        sb.addPermanentWidget(info)

    # ── Tick ──────────────────────────────────────────────────────────────────
    def _on_tick(self) -> None:
        if self._paused:
            return

        x = self._sim.state
        sp = self._setpoint
        x_err = x - np.array([sp, 0.0])
        u_lqr = float(np.clip((-self._K @ x_err + K_SPR * sp).ravel()[0], -30.0, 30.0))
        u = np.array([np.clip(u_lqr + self._pert, -50.0, 50.0)])
        self._sim.step(u, DT)
        self._t += DT
        q = x[0]

        # 3D transforms
        t_m = vtk.vtkTransform()
        t_m.Translate(q, 0, 0)
        self._mass_actor.SetUserTransform(t_m)

        t_d = vtk.vtkTransform()
        t_d.Translate(q - MASS_W / 2 - DAMP_W / 2 - 0.04, 0, FLOOR_Y)
        self._damp_actor.SetUserTransform(t_d)

        t_sp = vtk.vtkTransform()
        t_sp.Translate(sp, 0, 0)
        self._setpt_actor.SetUserTransform(t_sp)

        new_spring = _spring_polydata(WALL_X, q)
        self._spring_mesh.points = new_spring.points
        self._spring_mesh.lines = new_spring.lines

        pert_str = f"{self._pert:+5.0f} N" if abs(self._pert) > 0.5 else "  --"
        self._hud.SetInput(
            f"  posição  : {q:+6.3f} m\n"
            f"  vel.     : {x[1]:+6.3f} m/s\n"
            f"  setpoint : {sp:+6.3f} m\n"
            f"  erro     : {(q - sp):+6.3f} m\n"
            f"  força LQR: {u_lqr:+6.1f} N\n"
            f"  pert.    : {pert_str}"
        )
        self._pl.render()

        # Histórico
        self._hist["t"].append(self._t)
        self._hist["q"].append(q)
        self._hist["qdot"].append(x[1])
        self._hist["u"].append(float(u[0]))

        self._tick = (self._tick + 1) % MPL_SKIP
        if self._tick == 0:
            self._update_mpl()

        self._status.setText(
            f"  t = {self._t:.2f} s  |  q = {q:+.3f} m  |  "
            f"erro = {(q - sp):+.3f} m  |  "
            f"{'PAUSADO' if self._paused else 'rodando'}"
        )

    def _update_mpl(self) -> None:
        t = list(self._hist["t"])
        q = list(self._hist["q"])
        v = list(self._hist["qdot"])
        u = list(self._hist["u"])
        if len(t) < 2:
            return

        sp_arr = [self._setpoint] * len(t)
        self._sp_line.set_data(t, sp_arr)
        self._q_line.set_data(t, q)
        self._v_line.set_data(t, v)
        self._u_line.set_data(t, u)
        self._ph_line.set_data(q, v)
        self._ph_dot.set_data([q[-1]], [v[-1]])

        for ax in (self._ax_q, self._ax_v, self._ax_u):
            ax.relim()
            ax.autoscale_view()
        self._ax_ph.relim()
        self._ax_ph.autoscale_view()
        self._canvas.draw()

    # ── Teclado (global) ──────────────────────────────────────────────────────
    def handle_key_press(self, key: int) -> None:
        if key == Qt.Key_A:
            self._set_pert(-self._pert_max)
        elif key == Qt.Key_D:
            self._set_pert(+self._pert_max)
        elif key == Qt.Key_R:
            self._reset_sim()
        elif key == Qt.Key_Space:
            self._pause_btn.setChecked(not self._paused)
        elif key == Qt.Key_1:
            self._set_setpoint(SETPOINTS["1"])
            self._sp_group.buttons()[0].setChecked(True)
        elif key == Qt.Key_2:
            self._set_setpoint(SETPOINTS["2"])
            self._sp_group.buttons()[1].setChecked(True)
        elif key == Qt.Key_3:
            self._set_setpoint(SETPOINTS["3"])
            self._sp_group.buttons()[2].setChecked(True)
        elif key in (Qt.Key_Q, Qt.Key_Escape):
            self.close()

    def handle_key_release(self, key: int) -> None:
        if key in (Qt.Key_A, Qt.Key_D):
            self._set_pert(0.0)

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._pl.close()
        event.accept()


# ─────────────────────────────────────────────────────────────────────────────
# Key filter global
# ─────────────────────────────────────────────────────────────────────────────


class _KeyFilter(QObject):
    def __init__(self, win: MainWindow) -> None:
        super().__init__()
        self._win = win

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:
            self._win.handle_key_press(event.key())
        elif event.type() == QEvent.KeyRelease:
            self._win.handle_key_release(event.key())
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    for role, color in [
        (QPalette.Window, _DARK),
        (QPalette.WindowText, _FG),
        (QPalette.Base, _PANEL),
        (QPalette.Text, _FG),
        (QPalette.Button, _PANEL),
        (QPalette.ButtonText, _FG),
        (QPalette.Highlight, _ACCENT),
    ]:
        pal.setColor(role, QColor(color))
    pal.setColor(QPalette.HighlightedText, QColor(_DARK))
    app.setPalette(pal)

    win = MainWindow()
    kf = _KeyFilter(win)
    app.installEventFilter(kf)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
