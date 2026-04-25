"""CartPoleView — ready-to-run Cart-Pole simulation with pluggable controller.

Usage::

    from synapsys.viz import CartPoleView
    CartPoleView().run()                                   # auto-LQR
    CartPoleView(controller=lambda x: np.clip(-K@x,-50,50)).run()
"""

from __future__ import annotations

import numpy as np
import pyvista as pv
import vtk

from synapsys.simulators import CartPoleSim
from synapsys.viz.palette import Dark

from ._base import SimViewBase, _styled_ax

# ── physical parameters ───────────────────────────────────────────────────────
_M_C, _M_P, _L, _G = 1.0, 0.1, 0.5, 9.81
_X0 = np.array([0.0, 0.0, 0.18, 0.0])

# ── cart color thresholds (fraction of _TRACK_HW) ────────────────────────────
_WARN_FRAC = 0.72  # amber warning
_LIMIT_FRAC = 0.92  # auto-reset


def _hex_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


_CART_RGB_NORMAL = _hex_rgb(Dark.MESH_BODY)
_CART_RGB_WARN = _hex_rgb(Dark.WARN)
_CART_RGB_LIMIT = _hex_rgb(Dark.DANGER)

# ── geometry ──────────────────────────────────────────────────────────────────
_CART_W, _CART_D, _CART_H = 0.40, 0.28, 0.12
_POLE_R = 0.022
_TRACK_HW = 3.5
_PIVOT_Z = _CART_H + 0.01


def _vtk_t(
    tx: float, ty: float, tz: float, ry_deg: float = 0.0, tz2: float = 0.0
) -> vtk.vtkTransform:
    t = vtk.vtkTransform()
    t.Translate(tx, ty, tz)
    t.RotateY(ry_deg)
    t.Translate(0.0, 0.0, tz2)
    return t


