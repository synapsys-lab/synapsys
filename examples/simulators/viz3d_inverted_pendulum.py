"""Inverted Pendulum (fixed pivot) — real-time 3D with LQR + mouse perturbation.

Run:
    python examples/simulators/viz3d_inverted_pendulum.py

Keys:
  R        — reset simulation
  SPACE    — pause / resume
  A (hold) — apply negative torque  (push pendulum left)
  D (hold) — apply positive torque  (push pendulum right)
  Q/Esc    — quit

Mouse: rotate / zoom camera normally (no conflicts).
"""

import numpy as np
import pyvista as pv
import vtk

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import InvertedPendulumSim

# ── Physical parameters ───────────────────────────────────────────────────────
M, L, G, B = 1.0, 1.0, 9.81, 0.1
DT = 0.01
X0 = np.array([0.18, 0.0])
PERT_MAX = 20.0  # N·m maximum mouse perturbation

# ── LQR design ───────────────────────────────────────────────────────────────
sim = InvertedPendulumSim(m=M, l=L, g=G, b=B)
sim.reset()
ss = sim.linearize(np.zeros(2), np.zeros(1))
K, _ = lqr(ss.A, ss.B, np.diag([80.0, 5.0]), np.eye(1))
print(f"K = {K.ravel().round(3)}")
print(f"Poles: {np.linalg.eigvals(ss.A - ss.B @ K).round(3)}")
sim.reset(x0=X0)

PIVOT_Z = 0.12
POLE_R = 0.028

# ── Shared state ──────────────────────────────────────────────────────────────
paused = [False]
pert_torque = [0.0]  # current perturbation torque (N·m)

# ── Plotter ───────────────────────────────────────────────────────────────────
pl = pv.Plotter(window_size=(1100, 700), title="Inverted Pendulum LQR — Real-Time 3D")
pl.set_background("#0f172a")
pl.add_light(pv.Light(position=(3, -5, 6), intensity=0.9))
pl.add_light(pv.Light(position=(-3, -2, 4), intensity=0.35))

# Ground
pl.add_mesh(
    pv.Box(bounds=(-1.2, 1.2, -1.2, 1.2, -0.06, 0.0)),
    color="#1e293b",
    smooth_shading=True,
)

# Base plate
pl.add_mesh(
    pv.Cylinder(
        center=(0, 0, 0.04),
        direction=(0, 0, 1),
        height=0.08,
        radius=0.22,
        resolution=32,
    ),
    color="#334155",
    smooth_shading=True,
)

# Pivot joint
pl.add_mesh(
    pv.Sphere(radius=0.055, center=(0, 0, PIVOT_Z)),
    color="#64748b",
    smooth_shading=True,
)

# Pole
pole_mesh = pv.Cylinder(
    center=(0, 0, 0), direction=(0, 0, 1), height=L, radius=POLE_R, resolution=20
)
pole_actor = pl.add_mesh(pole_mesh, color="#c8a870", smooth_shading=True)

# Bob at tip
bob_mesh = pv.Sphere(radius=POLE_R * 3.0, center=(0, 0, 0))
bob_actor = pl.add_mesh(bob_mesh, color="#f97316", smooth_shading=True)

# Equilibrium guide line
pl.add_mesh(
    pv.Line((0, 0, PIVOT_Z), (0, 0, PIVOT_Z + L + 0.1)),
    color="#16a34a",
    opacity=0.25,
    line_width=1,
)

# Perturbation arrow (two actors: left and right; shown/hidden by opacity)
arr_r_mesh = pv.Arrow(
    start=(0, 0, 0), direction=(1, 0, 0), scale=0.45, tip_length=0.3, shaft_radius=0.05
)
arr_l_mesh = pv.Arrow(
    start=(0, 0, 0), direction=(-1, 0, 0), scale=0.45, tip_length=0.3, shaft_radius=0.05
)
arr_r_actor = pl.add_mesh(arr_r_mesh, color="#ef4444", opacity=0.0)
arr_l_actor = pl.add_mesh(arr_l_mesh, color="#ef4444", opacity=0.0)

# ── Phase portrait trail ──────────────────────────────────────────────────────
TRAIL_LEN = 250
trail_pts = np.zeros((TRAIL_LEN, 3))
trail_mesh = pv.PolyData(trail_pts)
pl.add_mesh(
    trail_mesh,
    color="#7c3aed",
    point_size=2.5,
    render_points_as_spheres=True,
    opacity=0.6,
)
trail_idx = [0]

