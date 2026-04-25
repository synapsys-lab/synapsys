"""Mass-Spring-Damper — real-time 3D with LQR tracking a setpoint (PyVista).

Run:
    python examples/simulators/viz3d_mass_spring_damper.py

Keys:  R = reset   SPACE = pause/resume   1/2/3 = change setpoint   Q/Esc = quit
"""

import numpy as np
import pyvista as pv
import vtk

from synapsys.algorithms.lqr import lqr
from synapsys.simulators import MassSpringDamperSim

# ── Physical parameters ───────────────────────────────────────────────────────
M, C, K_SPR = 1.0, 0.5, 2.0
DT = 0.01
X0 = np.array([0.0, 0.0])

SETPOINTS = {
    "1": 0.0,
    "2": 1.5,
    "3": -1.5,
}
setpoint = [0.0]

# ── LQR design (augmented with integrator for zero steady-state error) ────────
sim = MassSpringDamperSim(m=M, c=C, k=K_SPR)
sim.reset()
ss = sim.linearize(np.zeros(2), np.zeros(1))
# Use state-feedback with feed-forward: u = -K @ (x - x_ref) + F_ss
# F_ss = K_spr * q_ref (force needed to hold at setpoint)
K, _ = lqr(ss.A, ss.B, np.diag([20.0, 5.0]), np.eye(1))
print(f"K = {K.ravel().round(3)}")
sim.reset(x0=X0)

# ── Scene geometry ────────────────────────────────────────────────────────────
WALL_X = -2.5
MASS_W, MASS_D, MASS_H = 0.45, 0.45, 0.45
N_COILS = 8
SPRING_R = 0.07
SPRING_WIRE_R = 0.015
DAMP_W = 0.12
DAMP_H = 0.35
FLOOR_Y = -0.3

paused = [False]
pert_force = [0.0]  # extra force on mass (N)
PERT_MAX = 15.0


def _spring_polydata(x_wall, x_mass, radius=SPRING_R, n_coils=N_COILS, n_pts=400):
    """Helical spring between wall and mass centre."""
    t = np.linspace(0.0, n_coils * 2 * np.pi, n_pts)
    x = np.linspace(x_wall + 0.05, x_mass - MASS_W / 2 - 0.02, n_pts)
    y = radius * np.sin(t)
    z = radius * np.cos(t) + MASS_H / 2
    pts = np.column_stack([x, y, z])
    spline = pv.Spline(pts, n_pts)
    return spline.tube(radius=SPRING_WIRE_R, n_sides=12)


# ── Plotter ───────────────────────────────────────────────────────────────────
pl = pv.Plotter(window_size=(1200, 700), title="Mass-Spring-Damper LQR — Real-Time 3D")
pl.set_background("#0f172a")
pl.add_light(pv.Light(position=(2, -5, 6), intensity=0.9))
pl.add_light(pv.Light(position=(-4, -2, 4), intensity=0.35))

# Floor
pl.add_mesh(
    pv.Box(bounds=(-3.5, 3.5, -0.5, 0.5, FLOOR_Y - 0.06, FLOOR_Y)),
    color="#1e293b",
    smooth_shading=True,
)

# Wall
pl.add_mesh(
    pv.Box(bounds=(WALL_X - 0.15, WALL_X, -0.5, 0.5, FLOOR_Y, 0.8)),
    color="#334155",
    smooth_shading=True,
)

# Rail
pl.add_mesh(
    pv.Box(bounds=(-2.4, 2.4, -0.04, 0.04, FLOOR_Y, FLOOR_Y + 0.04)),
    color="#475569",
    smooth_shading=True,
)

# Damper body (cylinder, static — just visual hint, follows mass)
damp_mesh = pv.Box(
    bounds=(-DAMP_W / 2, DAMP_W / 2, -DAMP_W / 2, DAMP_W / 2, 0.0, DAMP_H)
)
damp_actor = pl.add_mesh(damp_mesh, color="#64748b", smooth_shading=True, opacity=0.7)

# Spring (updated each frame — PolyData whose points we rebuild)
spring_actor_ref = [None]
spring_mesh_ref = [_spring_polydata(WALL_X, 0.0)]
spring_actor_ref[0] = pl.add_mesh(
    spring_mesh_ref[0], color="#c8a870", smooth_shading=True
)

# Mass block
mass_mesh = pv.Box(
    bounds=(-MASS_W / 2, MASS_W / 2, -MASS_D / 2, MASS_D / 2, FLOOR_Y, FLOOR_Y + MASS_H)
)
mass_actor = pl.add_mesh(mass_mesh, color="#2563eb", smooth_shading=True)