class CartPoleView(SimViewBase):
    """Cart-Pole LQR / custom-controller simulation window.

    Parameters
    ----------
    controller:
        Callable ``(x: ndarray) -> ndarray | float`` that maps state to
        control input.  When *None* (default) an LQR is designed automatically.
    m_c, m_p, l, g:
        Physical parameters.  Defaults match the standard cart-pole textbook.
    """

    _title = "Cart-Pole — Synapsys SimView"
    _mpl_title = "Telemetria — Cart-Pole"
    _dt = 0.02
    _hist_len = 500
    _mpl_skip = 3
    _pert_max_default = 30.0
    _slider_range = (1, 80)
    _slider_unit = "N"
    _splitter_w = (770, 630)
    _hud_pos = (12, 560)
    _cam_pos = ((0, -5.5, 1.2), (0, 0, 0.4), (0, 0, 1))
    _u_clip = 50.0
    _u_clip_total = 80.0
    _pert_btn_left = "◀  Empurrar carrinho"
    _pert_btn_right = "Empurrar carrinho  ▶"
    _push_colors = ("#1e3a5f", "#2563eb", "#1d4ed8", "#2563eb", "#60a5fa")

    def __init__(
        self,
        controller=None,
        m_c: float = _M_C,
        m_p: float = _M_P,
        l: float = _L,
        g: float = _G,
        x0: np.ndarray | None = None,
        save: str | None = None,
    ) -> None:
        super().__init__(controller, save=save)
        self._m_c, self._m_p, self._l, self._g = m_c, m_p, l, g
        self._x0_init = x0

    # ── simulator ─────────────────────────────────────────────────────────────

    def _make_sim(self):
        return CartPoleSim(m_c=self._m_c, m_p=self._m_p, l=self._l, g=self._g)

    def _x0(self):
        return self._x0_init.copy() if self._x0_init is not None else _X0.copy()

    def _equilibrium(self):
        return np.zeros(4)

    def _lqr_weights(self):
        return np.diag([1.0, 0.1, 100.0, 10.0]), 0.01 * np.eye(1)

    def _extra_hist_keys(self):
        return ["pos", "vel", "ang", "angv", "u"]

    def _append_hist(self, x, u):
        self._hist["pos"].append(x[0])
        self._hist["vel"].append(x[1])
        self._hist["ang"].append(np.degrees(x[2]))
        self._hist["angv"].append(np.degrees(x[3]))
        self._hist["u"].append(float(u[0]))

    # ── 3D scene ──────────────────────────────────────────────────────────────

    def _build_scene(self, pl):
        pl.add_mesh(
            pv.Box(bounds=(-_TRACK_HW - 0.5, _TRACK_HW + 0.5, -0.8, 0.8, -0.06, 0.0)),
            color=Dark.MESH_FLOOR,
            smooth_shading=True,
        )
        pl.add_mesh(
            pv.Box(bounds=(-_TRACK_HW, _TRACK_HW, -0.04, 0.04, 0.0, 0.04)),
            color=Dark.MESH_RAIL,
            smooth_shading=True,
        )
        for sign in (-1, 1):
            pl.add_mesh(
                pv.Box(
                    bounds=(
                        sign * _TRACK_HW - 0.04,
                        sign * _TRACK_HW + 0.04,
                        -0.1,
                        0.1,
                        0.0,
                        0.15,
                    )
                ),
                color=Dark.MESH_STOP,
                smooth_shading=True,
            )

        wheel_actors = []
        for wx, wy in [(-0.14, -0.10), (-0.14, 0.10), (0.14, -0.10), (0.14, 0.10)]:
            wa = pl.add_mesh(
                pv.Sphere(radius=0.045, center=(wx, wy, 0.04)),
                color=Dark.MESH_STRUCT,
                smooth_shading=True,
            )
            wheel_actors.append((wa, wx, wy))

        cart_a = pl.add_mesh(
            pv.Box(
                bounds=(
                    -_CART_W / 2,
                    _CART_W / 2,
                    -_CART_D / 2,
                    _CART_D / 2,
                    0.0,
                    _CART_H,
                )
            ),
            color=Dark.MESH_BODY,
            smooth_shading=True,
        )
        pivot_a = pl.add_mesh(
            pv.Sphere(radius=_POLE_R * 2.2, center=(0, 0, 0)),
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
            pv.Sphere(radius=_POLE_R * 2.8, center=(0, 0, 0)),
            color=Dark.MESH_BOB,
            smooth_shading=True,
        )

        pl.add_text(
            "A/D=força  R=reset  SPACE=pausa  Q=fechar",
            position=(12, 12),
            font_size=8,
            color=Dark.MUTED,
        )

        return {
            "cart": cart_a,
            "pivot": pivot_a,
            "pole": pole_a,
            "bob": bob_a,
            "wheels": wheel_actors,
        }

    def _update_scene(self, actors, x, u):
        cx = x[0]
        theta = x[2]
        thetad = np.degrees(theta)
        pole_l = self._l

        actors["cart"].SetUserTransform(_vtk_t(cx, 0, 0))
        actors["pivot"].SetUserTransform(_vtk_t(cx, 0, _PIVOT_Z))
        actors["pole"].SetUserTransform(_vtk_t(cx, 0, _PIVOT_Z, thetad, pole_l / 2))
        actors["bob"].SetUserTransform(
            _vtk_t(cx + pole_l * np.sin(theta), 0, _PIVOT_Z + pole_l * np.cos(theta))
        )
        for wa, wx, wy in actors["wheels"]:
            wa.SetUserTransform(_vtk_t(cx + wx, wy, 0))

        frac = abs(cx) / _TRACK_HW
        if frac >= _LIMIT_FRAC:
            rgb = _CART_RGB_LIMIT
        elif frac >= _WARN_FRAC:
            rgb = _CART_RGB_WARN
        else:
            rgb = _CART_RGB_NORMAL
        actors["cart"].GetProperty().SetColor(*rgb)

    # ── matplotlib panels ─────────────────────────────────────────────────────

    def _make_mpl(self, fig, gs):
        def _ax(row):
            return _styled_ax(fig.add_subplot(gs[row]))

        ax_pos = _ax(0)
        ax_ang = _ax(1)
        ax_u = _ax(2)
        ax_ph = _ax(3)

        # Panel 1: position (left) + cart velocity (right twinx)
        ax_pos.set_title(
            "Posição / Velocidade do carrinho", color=Dark.FG, fontsize=9, pad=3
        )
        ax_pos.set_ylabel("pos (m)", color=Dark.SIG_POS, fontsize=8)
        ax_pos.tick_params(axis="y", colors=Dark.SIG_POS, labelsize=7)
        ax_pos.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        (pos_l,) = ax_pos.plot([], [], color=Dark.SIG_POS, lw=1.5, label="pos")

        ax_vel = ax_pos.twinx()
        ax_vel.set_facecolor("none")
        ax_vel.set_ylabel("vel (m/s)", color=Dark.SIG_VEL, fontsize=8)
        ax_vel.tick_params(axis="y", colors=Dark.SIG_VEL, labelsize=7)
        ax_vel.spines["right"].set_edgecolor(Dark.SIG_VEL)
        ax_vel.spines["left"].set_edgecolor(Dark.BORDER)
        ax_vel.spines["top"].set_visible(False)
        ax_vel.spines["bottom"].set_edgecolor(Dark.BORDER)
        (vel_l,) = ax_vel.plot(
            [], [], color=Dark.SIG_VEL, lw=1.2, alpha=0.85, ls="--", label="vel"
        )

        ax_ang.set_title("Ângulo da haste θ", color=Dark.FG, fontsize=9, pad=3)
        ax_ang.set_ylabel("graus", color=Dark.MUTED, fontsize=8)
        ax_ang.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        (ang_l,) = ax_ang.plot([], [], color=Dark.SIG_ANG, lw=1.5)

        ax_u.set_title("Força de controle", color=Dark.FG, fontsize=9, pad=3)
        ax_u.set_xlabel("t (s)", color=Dark.MUTED, fontsize=8)
        ax_u.set_ylabel("N", color=Dark.MUTED, fontsize=8)
        ax_u.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        (u_l,) = ax_u.plot([], [], color=Dark.SIG_CTRL, lw=1.5)

        ax_ph.set_title("Retrato de fase  (θ, θ̇)", color=Dark.FG, fontsize=9, pad=3)
        ax_ph.set_xlabel("θ (graus)", color=Dark.MUTED, fontsize=8)
        ax_ph.set_ylabel("θ̇ (°/s)", color=Dark.MUTED, fontsize=8)
        ax_ph.axhline(0, color=Dark.GRID, lw=0.7, ls=":")
        ax_ph.axvline(0, color=Dark.GRID, lw=0.7, ls=":")
        (ph_l,) = ax_ph.plot([], [], color=Dark.SIG_PHASE, lw=1.0, alpha=0.8)
        (ph_dot,) = ax_ph.plot([], [], "o", color=Dark.SIG_CYAN, ms=5, zorder=5)

        axes = {"pos": ax_pos, "vel_ax": ax_vel, "ang": ax_ang, "u": ax_u, "ph": ax_ph}
        lines = {
            "pos": pos_l,
            "vel": vel_l,
            "ang": ang_l,
            "u": u_l,
            "ph": ph_l,
            "ph_dot": ph_dot,
        }
        return axes, lines

    def _refresh_mpl(self, axes, lines):
        t = list(self._hist["t"])
        pos = list(self._hist["pos"])
        vel = list(self._hist["vel"])
        ang = list(self._hist["ang"])
        angv = list(self._hist["angv"])
        u = list(self._hist["u"])

        lines["pos"].set_data(t, pos)
        lines["vel"].set_data(t, vel)
        lines["ang"].set_data(t, ang)
        lines["u"].set_data(t, u)
        lines["ph"].set_data(ang, angv)
        lines["ph_dot"].set_data([ang[-1]], [angv[-1]])

        for ax in axes.values():
            ax.relim()
            ax.autoscale_view()

    # ── HUD / status ──────────────────────────────────────────────────────────

    def _trail_point(self, x):
        # pole tip in world XZ plane (Y=0 for 2D cart-pole)
        p, _, theta, _ = x
        tip_x = p + self._l * np.sin(theta)
        tip_z = _PIVOT_Z + self._l * np.cos(theta)
        return np.array([tip_x, 0.0, tip_z])

    def _post_tick(self, x, u):
        if abs(x[0]) >= _TRACK_HW * _LIMIT_FRAC:
            self._reset_sim()

    def _hud_text(self, x, u):
        pert_s = f"{self._pert:+5.0f} N" if abs(self._pert) > 0.5 else "  --"
        frac = abs(x[0]) / _TRACK_HW
        limit_s = "  ⚠ LIMITE" if frac >= _WARN_FRAC else ""
        return (
            f"  cart pos : {x[0]:+6.3f} m{limit_s}\n"
            f"  cart vel : {x[1]:+6.3f} m/s\n"
            f"  ângulo   : {np.degrees(x[2]):+6.2f}°\n"
            f"  vel. ang.: {np.degrees(x[3]):+6.1f} °/s\n"
            f"  força    : {float(u[0]):+6.1f} N\n"
            f"  pert.    : {pert_s}\n"
            f"  ctrl     : {self._ctrl_label}"
        )

    def _status_text(self, x):
        return (
            f"  t = {self._t:.2f} s  |  pos = {x[0]:+.3f} m  |  "
            f"θ = {np.degrees(x[2]):+.2f}°  |  "
            f"{'PAUSADO' if self._paused else 'rodando'}"
        )

    def _info_text(self):
        return (
            f"  m_c={self._m_c} kg  m_p={self._m_p} kg  l={self._l} m  g={self._g} m/s²"
        )
