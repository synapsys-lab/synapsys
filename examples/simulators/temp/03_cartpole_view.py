"""Cart-Pole — exemplos usando CartPoleView.

Descomente o bloco desejado e execute:
    python examples/simulators/temp/03_cartpole_view.py
"""

from synapsys.viz import CartPoleView

# ── 1. LQR automático (padrão) ───────────────────────────────────────────────
CartPoleView().run()

# ── 2. Estado inicial customizado ────────────────────────────────────────────
# CartPoleView(x0=np.array([0.0, 0.0, 0.30, 0.0])).run()

# ── 3. Parâmetros físicos customizados ───────────────────────────────────────
# CartPoleView(m_c=0.5, m_p=0.2, l=0.8).run()

# ── 4. Controlador PD customizado ────────────────────────────────────────────
# Kp_th, Kd_th = 80.0, 20.0
# Kp_x,  Kd_x  =  5.0,  4.0
# def pd_ctrl(x):
#     pos, vel, theta, thetadot = x
#     u = -(Kp_th * theta + Kd_th * thetadot +
#           Kp_x  * pos   + Kd_x  * vel)
#     return np.array([np.clip(u, -50, 50)])
#
# CartPoleView(controller=pd_ctrl).run()

# ── 5. Observando instabilidade (torque zero) ────────────────────────────────
# CartPoleView(controller=lambda x: np.zeros(1),
#              x0=np.array([0.0, 0.0, 0.05, 0.0])).run()
