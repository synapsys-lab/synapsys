"""Cart-Pole — real-time 3D with LQR (PyVista).

Run:
    python examples/simulators/viz3d_cartpole.py

Keys:  R = reset   SPACE = pause/resume   Q/Esc = quit
"""

import numpy as np
import pyvista as pv
import vtk

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import CartPoleSim

# ── Physical parameters ───────────────────────────────────────────────────────
M_C, M_P, L, G = 1.0, 0.1, 0.5, 9.81
DT = 0.02  # simulation step (s)
X0 = np.array([0.0, 0.0, 0.18, 0.0])

# ── Geometry ──────────────────────────────────────────────────────────────────
CART_W, CART_D, CART_H = 0.40, 0.28, 0.12
POLE_R = 0.022
TRACK_HW = 3.5  # half-width of track
PIVOT_Z = CART_H + 0.01

# ── LQR design ───────────────────────────────────────────────────────────────
sim = CartPoleSim(m_c=M_C, m_p=M_P, l=L, g=G)
sim.reset()
ss = sim.linearize(np.zeros(4), np.zeros(1))
K, _ = lqr(ss.A, ss.B, np.diag([1.0, 0.1, 100.0, 10.0]), 0.01 * np.eye(1))
sim.reset(x0=X0)

# ── Shared state ──────────────────────────────────────────────────────────────
paused = [False]
pert_force = [0.0]  # extra force applied on top of LQR (N)
PERT_MAX = 30.0

# ── Plotter ───────────────────────────────────────────────────────────────────
pl = pv.Plotter(window_size=(1280, 720), title="Cart-Pole LQR — Real-Time 3D")
pl.set_background("#0f172a")
pl.add_light(pv.Light(position=(2, -5, 8), intensity=0.9))
pl.add_light(pv.Light(position=(-4, -3, 5), intensity=0.4))

# Ground
pl.add_mesh(
    pv.Box(bounds=(-TRACK_HW - 0.5, TRACK_HW + 0.5, -0.8, 0.8, -0.06, 0.0)),
    color="#1e293b",
    smooth_shading=True,
)

# Rail
pl.add_mesh(
    pv.Box(bounds=(-TRACK_HW, TRACK_HW, -0.04, 0.04, 0.0, 0.04)),
    color="#475569",
    smooth_shading=True,
)
# Rail end stops
for sign in (-1, 1):
    pl.add_mesh(
        pv.Box(
            bounds=(
                sign * TRACK_HW - 0.04,
                sign * TRACK_HW + 0.04,
                -0.1,
                0.1,
                0.0,
                0.15,
            )
        ),
        color="#ef4444",
        smooth_shading=True,
    )

# Wheel spheres (static shape, moved with actor transform)
wheel_offsets = [(-0.14, -0.10), (-0.14, 0.10), (0.14, -0.10), (0.14, 0.10)]
wheel_actors = []
for wx, wy in wheel_offsets:
    wm = pv.Sphere(radius=0.045, center=(wx, wy, 0.04))
    wa = pl.add_mesh(wm, color="#334155", smooth_shading=True)
    wheel_actors.append((wa, wx, wy))

# Cart body
cart_mesh = pv.Box(
    bounds=(-CART_W / 2, CART_W / 2, -CART_D / 2, CART_D / 2, 0.0, CART_H)
)
cart_actor = pl.add_mesh(cart_mesh, color="#2563eb", smooth_shading=True)

# Pivot joint
pivot_mesh = pv.Sphere(radius=POLE_R * 2.2, center=(0, 0, 0))
pivot_actor = pl.add_mesh(pivot_mesh, color="#64748b", smooth_shading=True)

# Pole (cylinder centered at origin, along Z — we apply transform each frame)
pole_mesh = pv.Cylinder(
    center=(0, 0, 0), direction=(0, 0, 1), height=L, radius=POLE_R, resolution=20
)
pole_actor = pl.add_mesh(pole_mesh, color="#c8a870", smooth_shading=True)

