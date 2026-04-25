"""SimViewBase — base class for all 3D + matplotlib simulation views.

Do NOT instantiate this class directly. Use one of the concrete views:
    CartPoleView, PendulumView, MassSpringDamperView
"""

from __future__ import annotations

import collections
import sys
from typing import Callable

import matplotlib

matplotlib.use("QtAgg")
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from numpy import ndarray
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
from synapsys.simulators import SimulatorBase
from synapsys.viz.palette import Dark


class SimViewBase(QMainWindow):
    """Unified 3D PyVista + matplotlib sim window with pluggable controller.

    Subclass API
    ------------
    Override class attributes for configuration, then implement all abstract
    methods. Entry point::

        CartPoleView().run()                              # built-in LQR
        CartPoleView(controller=lambda x: -K @ x).run()  # custom
    """

    # ── class-level configuration (subclasses override) ──────────────────────
    _title: str = "Synapsys Simulator"
    _mpl_title: str = "Telemetria"
    _dt: float = 0.02
    _hist_len: int = 500
    _mpl_skip: int = 3
    _pert_max_default: float = 20.0
    _slider_range: tuple = (1, 50)
    _slider_unit: str = "N"
    _splitter_w: tuple = (770, 630)
    _hud_pos: tuple = (12, 500)
    _cam_pos: tuple = ((0, -5.5, 1.2), (0, 0, 0.4), (0, 0, 1))
    _u_clip: float = 50.0
    _u_clip_total: float = 80.0
    _pert_btn_left: str = "◀  Perturbar"
    _pert_btn_right: str = "Perturbar  ▶"
    # (bg, active_bg, hover_bg, border, active_border)
    _push_colors: tuple = ("#1e3a5f", "#2563eb", "#1d4ed8", "#2563eb", "#60a5fa")

    def __init__(self, controller: Callable | None = None) -> None:
        # QMainWindow.__init__ is deferred to run() so that
        # CartPoleView().run() works without a pre-existing QApplication.
        self._controller_fn = controller
        self._paused = False
        self._pert = 0.0
        self._pert_max = self._pert_max_default
        self._tick = 0
        self._t = 0.0
        # set during _build_all()
        self._K: ndarray | None = None
        self._sim: SimulatorBase | None = None
        self._hist: dict | None = None
        self._actors: dict | None = None
        self._mpl_axes: dict | None = None
        self._mpl_lines: dict | None = None
        self._pause_btn: QPushButton | None = None
        self._mag_lbl: QLabel | None = None
        self._status_lbl: QLabel | None = None
        self._hud = None
        self._ctrl_label: str = "LQR (auto)"

    # ── public entry point ────────────────────────────────────────────────────

    def run(self) -> None:
        """Create QApplication, initialize the Qt window, build UI, and exec.

        This is the main entry point.  Call it as::

            CartPoleView().run()
        """
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        # Initialize QMainWindow now that QApplication exists.
        QMainWindow.__init__(self)
        app.setStyle("Fusion")
        _apply_dark_palette(app)
        self._build_all()
        app.installEventFilter(_KeyFilter(self))
        self.show()
        sys.exit(app.exec())

    # ── interface for subclasses (must implement) ─────────────────────────────

    def _make_sim(self) -> SimulatorBase:
        """Instantiate and return the simulator."""
        raise NotImplementedError

    def _x0(self) -> ndarray:
        """Initial state vector."""
        raise NotImplementedError

    def _equilibrium(self) -> ndarray:
        """Equilibrium state used for linearization (usually zeros)."""
        raise NotImplementedError

    def _lqr_weights(self) -> tuple:
        """Return (Q, R) matrices for LQR design."""
        raise NotImplementedError

    def _extra_hist_keys(self) -> list:
        """Additional history deque keys beyond 't'."""
        raise NotImplementedError

    def _append_hist(self, x: ndarray, u: ndarray) -> None:
        """Append current (x, u) values to self._hist."""
        raise NotImplementedError

    def _build_scene(self, pl: QtInteractor) -> dict:
        """Build 3D scene and return a dict of named actors."""
        raise NotImplementedError

    def _update_scene(self, actors: dict, x: ndarray, u: ndarray) -> None:
        """Update actor positions/properties for the current state."""
        raise NotImplementedError

    def _make_mpl(self, fig, gs) -> tuple:
        """Build matplotlib panels. Return (axes_dict, lines_dict)."""
        raise NotImplementedError

    def _refresh_mpl(self, axes: dict, lines: dict) -> None:
        """Push new history data to mpl line objects."""
        raise NotImplementedError

    def _hud_text(self, x: ndarray, u: ndarray) -> str:
        """Multi-line HUD string shown in the PyVista viewport."""
        raise NotImplementedError

    def _status_text(self, x: ndarray) -> str:
        """Left status-bar text (updated every tick)."""
        raise NotImplementedError

    def _info_text(self) -> str:
        """Permanent right status-bar text (simulator parameters)."""
        raise NotImplementedError

    # ── optional override hooks ───────────────────────────────────────────────

    def _lqr_u(self, x: ndarray) -> ndarray:
        """LQR control law u = –Kx.  Override for setpoint tracking."""
        return (-self._K @ x).ravel()

    def _pert_vector(self) -> ndarray:
        """Convert scalar _pert to an input-dimensional vector."""
        return np.array([self._pert])

    def _build_extra_controls(self, hb: QHBoxLayout) -> None:
        """Hook: add extra widgets to the control bar (e.g. setpoint buttons)."""

    def _on_reset(self) -> None:
        """Called after sim.reset().  Override for extra reset logic."""

    def _post_tick(self, x: ndarray, u: ndarray) -> None:
        """Called at the end of each tick. Override for limit checking etc."""

    # ── internal build ────────────────────────────────────────────────────────

    def _build_all(self) -> None:
        self.setWindowTitle(self._title)
        self.resize(1400, 720)

        self._sim = self._make_sim()
        self._sim.reset()

        if self._controller_fn is None:
            Q, R = self._lqr_weights()
            ss = self._sim.linearize(self._equilibrium(), np.zeros(self._sim.input_dim))
            self._K, _ = lqr(ss.A, ss.B, Q, R)
            self._ctrl_label = "LQR (auto)"
        else:
            name = getattr(self._controller_fn, "__name__", None)
            self._ctrl_label = name if (name and name != "<lambda>") else "controller"

        self._sim.reset(x0=self._x0())

        self._hist = {
            k: collections.deque(maxlen=self._hist_len)
            for k in ["t"] + self._extra_hist_keys()
        }

        self._build_layout()
        self._build_3d_panel()
        self._build_mpl_panel()
        self._build_controls_bar()
        self._build_statusbar()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start(int(self._dt * 1000))

    def _build_layout(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet(f"background:{Dark.BG};")
        self._root_vb = QVBoxLayout(central)
        self._root_vb.setContentsMargins(0, 0, 0, 0)
        self._root_vb.setSpacing(0)
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(4)
        self._splitter.setStyleSheet(f"QSplitter::handle{{background:{Dark.BORDER};}}")
        self._root_vb.addWidget(self._splitter, stretch=1)

    def _build_3d_panel(self) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        vb = QVBoxLayout(frame)
        vb.setContentsMargins(0, 0, 0, 0)

        self._pl = QtInteractor(frame)
        self._pl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vb.addWidget(self._pl)
        self._splitter.addWidget(frame)

        self._pl.set_background(Dark.BG)
        self._pl.add_light(pv.Light(position=(2, -5, 8), intensity=0.9))
        self._pl.add_light(pv.Light(position=(-4, -3, 5), intensity=0.4))

        self._actors = self._build_scene(self._pl)
        self._hud = self._pl.add_text(
            "", position=self._hud_pos, font_size=10, color="white", font="courier"
        )
        self._pl.camera_position = self._cam_pos

    def _build_mpl_panel(self) -> None:
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        frame.setStyleSheet(f"background:{Dark.BG};")
        vb = QVBoxLayout(frame)
        vb.setContentsMargins(4, 4, 4, 4)

        fig = plt.figure(figsize=(6, 9), facecolor=Dark.BG)
        fig.suptitle(
            self._mpl_title, color="white", fontsize=11, fontweight="bold", y=0.99
        )
        gs = gridspec.GridSpec(
            4, 1, figure=fig, hspace=0.60, left=0.12, right=0.97, top=0.94, bottom=0.06
        )

        self._mpl_axes, self._mpl_lines = self._make_mpl(fig, gs)

        self._canvas = FigureCanvasQTAgg(fig)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        vb.addWidget(self._canvas)
        self._splitter.addWidget(frame)
        self._splitter.setSizes(list(self._splitter_w))

    def _build_controls_bar(self) -> None:
        bar = QFrame()
        bar.setFixedHeight(80)
        bar.setStyleSheet(
            f"background:{Dark.SURFACE}; border-top:1px solid {Dark.BORDER};"
        )
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(12, 8, 12, 8)
        hb.setSpacing(10)

        bg, act, hov, brd, abrd = self._push_colors
        _PUSH = f"""
            QPushButton {{
                background:{bg}; color:{Dark.FG}; border:1px solid {brd};
                border-radius:6px; padding:8px 22px; font-size:13px; font-weight:bold;
            }}
            QPushButton:pressed {{ background:{act}; border-color:{abrd}; }}
            QPushButton:hover   {{ background:{hov}; }}
        """
        _ACT = f"""
            QPushButton {{
                background:{Dark.SURFACE}; color:{Dark.FG};
                border:1px solid {Dark.BORDER};
                border-radius:6px; padding:8px 16px; font-size:11px;
            }}
            QPushButton:hover   {{ background:#334155; }}
            QPushButton:checked {{
                background:#065f46; border-color:#10b981; color:#4ade80;
            }}
        """

        btn_l = QPushButton(self._pert_btn_left)
        btn_l.setStyleSheet(_PUSH)
        btn_l.pressed.connect(lambda: self._set_pert(-self._pert_max))
        btn_l.released.connect(lambda: self._set_pert(0.0))
        hb.addWidget(btn_l)

        mag_vb = QVBoxLayout()
        mag_vb.setSpacing(2)
        self._mag_lbl = QLabel(f"Magnitude: {int(self._pert_max)} {self._slider_unit}")
        self._mag_lbl.setStyleSheet(f"color:{Dark.SIG_CYAN}; font-size:10px;")
        self._mag_lbl.setAlignment(Qt.AlignCenter)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(*self._slider_range)
        sl.setValue(int(self._pert_max))
        sl.setFixedWidth(130)
        sl.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height:4px; background:{Dark.BORDER}; border-radius:2px; }}
            QSlider::handle:horizontal {{
                width:14px; height:14px; margin:-5px 0;
                background:{Dark.SIG_CYAN}; border-radius:7px; }}
            QSlider::sub-page:horizontal {{
                background:{Dark.SIG_CYAN}; border-radius:2px; }}
        """)
        sl.valueChanged.connect(self._on_mag_changed)
        mag_vb.addWidget(self._mag_lbl)
        mag_vb.addWidget(sl)
        hb.addLayout(mag_vb)

        btn_r = QPushButton(self._pert_btn_right)
        btn_r.setStyleSheet(_PUSH)
        btn_r.pressed.connect(lambda: self._set_pert(+self._pert_max))
        btn_r.released.connect(lambda: self._set_pert(0.0))
        hb.addWidget(btn_r)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{Dark.BORDER};")
        hb.addWidget(sep)

        self._build_extra_controls(hb)

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

    def _build_statusbar(self) -> None:
        sb = QStatusBar()
        sb.setStyleSheet(
            f"background:{Dark.SURFACE}; color:{Dark.FG}; font-family:Courier;"
        )
        self.setStatusBar(sb)
        self._status_lbl = QLabel("Pronto")
        self._status_lbl.setStyleSheet(f"color:{Dark.FG};")
        sb.addWidget(self._status_lbl)
        info = QLabel(self._info_text())
        info.setStyleSheet(f"color:{Dark.SIG_CYAN};")
        sb.addPermanentWidget(info)

    # ── simulation tick ───────────────────────────────────────────────────────

    def _on_tick(self) -> None:
        if self._paused:
            return

        x = self._sim.state
        if self._controller_fn is not None:
            u_raw = np.asarray(self._controller_fn(x)).ravel()
        else:
            u_raw = self._lqr_u(x)
        u_ctrl = np.clip(u_raw, -self._u_clip, self._u_clip)
        u = np.clip(
            u_ctrl + self._pert_vector(), -self._u_clip_total, self._u_clip_total
        )

        self._sim.step(u, self._dt)
        self._t += self._dt

        self._update_scene(self._actors, x, u)
        self._hud.SetInput(self._hud_text(x, u))
        self._pl.render()

        self._hist["t"].append(self._t)
        self._append_hist(x, u)

        self._tick = (self._tick + 1) % self._mpl_skip
        if self._tick == 0 and len(self._hist["t"]) >= 2:
            self._refresh_mpl(self._mpl_axes, self._mpl_lines)
            self._canvas.draw()

        self._status_lbl.setText(self._status_text(x))
        self._post_tick(x, u)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_pert(self, value: float) -> None:
        self._pert = value

    def _on_mag_changed(self, value: int) -> None:
        self._pert_max = float(value)
        self._mag_lbl.setText(f"Magnitude: {value} {self._slider_unit}")

    def _toggle_pause(self, checked: bool) -> None:
        self._paused = checked
        self._pause_btn.setText("▶  Retomar" if checked else "⏸  Pausa")

    def _reset_sim(self) -> None:
        self._sim.reset(x0=self._x0())
        self._t = 0.0
        for d in self._hist.values():
            d.clear()
        if self._mpl_lines:
            for line in self._mpl_lines.values():
                line.set_data([], [])
            self._canvas.draw()
        self._on_reset()

    # ── keyboard ──────────────────────────────────────────────────────────────

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


# ── support classes / helpers ─────────────────────────────────────────────────


class _KeyFilter(QObject):
    def __init__(self, win: SimViewBase) -> None:
        super().__init__()
        self._win = win

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.KeyPress:
            self._win.handle_key_press(event.key())
        elif event.type() == QEvent.KeyRelease:
            self._win.handle_key_release(event.key())
        return False


def _apply_dark_palette(app: QApplication) -> None:
    pal = QPalette()
    for role, color in [
        (QPalette.Window, Dark.BG),
        (QPalette.WindowText, Dark.FG),
        (QPalette.Base, Dark.SURFACE),
        (QPalette.Text, Dark.FG),
        (QPalette.Button, Dark.SURFACE),
        (QPalette.ButtonText, Dark.FG),
        (QPalette.Highlight, Dark.SIG_CYAN),
    ]:
        pal.setColor(role, QColor(color))
    pal.setColor(QPalette.HighlightedText, QColor(Dark.BG))
    app.setPalette(pal)


def _styled_ax(ax, panel=Dark.SURFACE, grid=Dark.GRID, muted=Dark.MUTED):
    """Apply standard dark theme to a matplotlib Axes and return it."""
    ax.set_facecolor(panel)
    ax.tick_params(colors=muted, labelsize=7)
    for sp in ax.spines.values():
        sp.set_edgecolor(grid)
    ax.grid(True, color=grid, linewidth=0.5, alpha=0.7)
    return ax
