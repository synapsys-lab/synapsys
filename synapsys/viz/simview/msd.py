"""MassSpringDamperView — ready-to-run MSD simulation with pluggable controller.

Usage::

    from synapsys.viz import MassSpringDamperView
    MassSpringDamperView().run()
    MassSpringDamperView(controller=lambda x: np.clip(-K@x, -30, 30)).run()
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
import vtk
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
)

from synapsys.simulators import MassSpringDamperSim
from synapsys.viz.palette import Dark

from ._base import SimViewBase, _styled_ax

# ── physical parameters ───────────────────────────────────────────────────────
_M, _C, _K = 1.0, 0.5, 2.0
_X0 = np.zeros(2)
_PERT_MAX = 15.0

# ── geometry ──────────────────────────────────────────────────────────────────
_WALL_X = -2.5
_MASS_W, _MASS_D, _MASS_H = 0.45, 0.45, 0.45
_N_COILS, _SPRING_R = 8, 0.07
_SPRING_WIRE_R = 0.015
_DAMP_W, _DAMP_H = 0.12, 0.35
_FLOOR_Y = -0.3

_DEFAULT_SETPOINTS = [("0 m", 0.0), ("+1.5 m", 1.5), ("−1.5 m", -1.5)]


def _spring_polydata(
    x_wall: float,
    x_mass: float,
    radius: float = _SPRING_R,
    n_coils: int = _N_COILS,
    n_pts: int = 400,
) -> pv.PolyData:
    z_c = _FLOOR_Y + _MASS_H / 2  # center height — matches mass face center
    x0 = x_wall + 0.05
    x1 = x_mass - _MASS_W / 2 - 0.02
    straight = (x1 - x0) * 0.06  # short flat segment at each end

    n_str = 12
    n_coil = n_pts - 2 * n_str

    # Straight horizontal segment from wall to coil start
    xs = np.linspace(x0, x0 + straight, n_str)

    # Helix: phase starts at π/2 so cos(t_start)=0 → z endpoint = z_c exactly
    t = np.linspace(np.pi / 2, np.pi / 2 + n_coils * 2 * np.pi, n_coil)
    xc = np.linspace(x0 + straight, x1 - straight, n_coil)
    yc = radius * np.sin(t)
    zc = radius * np.cos(t) + z_c

    # Straight horizontal segment from coil end to mass face
    xe = np.linspace(x1 - straight, x1, n_str)

    x_all = np.concatenate([xs, xc, xe])
    y_all = np.concatenate([np.zeros(n_str), yc, np.zeros(n_str)])
    z_all = np.concatenate([np.full(n_str, z_c), zc, np.full(n_str, z_c)])

    pts = np.column_stack([x_all, y_all, z_all])
    return pv.Spline(pts, n_pts).tube(radius=_SPRING_WIRE_R, n_sides=12)


class MassSpringDamperView(SimViewBase):
    """Mass-Spring-Damper LQR / custom-controller simulation window.

    Includes setpoint selection buttons (0 m, +1.5 m, −1.5 m) and keyboard
    shortcuts 1/2/3 to switch setpoints.

    Parameters
    ----------
    controller:
        Callable ``(x: ndarray) -> ndarray | float``.  When *None* (default)
        an LQR with setpoint tracking is designed automatically.
    m, c, k:
        Physical parameters (mass [kg], damping coefficient, spring constant).
    """

    _title = "Mass-Spring-Damper — Synapsys SimView"
    _mpl_title = "Telemetria — Mass-Spring-Damper"
    _dt = 0.01
    _hist_len = 600
    _mpl_skip = 5
    _pert_max_default = _PERT_MAX
    _slider_range = (1, 30)
    _slider_unit = "N"
    _splitter_w = (770, 630)
    _hud_pos = (12, 480)
    _cam_pos = ((0, -6, 0.4), (0, 0, 0.1), (0, 0, 1))
    _u_clip = 30.0
    _u_clip_total = 50.0
    _pert_btn_left = "◀  Empurrar"
    _pert_btn_right = "Empurrar  ▶"
    _push_colors = ("#1e3a5f", "#2563eb", "#1d4ed8", "#2563eb", "#60a5fa")

    def __init__(
        self,
        controller=None,
        m: float = _M,
        c: float = _C,
        k: float = _K,
        x0: np.ndarray | None = None,
        setpoints: list | None = None,
        save: str | None = None,
    ) -> None:
        super().__init__(controller, save=save)
        self._m, self._c, self._k = m, c, k
        self._x0_init = x0
        self._setpoints = setpoints if setpoints is not None else _DEFAULT_SETPOINTS
        self._setpoint: float = self._setpoints[0][1]
        self._sp_group: QButtonGroup | None = None

    # ── simulator ─────────────────────────────────────────────────────────────

    def _make_sim(self):
        return MassSpringDamperSim(m=self._m, c=self._c, k=self._k)

    def _x0(self):
        return self._x0_init.copy() if self._x0_init is not None else _X0.copy()

    def _equilibrium(self):
        return np.zeros(2)

    def _lqr_weights(self):
        return np.diag([20.0, 5.0]), np.eye(1)

    def _lqr_u(self, x):
        sp = self._setpoint
        x_err = x - np.array([sp, 0.0])
        return (-self._K @ x_err + self._k * sp).ravel()

    def _extra_hist_keys(self):
        return ["q", "qdot", "u"]

    def _append_hist(self, x, u):
        self._hist["q"].append(x[0])
        self._hist["qdot"].append(x[1])
        self._hist["u"].append(float(u[0]))

    # ── 3D scene ──────────────────────────────────────────────────────────────

    def _build_scene(self, pl):
        pl.add_mesh(
            pv.Box(bounds=(-3.5, 3.5, -0.5, 0.5, _FLOOR_Y - 0.06, _FLOOR_Y)),
            color=Dark.MESH_FLOOR,
            smooth_shading=True,
        )
        pl.add_mesh(
            pv.Box(bounds=(_WALL_X - 0.15, _WALL_X, -0.5, 0.5, _FLOOR_Y, 0.8)),
            color=Dark.MESH_WALL,
            smooth_shading=True,
        )
        pl.add_mesh(
            pv.Box(bounds=(-2.4, 2.4, -0.04, 0.04, _FLOOR_Y, _FLOOR_Y + 0.04)),
            color=Dark.MESH_RAIL,
            smooth_shading=True,
        )

        damp_a = pl.add_mesh(
            pv.Box(
                bounds=(
                    -_DAMP_W / 2,
                    _DAMP_W / 2,
                    -_DAMP_W / 2,
                    _DAMP_W / 2,
                    0.0,
                    _DAMP_H,
                )
            ),
            color=Dark.MESH_DAMP,
            smooth_shading=True,
            opacity=0.7,
        )

        spring_mesh = _spring_polydata(_WALL_X, 0.0)
        spring_a = pl.add_mesh(spring_mesh, color=Dark.MESH_SPRING, smooth_shading=True)

        mass_a = pl.add_mesh(
            pv.Box(
                bounds=(
                    -_MASS_W / 2,
                    _MASS_W / 2,
                    -_MASS_D / 2,
                    _MASS_D / 2,
                    _FLOOR_Y,
                    _FLOOR_Y + _MASS_H,
                )
            ),
            color=Dark.MESH_BODY,
            smooth_shading=True,
        )

        setpt_a = pl.add_mesh(
            pv.Box(
                bounds=(
                    -0.015,
                    0.015,
                    -0.3,
                    0.3,
                    _FLOOR_Y - 0.02,
                    _FLOOR_Y + _MASS_H + 0.1,
                )
            ),
            color=Dark.MESH_REF,
            opacity=0.6,
        )

        pl.add_text(
            "A/D=força  1/2/3=setpoint  R=reset  SPACE=pausa  Q=fechar",
            position=(12, 12),
            font_size=8,
            color=Dark.MUTED,
        )

        return {
            "mass": mass_a,
            "damp": damp_a,
            "spring": spring_a,
            "spring_mesh": spring_mesh,
            "setpt": setpt_a,
        }

    def _update_scene(self, actors, x, u):
        q = x[0]
        sp = self._setpoint

        t_m = vtk.vtkTransform()
        t_m.Translate(q, 0, 0)
        actors["mass"].SetUserTransform(t_m)

        t_d = vtk.vtkTransform()
        t_d.Translate(q - _MASS_W / 2 - _DAMP_W / 2 - 0.04, 0, _FLOOR_Y)
        actors["damp"].SetUserTransform(t_d)

        t_sp = vtk.vtkTransform()
        t_sp.Translate(sp, 0, 0)
        actors["setpt"].SetUserTransform(t_sp)

        new_s = _spring_polydata(_WALL_X, q)
        actors["spring_mesh"].points = new_s.points
        actors["spring_mesh"].lines = new_s.lines

    # ── extra controls: setpoint buttons ─────────────────────────────────────

    def _build_extra_controls(self, hb: QHBoxLayout) -> None:
        sp_lbl = QLabel("Setpoint:")
        sp_lbl.setStyleSheet(f"color:{Dark.MUTED}; font-size:10px;")
        hb.addWidget(sp_lbl)

        _SP = f"""
            QPushButton {{
                background:{Dark.BG}; color:{Dark.FG}; border:1px solid {Dark.BORDER};
                border-radius:5px; padding:6px 12px; font-size:11px;
            }}
            QPushButton:checked {{
                background:#14532d; border-color:#16a34a; color:#4ade80;
            }}
            QPushButton:hover   {{ background:#1e293b; }}
        """
        self._sp_group = QButtonGroup(self)
        self._sp_group.setExclusive(True)
        for label, val in self._setpoints:
            b = QPushButton(label)
            b.setCheckable(True)
            b.setStyleSheet(_SP)
            b.clicked.connect(lambda _, v=val: self._set_setpoint(v))
            self._sp_group.addButton(b)
            hb.addWidget(b)
        self._sp_group.buttons()[0].setChecked(True)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{Dark.BORDER};")
        hb.addWidget(sep)

    def _set_setpoint(self, value: float) -> None:
        self._setpoint = value

    def handle_key_press(self, key: int) -> None:
        super().handle_key_press(key)
        _keys = [Qt.Key_1, Qt.Key_2, Qt.Key_3]
        for i, k in enumerate(_keys):
            if key == k and i < len(self._setpoints):
                self._set_setpoint(self._setpoints[i][1])
                self._sp_group.buttons()[i].setChecked(True)
                break

    def _on_reset(self) -> None:
        self._setpoint = self._setpoints[0][1]
        if self._sp_group is not None:
            self._sp_group.buttons()[0].setChecked(True)

    # ── matplotlib panels ─────────────────────────────────────────────────────

    def _make_mpl(self, fig, gs):
        def _ax(row):
            return _styled_ax(fig.add_subplot(gs[row]))

        ax_q = _ax(0)
        ax_v = _ax(1)
        ax_u = _ax(2)
        ax_ph = _ax(3)

        ax_q.set_title("Posição q(t)", color=Dark.FG, fontsize=9, pad=3)
        ax_q.set_ylabel("m", color=Dark.MUTED, fontsize=8)
        (sp_l,) = ax_q.plot([], [], "--", color=Dark.SIG_REF_DK, lw=1.0, label="sp")
        (q_l,) = ax_q.plot([], [], color=Dark.SIG_POS, lw=1.5, label="q")
        ax_q.legend(
            fontsize=7, facecolor=Dark.SURFACE, edgecolor=Dark.GRID, labelcolor=Dark.FG
        )

        ax_v.set_title("Velocidade q̇(t)", color=Dark.FG, fontsize=9, pad=3)
        ax_v.set_ylabel("m/s", color=Dark.MUTED, fontsize=8)
        (v_l,) = ax_v.plot([], [], color=Dark.SIG_VEL, lw=1.5)

        ax_u.set_title("Força de controle u(t)", color=Dark.FG, fontsize=9, pad=3)
        ax_u.set_xlabel("t (s)", color=Dark.MUTED, fontsize=8)
        ax_u.set_ylabel("N", color=Dark.MUTED, fontsize=8)
        ax_u.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        (u_l,) = ax_u.plot([], [], color=Dark.SIG_CTRL, lw=1.5)

        ax_ph.set_title("Retrato de fase", color=Dark.FG, fontsize=9, pad=3)
        ax_ph.set_xlabel("q (m)", color=Dark.MUTED, fontsize=8)
        ax_ph.set_ylabel("q̇ (m/s)", color=Dark.MUTED, fontsize=8)
        ax_ph.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        ax_ph.axvline(0, color=Dark.GRID, lw=0.7, ls=":")
        (ph_l,) = ax_ph.plot([], [], color=Dark.SIG_PHASE, lw=1.0, alpha=0.8)
        (ph_dot,) = ax_ph.plot([], [], "o", color=Dark.SIG_CYAN, ms=5, zorder=5)

        axes = {"q": ax_q, "v": ax_v, "u": ax_u, "ph": ax_ph}
        lines = {"sp": sp_l, "q": q_l, "v": v_l, "u": u_l, "ph": ph_l, "ph_dot": ph_dot}
        return axes, lines

    def _refresh_mpl(self, axes, lines):
        t = list(self._hist["t"])
        q = list(self._hist["q"])
        v = list(self._hist["qdot"])
        u = list(self._hist["u"])
        sp = [self._setpoint] * len(t)

        lines["sp"].set_data(t, sp)
        lines["q"].set_data(t, q)
        lines["v"].set_data(t, v)
        lines["u"].set_data(t, u)
        lines["ph"].set_data(q, v)
        lines["ph_dot"].set_data([q[-1]], [v[-1]])

        for ax in axes.values():
            ax.relim()
            ax.autoscale_view()

    # ── HUD / status ──────────────────────────────────────────────────────────

    def _trail_point(self, x):
        # mass position along the horizontal axis
        return np.array([x[0], 0.0, _MASS_H / 2])

    def _hud_text(self, x, u):
        q = x[0]
        sp = self._setpoint
        pert_s = f"{self._pert:+5.0f} N" if abs(self._pert) > 0.5 else "  --"
        return (
            f"  posição  : {q:+6.3f} m\n"
            f"  vel.     : {x[1]:+6.3f} m/s\n"
            f"  setpoint : {sp:+6.3f} m\n"
            f"  erro     : {(q - sp):+6.3f} m\n"
            f"  força    : {float(u[0]):+6.1f} N\n"
            f"  pert.    : {pert_s}\n"
            f"  ctrl     : {self._ctrl_label}"
        )

    def _status_text(self, x):
        q = x[0]
        sp = self._setpoint
        return (
            f"  t = {self._t:.2f} s  |  q = {q:+.3f} m  |  "
            f"erro = {(q - sp):+.3f} m  |  "
            f"{'PAUSADO' if self._paused else 'rodando'}"
        )

    def _info_text(self):
        fn = getattr(self._sim, "natural_frequency", lambda: "?")()
        dr = getattr(self._sim, "damping_ratio", lambda: "?")()
        fn_s = f"{fn:.2f}" if isinstance(fn, float) else str(fn)
        dr_s = f"{dr:.3f}" if isinstance(dr, float) else str(dr)
        return (
            f"  m={self._m} kg  c={self._c}  k={self._k}  |  ωₙ={fn_s} rad/s  ζ={dr_s}"
        )
