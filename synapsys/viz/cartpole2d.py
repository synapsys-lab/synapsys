"""CartPole2DView — lightweight 2-D matplotlib animation for CartPoleSim."""

from __future__ import annotations

from typing import Callable

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from numpy import ndarray

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import CartPoleSim

_DEFAULT_X0 = np.array([0.0, 0.0, 0.15, 0.0])
_DEFAULT_Q = np.diag([1.0, 0.1, 100.0, 10.0])
_DEFAULT_R = np.eye(1) * 0.01
_U_CLIP = 50.0


class CartPole2DView:
    """2D matplotlib animation of CartPoleSim with pluggable controller.

    Parameters
    ----------
    sim:
        CartPoleSim instance.  A default one is created if not supplied.
    controller:
        Callable ``(x: ndarray) -> ndarray`` returning the control force.
        If *None*, an LQR gain is designed automatically.
    dt:
        Integration / animation step (seconds).
    duration:
        Total simulation time (seconds).
    x0:
        Initial state ``[p, ṗ, θ, θ̇]``.  Defaults to ``[0, 0, 0.15, 0]``.

    Usage::

        CartPole2DView().simulate()          # run and return history dict
        CartPole2DView().animate()           # build animation object
        CartPole2DView().run()               # simulate → animate → plt.show()
    """

    def __init__(
        self,
        sim: CartPoleSim | None = None,
        controller: Callable | None = None,
        dt: float = 0.02,
        duration: float = 10.0,
        x0: ndarray | None = None,
    ) -> None:
        self._sim = sim if sim is not None else CartPoleSim()
        self.controller = controller
        self.dt = float(dt)
        self.duration = float(duration)
        self.x0 = np.array(x0 if x0 is not None else _DEFAULT_X0, dtype=float)
        self.history: dict | None = None

        if controller is None:
            self._sim.reset()
            ss = self._sim.linearize(np.zeros(4), np.zeros(1))
            K, _ = lqr(ss.A, ss.B, _DEFAULT_Q, _DEFAULT_R)
            self._K = K
        else:
            self._K = None

    def _control(self, x: ndarray) -> ndarray:
        if self.controller is not None:
            return np.asarray(self.controller(x), dtype=float).ravel()
        return np.clip(-self._K @ x, -_U_CLIP, _U_CLIP).ravel()

    # ── public API ────────────────────────────────────────────────────────────

    def simulate(self) -> dict:
        """Run the simulation and return a history dict.

        Returns
        -------
        dict with keys ``t``, ``pos``, ``angle``, ``force``, ``states``.
        All values are 1-D arrays of length ``steps = int(duration / dt)``.
        """
        steps = int(self.duration / self.dt)
        self._sim.reset(x0=self.x0)

        t_arr = np.empty(steps)
        pos_arr = np.empty(steps)
        angle_arr = np.empty(steps)
        force_arr = np.empty(steps)
        states = np.empty((steps, 4))

        for i in range(steps):
            x = self._sim.state
            u = self._control(x)
            self._sim.step(u, self.dt)
            t_arr[i] = i * self.dt
            pos_arr[i] = x[0]
            angle_arr[i] = x[2]
            force_arr[i] = u[0]
            states[i] = x

        self.history = {
            "t": t_arr,
            "pos": pos_arr,
            "angle": angle_arr,
            "force": force_arr,
            "states": states,
        }
        return self.history

    def animate(self, save: str | None = None) -> FuncAnimation:
        """Build and return a :class:`~matplotlib.animation.FuncAnimation`.

        Parameters
        ----------
        save:
            If given, save the animation to this path (e.g. ``"out.gif"``).
            Requires *Pillow* for GIFs or *ffmpeg* for MP4.

        Returns the ``FuncAnimation`` object (call ``plt.show()`` separately
        or use :meth:`run` for an all-in-one entry point).
        """
        if self.history is None:
            self.simulate()

        hist = self.history
        states = hist["states"]
        t_arr = hist["t"]
        l = self._sim._l  # pole length

        fig, ax = plt.subplots(figsize=(9, 4))
        ax.set_xlim(-3, 3)
        ax.set_ylim(-0.3, 1.2)
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.3)
        ax.axhline(0, color="k", lw=1)
        ax.set_title("Cart-Pole Animation")

        cart_w, cart_h = 0.4, 0.15
        cart_patch = patches.FancyBboxPatch(
            (-cart_w / 2, -cart_h / 2),
            cart_w,
            cart_h,
            boxstyle="round,pad=0.02",
            fc="#2563eb",
            ec="white",
            lw=1.5,
        )
        ax.add_patch(cart_patch)
        (pole_line,) = ax.plot([], [], "o-", color="#c8a870", lw=3, ms=10)
        time_text = ax.text(0.02, 0.92, "", transform=ax.transAxes, fontsize=10)

        def _update(frame):
            p, theta = states[frame, 0], states[frame, 2]
            cart_patch.set_x(p - cart_w / 2)
            tip_x = p + l * np.sin(theta)
            tip_y = l * np.cos(theta)
            pole_line.set_data([p, tip_x], [0, tip_y])
            time_text.set_text(
                f"t = {t_arr[frame]:.2f} s   θ = {np.degrees(theta):.1f}°"
            )
            return cart_patch, pole_line, time_text

        anim = FuncAnimation(
            fig, _update, frames=len(states), interval=self.dt * 1000, blit=True
        )

        if save is not None:
            anim.save(save)

        return anim

    def run(self) -> None:
        """Simulate, build animation, and call ``plt.show()``."""
        self.simulate()
        self.animate()
        plt.show()