# Pole tip bob
bob_mesh = pv.Sphere(radius=POLE_R * 2.8, center=(0, 0, 0))
bob_actor = pl.add_mesh(bob_mesh, color="#f97316", smooth_shading=True)

# ── Text overlay ──────────────────────────────────────────────────────────────
hud = pl.add_text("", position=(12, 560), font_size=11, color="white", font="courier")
mode_hud = pl.add_text(
    "", position=(12, 660), font_size=13, color="#ef4444", font="courier"
)
pl.add_text(
    "A/D hold = push cart   R=reset   SPACE=pause   Q=quit",
    position=(12, 12),
    font_size=9,
    color="#94a3b8",
)


def _vtk_transform(tx, ty, tz, ry_deg=0.0, tz2=0.0):
    """Build a VTK transform: Translate(tx,ty,tz) · RotateY(ry) · Translate(0,0,tz2)."""
    t = vtk.vtkTransform()
    t.Translate(tx, ty, tz)
    t.RotateY(ry_deg)
    t.Translate(0.0, 0.0, tz2)
    return t


def _update():
    if paused[0]:
        return

    x = sim.state
    u_lqr = float(np.clip((-K @ x).ravel()[0], -50.0, 50.0))
    u = np.array([np.clip(u_lqr + pert_force[0], -80.0, 80.0)])
    sim.step(u, DT)

    cart_x = x[0]
    theta = x[2]
    theta_d = np.degrees(theta)

    cart_actor.SetUserTransform(_vtk_transform(cart_x, 0, 0))
    for wa, wx, wy in wheel_actors:
        wa.SetUserTransform(_vtk_transform(cart_x + wx, wy, 0))
    pivot_actor.SetUserTransform(_vtk_transform(cart_x, 0, PIVOT_Z))
    pole_actor.SetUserTransform(_vtk_transform(cart_x, 0, PIVOT_Z, theta_d, L / 2))

    tip_x = cart_x + L * np.sin(theta)
    tip_z = PIVOT_Z + L * np.cos(theta)
    bob_actor.SetUserTransform(_vtk_transform(tip_x, 0, tip_z))

    pert_str = f"{pert_force[0]:+5.0f} N" if abs(pert_force[0]) > 0.5 else "  --"
    hud.SetInput(
        f"  cart pos : {cart_x:+6.3f} m\n"
        f"  cart vel : {x[1]:+6.3f} m/s\n"
        f"  angle    : {theta_d:+6.2f}°\n"
        f"  ang vel  : {np.degrees(x[3]):+6.1f} °/s\n"
        f"  LQR F    : {u_lqr:+6.1f} N\n"
        f"  PERT F   : {pert_str}"
    )


def _on_key_press(caller, event):
    key = caller.GetKeySym().lower()
    if key == "a":
        pert_force[0] = -PERT_MAX
        mode_hud.SetInput("  [A] pushing cart left")
    elif key == "d":
        pert_force[0] = +PERT_MAX
        mode_hud.SetInput("  [D] pushing cart right")
    elif key == "r":
        sim.reset(x0=X0)
        pert_force[0] = 0.0
        mode_hud.SetInput("")
    elif key == "space":
        paused[0] = not paused[0]


def _on_key_release(caller, event):
    key = caller.GetKeySym().lower()
    if key in ("a", "d"):
        pert_force[0] = 0.0
        mode_hud.SetInput("")


def _timer_callback(caller, event):
    _update()
    caller.GetRenderWindow().Render()


pl.iren.add_observer("KeyPressEvent", _on_key_press)
pl.iren.add_observer("KeyReleaseEvent", _on_key_release)

pl.camera_position = [(0, -5.5, 1.2), (0, 0, 0.4), (0, 0, 1)]
pl.show(auto_close=False, interactive_update=True)

pl.iren.add_observer("TimerEvent", _timer_callback)
pl.iren.create_timer(int(DT * 1000), repeating=True)
pl.iren.start()
