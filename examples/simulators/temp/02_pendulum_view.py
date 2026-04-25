"""Pêndulo Invertido — exemplos usando PendulumView.

Descomente o bloco desejado e execute:
    python examples/simulators/temp/02_pendulum_view.py
"""

from synapsys.viz import PendulumView

# ── 1. LQR automático (padrão) ───────────────────────────────────────────────
PendulumView().run()

# ── 2. Estado inicial customizado (perturbação maior) ────────────────────────
# PendulumView(x0=np.array([0.35, 0.0])).run()

# ── 3. Controlador energético (swing-up simples) ─────────────────────────────
# def energy_ctrl(x):
#     theta, thetadot = x
#     E_ref = 9.81 * 1.0   # m*g*l com m=1, l=1
#     E     = 0.5 * thetadot**2 - 9.81 * np.cos(theta)
#     return np.array([np.clip(3.0 * thetadot * (E - E_ref), -30, 30)])
#
# PendulumView(controller=energy_ctrl).run()

# ── 4. Parâmetros físicos customizados ───────────────────────────────────────
# PendulumView(m=0.5, l=1.5, b=0.05).run()

# ── 5. Torque zero (queda livre a partir de perturbação) ─────────────────────
# PendulumView(controller=lambda x: np.zeros(1),
#              x0=np.array([0.1, 0.0])).run()
