"""synapsys.viz — Utilities for real-time and static visualisation."""

from .cartpole2d import CartPole2DView
from .palette import Dark, Light, mpl_theme

# SimView classes depend on Qt/PyVista — import lazily so that
# CartPole2DView (pure matplotlib) remains importable on headless environments.
try:
    from .simview import CartPoleView, MassSpringDamperView, PendulumView

    __all__ = [
        "Dark",
        "Light",
        "mpl_theme",
        "CartPole2DView",
        "CartPoleView",
        "PendulumView",
        "MassSpringDamperView",
    ]
except ImportError:
    __all__ = [
        "Dark",
        "Light",
        "mpl_theme",
        "CartPole2DView",
    ]