# ── Text overlays ─────────────────────────────────────────────────────────────
hud = pl.add_text("", position=(12, 510), font_size=11, color="white", font="courier")
mode_hud = pl.add_text(
    "", position=(12, 660), font_size=13, color="#ef4444", font="courier"
)
pl.add_text(
    "A/D hold = push left/right   R=reset   SPACE=pause   Q=quit",
    position=(12, 12),
    font_size=9,
    color="#94a3b8",
)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _vtk_transform(tx, ty, tz, ry_deg=0.0, tz2=0.0):
    t = vtk.vtkTransform()
    t.Translate(tx, ty, tz)
    t.RotateY(ry_deg)
    t.Translate(0.0, 0.0, tz2)
    return t


# ── Simulation update (called every timer tick) ───────────────────────────────
def _update():
    if paused[0]:
        return

    x = sim.state
    tau_lqr = float(np.clip((-K @ x).ravel()[0], -30.0, 30.0))
    tau_pert = pert_torque[0]
    u = np.array([np.clip(tau_lqr + tau_pert, -50.0, 50.0)])
    sim.step(u, DT)

    theta = x[0]
    theta_d = np.degrees(theta)
    tip_x = L * np.sin(theta)
    tip_z = PIVOT_Z + L * np.cos(theta)

    # Pole
    pole_actor.SetUserTransform(_vtk_transform(0, 0, PIVOT_Z, theta_d, L / 2))

    # Bob — turns red while perturbing
    bob_actor.SetUserTransform(_vtk_transform(tip_x, 0, tip_z))
    if abs(tau_pert) > 0.5:
        bob_actor.GetProperty().SetColor(0.94, 0.27, 0.27)
    else:
        bob_actor.GetProperty().SetColor(0.97, 0.57, 0.07)

    # Perturbation arrows
    if tau_pert > 0.5:
        t_a = vtk.vtkTransform()
        t_a.Translate(tip_x - 0.1, 0, tip_z)
        arr_r_actor.SetUserTransform(t_a)
        arr_r_actor.GetProperty().SetOpacity(min(tau_pert / PERT_MAX, 1.0))
        arr_l_actor.GetProperty().SetOpacity(0.0)
    elif tau_pert < -0.5:
        t_a = vtk.vtkTransform()
        t_a.Translate(tip_x + 0.1, 0, tip_z)
        arr_l_actor.SetUserTransform(t_a)
        arr_l_actor.GetProperty().SetOpacity(min(-tau_pert / PERT_MAX, 1.0))
        arr_r_actor.GetProperty().SetOpacity(0.0)
    else:
        arr_r_actor.GetProperty().SetOpacity(0.0)
        arr_l_actor.GetProperty().SetOpacity(0.0)

    # Phase trail
    idx = trail_idx[0] % TRAIL_LEN
    trail_pts[idx] = [0.8 + theta * 0.5, -0.9, 0.1 + x[1] * 0.05]
    trail_mesh.points = trail_pts
    trail_idx[0] += 1

    # HUD
    pert_str = f"{tau_pert:+6.1f} N·m" if abs(tau_pert) > 0.5 else "   --"
    arrow_str = "  [A]" if tau_pert < -0.5 else "  [D]" if tau_pert > 0.5 else ""
    hud.SetInput(
        f"  angle    : {theta_d:+6.2f}°\n"
        f"  ang vel  : {np.degrees(x[1]):+6.1f} °/s\n"
        f"  LQR τ    : {tau_lqr:+6.2f} N·m\n"
        f"  PERT τ   : {pert_str}{arrow_str}\n"
        f"  λ_unstable = +{sim.unstable_pole():.3f} rad/s"
    )


# ── Key handlers ──────────────────────────────────────────────────────────────
def _on_key_press(caller, event):
    key = caller.GetKeySym().lower()
    if key == "a":
        pert_torque[0] = -PERT_MAX
        mode_hud.SetInput("  [A] pushing left")
    elif key == "d":
        pert_torque[0] = +PERT_MAX
        mode_hud.SetInput("  [D] pushing right")
    elif key == "r":
        sim.reset(x0=X0)
        trail_pts[:] = 0
        trail_idx[0] = 0
        pert_torque[0] = 0.0
        mode_hud.SetInput("")
    elif key == "space":
        paused[0] = not paused[0]


def _on_key_release(caller, event):
    key = caller.GetKeySym().lower()
    if key in ("a", "d"):
        pert_torque[0] = 0.0
        mode_hud.SetInput("")


# ── Timer callback ────────────────────────────────────────────────────────────
def _timer_callback(caller, event):
    _update()
    caller.GetRenderWindow().Render()


# ── Wire everything up ────────────────────────────────────────────────────────
pl.iren.add_observer("KeyPressEvent", _on_key_press)
pl.iren.add_observer("KeyReleaseEvent", _on_key_release)

pl.camera_position = [(2.5, -4.5, 1.0), (0, 0, 0.6), (0, 0, 1)]
pl.show(auto_close=False, interactive_update=True)

pl.iren.add_observer("TimerEvent", _timer_callback)
pl.iren.create_timer(int(DT * 1000), repeating=True)
pl.iren.start()
