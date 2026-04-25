"""06_simview_advanced.py — SimView: camera presets, trajectory trail, save=.

Demonstrates new features added in v0.2.7 that require a Qt display:

    1. set_camera_preset() — choose viewing angle before run()
    2. toggle_trail()      — enable 3D trajectory trail
    3. save=               — record animation to file on close

Run one section at a time by uncommenting the desired block.
Requires: pyside6, pyvistaqt, matplotlib

Run:
    uv run python examples/simulators/06_simview_advanced.py
"""

from synapsys.viz import CartPoleView

# ── choose which demo to run ──────────────────────────────────────────────────
# Uncomment exactly one block.

# ── 1. Camera preset: top-down ────────────────────────────────────────────────
view = CartPoleView()
view.set_camera_preset("top")
view.run()

# ── 2. Camera preset: isometric + trajectory trail ────────────────────────────
# view = CartPoleView()
# view.set_camera_preset("iso")
# view.toggle_trail()        # violet trail traces the pole tip
# view.run()

# ── 3. Side view + trail — inverted pendulum ──────────────────────────────────
# view = PendulumView()
# view.set_camera_preset("side")
# view.toggle_trail()        # traces pole tip arc
# view.run()

# ── 4. MSD with trail + save ──────────────────────────────────────────────────
# view = MassSpringDamperView(save="/tmp/msd_session.gif")
# view.toggle_trail()        # traces mass centre path
# view.run()
# # After closing the window: /tmp/msd_session.gif is written.

# ── 5. CartPole: follow-cam + save ────────────────────────────────────────────
# view = CartPoleView(save="/tmp/cartpole_session.gif")
# view.set_camera_preset("follow")
# view.run()
