"""synapsys.viz — Utilities for real-time and static visualisation."""

from .palette import Dark, mpl_theme
from .simview import CartPoleView, MassSpringDamperView, PendulumView

__all__ = [
    "Dark",
    "mpl_theme",
    "CartPoleView",
    "PendulumView",
    "MassSpringDamperView",
]
