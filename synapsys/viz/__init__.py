"""synapsys.viz — Utilities for real-time and static visualisation."""

from .cartpole2d import CartPole2DView
from .palette import Dark, mpl_theme
from .simview import CartPoleView, MassSpringDamperView, PendulumView

__all__ = [
    "Dark",
    "mpl_theme",
    "CartPole2DView",
    "CartPoleView",
    "PendulumView",
    "MassSpringDamperView",
]
