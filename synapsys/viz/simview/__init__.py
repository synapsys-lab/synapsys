"""synapsys.viz.simview — Plug-and-play 3D simulation views.

Each view provides a unified PySide6 window (PyVista 3D + matplotlib telemetry)
that accepts any callable controller::

    from synapsys.viz import CartPoleView, PendulumView, MassSpringDamperView

    CartPoleView().run()                                   # auto-LQR
    PendulumView(controller=lambda x: -K @ x).run()       # custom LQR
    MassSpringDamperView(controller=my_rl_agent).run()     # RL / neural net
"""

from .cartpole import CartPoleView
from .msd import MassSpringDamperView
from .pendulum import PendulumView

__all__ = ["CartPoleView", "PendulumView", "MassSpringDamperView"]