# Setpoint indicator (thin vertical bar)
setpt_mesh = pv.Box(
    bounds=(-0.015, 0.015, -0.3, 0.3, FLOOR_Y - 0.02, FLOOR_Y + MASS_H + 0.1)
)
setpt_actor = pl.add_mesh(setpt_mesh, color="#16a34a", opacity=0.6)

# ── Displacement plot (trail on the right) ────────────────────────────────────
TRAIL_LEN = 300
trail_t = np.linspace(0, 1, TRAIL_LEN)
trail_q = np.zeros(TRAIL_LEN)
trail_pts = np.zeros((TRAIL_LEN, 3))
trail_mesh = pv.PolyData(trail_pts)
pl.add_mesh(
    trail_mesh,
    color="#3b82f6",
    point_size=2,
    render_points_as_spheres=True,
    opacity=0.8,
)
trail_idx = [0]
t_elapsed = [0.0]

# ── Text overlay ──────────────────────────────────────────────────────────────
hud = pl.add_text("", position=(12, 480), font_size=11, color="white", font="courier")
mode_hud = pl.add_text(
    "", position=(12, 660), font_size=13, color="#ef4444", font="courier"
)
pl.add_text(
    "A/D hold = push mass   1/2/3=setpoint   R=reset   SPACE=pause   Q=quit",
    position=(12, 12),
    font_size=9,
    color="#94a3b8",
)


def _update():
    if paused[0]:
        return

    x = sim.state
    sp = setpoint[0]
    x_err = x - np.array([sp, 0.0])
    u_lqr = float(np.clip((-K @ x_err + K_SPR * sp).ravel()[0], -30.0, 30.0))
    u = np.array([np.clip(u_lqr + pert_force[0], -50.0, 50.0)])
    sim.step(u, DT)
    t_elapsed[0] += DT

    q = x[0]

    # Mass position
    mass_actor.SetUserTransform(
        (lambda t: (t.Translate(q, 0, 0), t)[1])(vtk.vtkTransform())
    )

    # Damper follows mass (half-hidden behind it)
    t_d = vtk.vtkTransform()
    t_d.Translate(q - MASS_W / 2 - DAMP_W / 2 - 0.04, 0, FLOOR_Y)
    damp_actor.SetUserTransform(t_d)

    # Setpoint indicator
    t_sp = vtk.vtkTransform()
    t_sp.Translate(sp, 0, 0)
    setpt_actor.SetUserTransform(t_sp)

    # Spring: rebuild geometry with updated mass position
    new_spring = _spring_polydata(WALL_X, q)
    spring_mesh_ref[0].points = new_spring.points
    spring_mesh_ref[0].lines = new_spring.lines

    # Displacement trail (q mapped to Z, time mapped to Y offset)
    idx = trail_idx[0] % TRAIL_LEN
    trail_pts[idx] = [2.8, -0.4 + (trail_idx[0] % TRAIL_LEN) / TRAIL_LEN * 0.8, q * 0.4]
    trail_mesh.points = trail_pts
    trail_idx[0] += 1

    pert_str = f"{pert_force[0]:+5.0f} N" if abs(pert_force[0]) > 0.5 else "  --"
    hud.SetInput(
        f"  position : {q:+6.3f} m\n"
        f"  velocity : {x[1]:+6.3f} m/s\n"
        f"  setpoint : {sp:+6.3f} m\n"
        f"  error    : {(q - sp):+6.3f} m\n"
        f"  LQR F    : {u_lqr:+6.1f} N\n"
        f"  PERT F   : {pert_str}\n"
        f"  ωₙ = {sim.natural_frequency():.2f} rad/s   ζ = {sim.damping_ratio():.3f}"
    )


def _on_key_press(caller, event):
    key = caller.GetKeySym().lower()
    if key == "a":
        pert_force[0] = -PERT_MAX
        mode_hud.SetInput("  [A] pushing mass left")
    elif key == "d":
        pert_force[0] = +PERT_MAX
        mode_hud.SetInput("  [D] pushing mass right")
    elif key == "r":
        sim.reset(x0=X0)
        t_elapsed[0] = 0.0
        trail_idx[0] = 0
        trail_pts[:] = 0
        pert_force[0] = 0.0
        mode_hud.SetInput("")
    elif key == "space":
        paused[0] = not paused[0]
    elif key in SETPOINTS:
        setpoint[0] = SETPOINTS[key]


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

pl.camera_position = [(0, -6, 0.4), (0, 0, 0.1), (0, 0, 1)]
pl.show(auto_close=False, interactive_update=True)

pl.iren.add_observer("TimerEvent", _timer_callback)
pl.iren.create_timer(int(DT * 1000), repeating=True)
pl.iren.start()
