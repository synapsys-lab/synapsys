"""Cart-Pole LQR — UI unificada PySide6: 3D PyVista + telemetria matplotlib.

Run:
    python examples/simulators/viz3d_cartpole_qt.py

Teclas (qualquer foco):
  A / D (hold) — força no carrinho  |  R — reset  |  SPACE — pausa  |  Q — fechar
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
from synapsys.simulators import CartPoleSim
from synapsys.viz.palette import Dark

# ── Parâmetros físicos ────────────────────────────────────────────────────────
M_C, M_P, L, G = 1.0, 0.1, 0.5, 9.81
DT = 0.02  # 50 Hz
X0 = np.array([0.0, 0.0, 0.18, 0.0])
PERT_MAX = 30.0
HIST_LEN = 500
MPL_SKIP = 3  # matplotlib ~17 Hz

# ── Geometria ─────────────────────────────────────────────────────────────────
CART_W, CART_D, CART_H = 0.40, 0.28, 0.12
POLE_R = 0.022
TRACK_HW = 3.5
PIVOT_Z = CART_H + 0.01

# ── Aliases de paleta ─────────────────────────────────────────────────────────
_DARK, _PANEL, _BORDER = Dark.BG, Dark.SURFACE, Dark.BORDER
_FG, _ACCENT = Dark.FG, Dark.SIG_CYAN
_GRD, _TXT = Dark.GRID, Dark.MUTED


def _vtk_transform(
    tx: float, ty: float, tz: float, ry_deg: float = 0.0, tz2: float = 0.0
) -> vtk.vtkTransform:
    t = vtk.vtkTransform()
    t.Translate(tx, ty, tz)
    t.RotateY(ry_deg)
    t.Translate(0.0, 0.0, tz2)
    return t


# ─────────────────────────────────────────────────────────────────────────────
# Janela principal
# ─────────────────────────────────────────────────────────────────────────────


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Cart-Pole LQR — UI Unificada")
        self.resize(1400, 720)

        self._paused = False
        self._pert = 0.0
        self._tick = 0

        # Simulador + LQR
        self._sim = CartPoleSim(m_c=M_C, m_p=M_P, l=L, g=G)
        self._sim.reset()
        ss = self._sim.linearize(np.zeros(4), np.zeros(1))
        self._K, _ = lqr(ss.A, ss.B, np.diag([1.0, 0.1, 100.0, 10.0]), 0.01 * np.eye(1))
        self._sim.reset(x0=X0)

        self._hist = {
            k: collections.deque(maxlen=HIST_LEN)
            for k in ("t", "pos", "vel", "ang", "angv", "u")
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
        pl.add_light(pv.Light(position=(2, -5, 8), intensity=0.9))
        pl.add_light(pv.Light(position=(-4, -3, 5), intensity=0.4))

        # Chão
        pl.add_mesh(
            pv.Box(bounds=(-TRACK_HW - 0.5, TRACK_HW + 0.5, -0.8, 0.8, -0.06, 0.0)),
            color="#1e293b",
            smooth_shading=True,
        )
        # Trilho
        pl.add_mesh(
            pv.Box(bounds=(-TRACK_HW, TRACK_HW, -0.04, 0.04, 0.0, 0.04)),
            color="#475569",
            smooth_shading=True,
        )
        # Batentes
        for sign in (-1, 1):
            pl.add_mesh(
                pv.Box(
                    bounds=(
                        sign * TRACK_HW - 0.04,
                        sign * TRACK_HW + 0.04,
                        -0.1,
                        0.1,
                        0.0,
                        0.15,
                    )
                ),
                color="#ef4444",
                smooth_shading=True,
            )

        # Rodas
        wheel_offsets = [(-0.14, -0.10), (-0.14, 0.10), (0.14, -0.10), (0.14, 0.10)]
        self._wheel_actors = []
        for wx, wy in wheel_offsets:
            wm = pv.Sphere(radius=0.045, center=(wx, wy, 0.04))
            wa = pl.add_mesh(wm, color="#334155", smooth_shading=True)
            self._wheel_actors.append((wa, wx, wy))

        # Carrinho
        cart = pv.Box(
            bounds=(-CART_W / 2, CART_W / 2, -CART_D / 2, CART_D / 2, 0.0, CART_H)
        )
        self._cart_actor = pl.add_mesh(cart, color="#2563eb", smooth_shading=True)

        # Pivô
        pivot = pv.Sphere(radius=POLE_R * 2.2, center=(0, 0, 0))
        self._pivot_actor = pl.add_mesh(pivot, color="#64748b", smooth_shading=True)

        # Haste
        pole = pv.Cylinder(
            center=(0, 0, 0),
            direction=(0, 0, 1),
            height=L,
            radius=POLE_R,
            resolution=20,
        )
        self._pole_actor = pl.add_mesh(pole, color="#c8a870", smooth_shading=True)

        # Bob
        bob = pv.Sphere(radius=POLE_R * 2.8, center=(0, 0, 0))
        self._bob_actor = pl.add_mesh(bob, color="#f97316", smooth_shading=True)

        self._hud = pl.add_text(
            "", position=(12, 560), font_size=10, color="white", font="courier"
        )
        pl.add_text(
            "A/D=força  R=reset  SPACE=pausa  Q=fechar",
            position=(12, 12),
            font_size=8,
            color="#94a3b8",
        )
        pl.camera_position = [(0, -5.5, 1.2), (0, 0, 0.4), (0, 0, 1)]

    def _build_mpl(self) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setStyleSheet(f"background:{_DARK};")
        vb = QVBoxLayout(frame)
        vb.setContentsMargins(4, 4, 4, 4)

        fig = plt.figure(figsize=(6, 9), facecolor=_DARK)
        fig.suptitle(
            "Telemetria — Cart-Pole LQR",
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

        ax_pos = _ax(0)
        ax_ang = _ax(1)
        ax_u = _ax(2)
        ax_ph = _ax(3)

        ax_pos.set_title("Posição do carrinho", color="#e2e8f0", fontsize=9, pad=3)
        ax_pos.set_ylabel("m", color=_TXT, fontsize=8)
        ax_pos.axhline(0, color=_GRD, lw=0.7, ls=":")
        (self._pos_line,) = ax_pos.plot([], [], color="#3b82f6", lw=1.5)

        ax_ang.set_title("Ângulo da haste θ", color="#e2e8f0", fontsize=9, pad=3)
        ax_ang.set_ylabel("graus", color=_TXT, fontsize=8)
        ax_ang.axhline(0, color=_GRD, lw=0.7, ls=":")
        (self._ang_line,) = ax_ang.plot([], [], color="#f97316", lw=1.5)

        ax_u.set_title("Força de controle", color="#e2e8f0", fontsize=9, pad=3)
        ax_u.set_xlabel("t (s)", color=_TXT, fontsize=8)
        ax_u.set_ylabel("N", color=_TXT, fontsize=8)
        ax_u.axhline(0, color=_GRD, lw=0.7, ls=":")
        (self._u_line,) = ax_u.plot([], [], color="#ef4444", lw=1.5)

        ax_ph.set_title("Retrato de fase  (θ, θ̇)", color="#e2e8f0", fontsize=9, pad=3)
        ax_ph.set_xlabel("θ (graus)", color=_TXT, fontsize=8)
        ax_ph.set_ylabel("θ̇ (°/s)", color=_TXT, fontsize=8)
        ax_ph.axhline(0, color=_GRD, lw=0.7, ls=":")
        ax_ph.axvline(0, color=_GRD, lw=0.7, ls=":")
        (self._ph_line,) = ax_ph.plot([], [], color="#a78bfa", lw=1.0, alpha=0.8)
        (self._ph_dot,) = ax_ph.plot([], [], "o", color="#38bdf8", ms=5, zorder=5)

        self._ax_pos, self._ax_ang, self._ax_u, self._ax_ph = (
            ax_pos,
            ax_ang,
            ax_u,
            ax_ph,
        )

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
            QPushButton:hover   {{ background:#334155; }}
            QPushButton:checked {{ background:#065f46; border-color:#10b981; color:#4ade80; }}
        """

        btn_left = QPushButton("◀  Empurrar carrinho")
        btn_left.setStyleSheet(_PUSH)
        btn_left.pressed.connect(lambda: self._set_pert(-self._pert_max))
        btn_left.released.connect(lambda: self._set_pert(0.0))
        hb.addWidget(btn_left)

        mag_vb = QVBoxLayout()
        mag_vb.setSpacing(2)
        self._mag_lbl = QLabel(f"Magnitude: {int(self._pert_max)} N")
        self._mag_lbl.setStyleSheet(f"color:{_ACCENT}; font-size:10px;")
        self._mag_lbl.setAlignment(Qt.AlignCenter)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(1, 80)
        sl.setValue(int(self._pert_max))
        sl.setFixedWidth(130)
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

        btn_right = QPushButton("Empurrar carrinho  ▶")
        btn_right.setStyleSheet(_PUSH)
        btn_right.pressed.connect(lambda: self._set_pert(+self._pert_max))
        btn_right.released.connect(lambda: self._set_pert(0.0))
        hb.addWidget(btn_right)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{_BORDER};")
        hb.addWidget(sep)

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

    def _on_mag_changed(self, value: int) -> None:
        self._pert_max = float(value)
        self._mag_lbl.setText(f"Magnitude: {value} N")

    def _toggle_pause(self, checked: bool) -> None:
        self._paused = checked
        self._pause_btn.setText("▶  Retomar" if checked else "⏸  Pausa")

    def _reset_sim(self) -> None:
        self._sim.reset(x0=X0)
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
        info = QLabel(f"  m_c={M_C} kg  m_p={M_P} kg  l={L} m  g={G} m/s²")
        info.setStyleSheet(f"color:{_ACCENT};")
        sb.addPermanentWidget(info)

    # ── Tick ──────────────────────────────────────────────────────────────────
    def _on_tick(self) -> None:
        if self._paused:
            return

        x = self._sim.state
        u_lqr = float(np.clip((-self._K @ x).ravel()[0], -50.0, 50.0))
        u = np.array([np.clip(u_lqr + self._pert, -80.0, 80.0)])
        self._sim.step(u, DT)
        self._t += DT

        cart_x = x[0]
        theta = x[2]
        theta_d = np.degrees(theta)

        self._cart_actor.SetUserTransform(_vtk_transform(cart_x, 0, 0))
        for wa, wx, wy in self._wheel_actors:
            wa.SetUserTransform(_vtk_transform(cart_x + wx, wy, 0))
        self._pivot_actor.SetUserTransform(_vtk_transform(cart_x, 0, PIVOT_Z))
        self._pole_actor.SetUserTransform(
            _vtk_transform(cart_x, 0, PIVOT_Z, theta_d, L / 2)
        )
        tip_x = cart_x + L * np.sin(theta)
        tip_z = PIVOT_Z + L * np.cos(theta)
        self._bob_actor.SetUserTransform(_vtk_transform(tip_x, 0, tip_z))

        pert_str = f"{self._pert:+5.0f} N" if abs(self._pert) > 0.5 else "  --"
        self._hud.SetInput(
            f"  cart pos : {cart_x:+6.3f} m\n"
            f"  cart vel : {x[1]:+6.3f} m/s\n"
            f"  ângulo   : {theta_d:+6.2f}°\n"
            f"  vel. ang.: {np.degrees(x[3]):+6.1f} °/s\n"
            f"  força LQR: {u_lqr:+6.1f} N\n"
            f"  pert.    : {pert_str}"
        )
        self._pl.render()

        self._hist["t"].append(self._t)
        self._hist["pos"].append(cart_x)
        self._hist["vel"].append(x[1])
        self._hist["ang"].append(theta_d)
        self._hist["angv"].append(np.degrees(x[3]))
        self._hist["u"].append(float(u[0]))

        self._tick = (self._tick + 1) % MPL_SKIP
        if self._tick == 0:
            self._update_mpl()

        self._status.setText(
            f"  t = {self._t:.2f} s  |  pos = {cart_x:+.3f} m  |  "
            f"θ = {theta_d:+.2f}°  |  "
            f"{'PAUSADO' if self._paused else 'rodando'}"
        )

    def _update_mpl(self) -> None:
        t = list(self._hist["t"])
        pos = list(self._hist["pos"])
        ang = list(self._hist["ang"])
        angv = list(self._hist["angv"])
        u = list(self._hist["u"])
        if len(t) < 2:
            return

        self._pos_line.set_data(t, pos)
        self._ang_line.set_data(t, ang)
        self._u_line.set_data(t, u)
        self._ph_line.set_data(ang, angv)
        self._ph_dot.set_data([ang[-1]], [angv[-1]])

        for ax in (self._ax_pos, self._ax_ang, self._ax_u):
            ax.relim()
            ax.autoscale_view()
        self._ax_ph.relim()
        self._ax_ph.autoscale_view()
        self._canvas.draw()

    # ── Teclado ───────────────────────────────────────────────────────────────
    def handle_key_press(self, key: int) -> None:
        if key == Qt.Key_A:
            self._set_pert(-self._pert_max)
        elif key == Qt.Key_D:
            self._set_pert(+self._pert_max)
        elif key == Qt.Key_R:
            self._reset_sim()
        elif key == Qt.Key_Space:
            self._pause_btn.setChecked(not self._paused)
        elif key in (Qt.Key_Q, Qt.Key_Escape):
            self.close()

    def handle_key_release(self, key: int) -> None:
        if key in (Qt.Key_A, Qt.Key_D):
            self._set_pert(0.0)

    def closeEvent(self, event) -> None:
        self._timer.stop()
        self._pl.close()
        event.accept()


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
    app.installEventFilter(_KeyFilter(win))
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
