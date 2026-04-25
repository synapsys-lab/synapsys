"""Mass-Spring-Damper — exemplos usando MassSpringDamperView.

Descomente o bloco desejado e execute:
    python examples/simulators/temp/01_msd_view.py
"""

from synapsys.viz import MassSpringDamperView

# ── 1. LQR automático (padrão) ───────────────────────────────────────────────
MassSpringDamperView().run()

# ── 2. Controlador PD customizado ────────────────────────────────────────────
# Kp, Kd = 20.0, 8.0
# def pd_ctrl(x):
#     q, qdot = x
#     return np.array([-(Kp * q + Kd * qdot)])
#
# MassSpringDamperView(controller=pd_ctrl).run()

# ── 3. Setpoints customizados ────────────────────────────────────────────────
# setpoints = [("0 m", 0.0), ("+2 m", 2.0), ("-2 m", -2.0), ("+0.5 m", 0.5)]
# MassSpringDamperView(setpoints=setpoints).run()

# ── 4. Parâmetros físicos customizados ───────────────────────────────────────
# MassSpringDamperView(m=2.0, c=0.3, k=5.0).run()

# ── 5. Estado inicial customizado ────────────────────────────────────────────
# MassSpringDamperView(x0=np.array([1.5, 0.0])).run()
