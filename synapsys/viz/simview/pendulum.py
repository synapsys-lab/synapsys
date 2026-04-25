"""PendulumView — ready-to-run Inverted Pendulum simulation with pluggable controller.

Usage::

    from synapsys.viz import PendulumView
    PendulumView().run()
    PendulumView(controller=lambda x: np.clip(-K@x, -30, 30)).run()
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
import vtk

from synapsys.simulators import InvertedPendulumSim
from synapsys.viz.palette import Dark

from ._base import SimViewBase, _styled_ax

# ── physical parameters ───────────────────────────────────────────────────────
_M, _L, _G, _B = 1.0, 1.0, 9.81, 0.1
_X0 = np.array([0.18, 0.0])
_PERT_MAX = 20.0

# ── geometry ──────────────────────────────────────────────────────────────────
_PIVOT_Z = 0.12
_POLE_R = 0.028


def _vtk_t(
    tx: float, ty: float, tz: float, ry_deg: float = 0.0, tz2: float = 0.0
) -> vtk.vtkTransform:
    t = vtk.vtkTransform()
    t.Translate(tx, ty, tz)
    t.RotateY(ry_deg)
    t.Translate(0.0, 0.0, tz2)
    return t


class PendulumView(SimViewBase):
    """Inverted Pendulum LQR / custom-controller simulation window.

    Parameters
    ----------
    controller:
        Callable ``(x: ndarray) -> ndarray | float``.  When *None* (default)
        an LQR is designed automatically from the linearized model.
    m, l, g, b:
        Physical parameters (mass [kg], length [m], gravity, damping).
    """

    _title = "Pêndulo Invertido — Synapsys SimView"
    _mpl_title = "Telemetria — Pêndulo Invertido"
    _dt = 0.01
    _hist_len = 600
    _mpl_skip = 5
    _pert_max_default = _PERT_MAX
    _slider_range = (1, 40)
    _slider_unit = "N·m"
    _splitter_w = (770, 630)
    _hud_pos = (12, 510)
    _cam_pos = ((2.5, -4.5, 1.0), (0, 0, 0.6), (0, 0, 1))
    _u_clip = 30.0
    _u_clip_total = 50.0
    _pert_btn_left = "↺  Torque esq."
    _pert_btn_right = "Torque dir.  ↻"
    _push_colors = ("#3b1f0a", "#ea580c", "#c2410c", "#ea580c", "#fb923c")

    def __init__(
        self,
        controller=None,
        m: float = _M,
        l: float = _L,
        g: float = _G,
        b: float = _B,
        x0: np.ndarray | None = None,
        save: str | None = None,
    ) -> None:
        super().__init__(controller, save=save)
        self._m, self._l, self._g, self._b = m, l, g, b
        self._x0_init = x0

    # ── simulator ─────────────────────────────────────────────────────────────

    def _make_sim(self):
        return InvertedPendulumSim(m=self._m, l=self._l, g=self._g, b=self._b)

    def _x0(self):
        return self._x0_init.copy() if self._x0_init is not None else _X0.copy()

    def _equilibrium(self):
        return np.zeros(2)

    def _lqr_weights(self):
        return np.diag([80.0, 5.0]), np.eye(1)

    def _extra_hist_keys(self):
        return ["ang", "angv", "tau"]

    def _append_hist(self, x, u):
        self._hist["ang"].append(np.degrees(x[0]))
        self._hist["angv"].append(np.degrees(x[1]))
        self._hist["tau"].append(float(u[0]))

    # ── 3D scene ──────────────────────────────────────────────────────────────

    def _build_scene(self, pl):
        pl.add_mesh(
            pv.Box(bounds=(-1.2, 1.2, -1.2, 1.2, -0.06, 0.0)),
            color=Dark.MESH_FLOOR,
            smooth_shading=True,
        )
        pl.add_mesh(
            pv.Cylinder(
                center=(0, 0, 0.04),
                direction=(0, 0, 1),
                height=0.08,
                radius=0.22,
                resolution=32,
            ),
            color=Dark.MESH_STRUCT,
            smooth_shading=True,
        )
        pl.add_mesh(
            pv.Sphere(radius=0.055, center=(0, 0, _PIVOT_Z)),
            color=Dark.MESH_DAMP,
            smooth_shading=True,
        )

        pole_a = pl.add_mesh(
            pv.Cylinder(
                center=(0, 0, 0),
                direction=(0, 0, 1),
                height=self._l,
                radius=_POLE_R,
                resolution=20,
            ),
            color=Dark.MESH_POLE,
            smooth_shading=True,
        )
        bob_a = pl.add_mesh(
            pv.Sphere(radius=_POLE_R * 3.0, center=(0, 0, 0)),
            color=Dark.MESH_BOB,
            smooth_shading=True,
        )

        pl.add_mesh(
            pv.Line((0, 0, _PIVOT_Z), (0, 0, _PIVOT_Z + self._l + 0.1)),
            color=Dark.SIG_REF_DK,
            opacity=0.25,
            line_width=1,
        )

        arr_r = pl.add_mesh(
            pv.Arrow(
                start=(0, 0, 0),
                direction=(1, 0, 0),
                scale=0.45,
                tip_length=0.3,
                shaft_radius=0.05,
            ),
            color=Dark.DANGER,
            opacity=0.0,
        )
        arr_l = pl.add_mesh(
            pv.Arrow(
                start=(0, 0, 0),
                direction=(-1, 0, 0),
                scale=0.45,
                tip_length=0.3,
                shaft_radius=0.05,
            ),
            color=Dark.DANGER,
            opacity=0.0,
        )

        pl.add_text(
            "A/D=torque  R=reset  SPACE=pausa  Q=fechar",
            position=(12, 12),
            font_size=8,
            color=Dark.MUTED,
        )

        return {"pole": pole_a, "bob": bob_a, "arr_r": arr_r, "arr_l": arr_l}

    def _update_scene(self, actors, x, u):
        theta = x[0]
        thetad = np.degrees(theta)
        pl = self._l
        tip_x = pl * np.sin(theta)
        tip_z = _PIVOT_Z + pl * np.cos(theta)

        actors["pole"].SetUserTransform(_vtk_t(0, 0, _PIVOT_Z, thetad, pl / 2))
        actors["bob"].SetUserTransform(_vtk_t(tip_x, 0, tip_z))

        if abs(self._pert) > 0.5:
            actors["bob"].GetProperty().SetColor(0.94, 0.27, 0.27)
        else:
            actors["bob"].GetProperty().SetColor(0.97, 0.57, 0.07)

        if self._pert > 0.5:
            ta = vtk.vtkTransform()
            ta.Translate(tip_x - 0.1, 0, tip_z)
            actors["arr_r"].SetUserTransform(ta)
            actors["arr_r"].GetProperty().SetOpacity(min(self._pert / _PERT_MAX, 1.0))
            actors["arr_l"].GetProperty().SetOpacity(0.0)
        elif self._pert < -0.5:
            ta = vtk.vtkTransform()
            ta.Translate(tip_x + 0.1, 0, tip_z)
            actors["arr_l"].SetUserTransform(ta)
            actors["arr_l"].GetProperty().SetOpacity(min(-self._pert / _PERT_MAX, 1.0))
            actors["arr_r"].GetProperty().SetOpacity(0.0)
        else:
            actors["arr_r"].GetProperty().SetOpacity(0.0)
            actors["arr_l"].GetProperty().SetOpacity(0.0)

    # ── matplotlib panels ─────────────────────────────────────────────────────

    def _make_mpl(self, fig, gs):
        def _ax(row):
            return _styled_ax(fig.add_subplot(gs[row]))

        ax_ang = _ax(0)
        ax_angv = _ax(1)
        ax_tau = _ax(2)
        ax_ph = _ax(3)

        ax_ang.set_title("Ângulo θ(t)", color=Dark.FG, fontsize=9, pad=3)
        ax_ang.set_ylabel("graus", color=Dark.MUTED, fontsize=8)
        ax_ang.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        (ang_l,) = ax_ang.plot([], [], color=Dark.SIG_POS, lw=1.5)

        ax_angv.set_title("Velocidade angular θ̇(t)", color=Dark.FG, fontsize=9, pad=3)
        ax_angv.set_ylabel("°/s", color=Dark.MUTED, fontsize=8)
        ax_angv.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        (angv_l,) = ax_angv.plot([], [], color=Dark.SIG_VEL, lw=1.5)

        ax_tau.set_title("Torque de controle τ(t)", color=Dark.FG, fontsize=9, pad=3)
        ax_tau.set_xlabel("t (s)", color=Dark.MUTED, fontsize=8)
        ax_tau.set_ylabel("N·m", color=Dark.MUTED, fontsize=8)
        ax_tau.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        (tau_l,) = ax_tau.plot([], [], color=Dark.SIG_CTRL, lw=1.5)

        ax_ph.set_title("Retrato de fase  (θ, θ̇)", color=Dark.FG, fontsize=9, pad=3)
        ax_ph.set_xlabel("θ (graus)", color=Dark.MUTED, fontsize=8)
        ax_ph.set_ylabel("θ̇ (°/s)", color=Dark.MUTED, fontsize=8)
        ax_ph.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        ax_ph.axvline(0, color=Dark.GRID, lw=0.7, ls=":")
        (ph_l,) = ax_ph.plot([], [], color=Dark.SIG_PHASE, lw=1.0, alpha=0.8)
        (ph_dot,) = ax_ph.plot([], [], "o", color=Dark.SIG_CYAN, ms=5, zorder=5)

        axes = {"ang": ax_ang, "angv": ax_angv, "tau": ax_tau, "ph": ax_ph}
        lines = {
            "ang": ang_l,
            "angv": angv_l,
            "tau": tau_l,
            "ph": ph_l,
            "ph_dot": ph_dot,
        }
        return axes, lines

    def _refresh_mpl(self, axes, lines):
        t = list(self._hist["t"])
        ang = list(self._hist["ang"])
        angv = list(self._hist["angv"])
        tau = list(self._hist["tau"])

        lines["ang"].set_data(t, ang)
        lines["angv"].set_data(t, angv)
        lines["tau"].set_data(t, tau)
        lines["ph"].set_data(ang, angv)
        lines["ph_dot"].set_data([ang[-1]], [angv[-1]])

        for ax in axes.values():
            ax.relim()
            ax.autoscale_view()

    # ── HUD / status ──────────────────────────────────────────────────────────

    def _trail_point(self, x):
        theta = x[0]
        tip_x = self._l * np.sin(theta)
        tip_z = _PIVOT_Z + self._l * np.cos(theta)
        return np.array([tip_x, 0.0, tip_z])

    def _hud_text(self, x, u):
        pert_s = f"{self._pert:+6.1f} N·m" if abs(self._pert) > 0.5 else "   --"
        return (
            f"  ângulo   : {np.degrees(x[0]):+6.2f}°\n"
            f"  vel. ang.: {np.degrees(x[1]):+6.1f} °/s\n"
            f"  torque   : {float(u[0]):+6.2f} N·m\n"
            f"  pert.    : {pert_s}\n"
            f"  ctrl     : {self._ctrl_label}"
        )

    def _status_text(self, x):
        return (
            f"  t = {self._t:.2f} s  |  θ = {np.degrees(x[0]):+.2f}°  |  "
            f"θ̇ = {np.degrees(x[1]):+.1f} °/s  |  "
            f"{'PAUSADO' if self._paused else 'rodando'}"
        )

    def _info_text(self):
        pole = getattr(self._sim, "unstable_pole", lambda: "?")()
        pole_s = f"{pole:.3f}" if isinstance(pole, float) else str(pole)
        return (
            f"  m={self._m} kg  l={self._l} m  b={self._b}  |  λ_inst = +{pole_s} rad/s"
        )
