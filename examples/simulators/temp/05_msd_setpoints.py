"""MSD com setpoints e controlador externo — demonstração avançada.

Mostra:
- Setpoints customizados (teclas 1/2/3/4)
- Controlador LQR externo com ganho pré-computado
- Combinando parâmetros físicos, setpoints e estado inicial

Execute:
    python examples/simulators/temp/05_msd_setpoints.py
"""

from synapsys.viz import MassSpringDamperView

# ── 1. Setpoints customizados com LQR automático ─────────────────────────────
setpoints = [("0 m", 0.0), ("+1 m", 1.0), ("-1 m", -1.0), ("+2 m", 2.0)]
MassSpringDamperView(setpoints=setpoints).run()


# ── 2. Ganho LQR pré-computado externamente ──────────────────────────────────
# m, c, k = 1.5, 0.4, 3.0
# sim = MassSpringDamperSim(m=m, c=c, k=k)
# sim.reset()
# ss = sim.linearize(np.zeros(2), np.zeros(1))
# Q  = np.diag([50.0, 10.0])
# R  = np.eye(1) * 0.5
# K, _ = lqr(ss.A, ss.B, Q, R)
#
# sp = 1.0   # setpoint fixo
# def lqr_tracking(x):
#     x_err = x - np.array([sp, 0.0])
#     return (-K @ x_err + k * sp).ravel()
#
# MassSpringDamperView(
#     m=m, c=c, k=k,
#     controller=lqr_tracking,
#     setpoints=[("+1 m", 1.0)],
# ).run()


# ── 3. Combinação completa ────────────────────────────────────────────────────
# MassSpringDamperView(
#     m=2.0, c=0.2, k=4.0,
#     x0=np.array([1.0, 0.0]),
#     setpoints=[("0 m", 0.0), ("+1.5 m", 1.5), ("-1.5 m", -1.5)],
# ).run()
