"""Controladores customizados — integração com CartPoleView.

Demonstra como plugar diferentes estratégias de controle:
PID, rede neural simples, controle por lookup table.

Execute:
    python examples/simulators/temp/04_custom_controllers.py
"""

import numpy as np

from synapsys.viz import CartPoleView

# ── PID no ângulo ─────────────────────────────────────────────────────────────


class PIDController:
    def __init__(self, Kp=120.0, Ki=2.0, Kd=25.0, dt=0.01):
        self.Kp, self.Ki, self.Kd, self.dt = Kp, Ki, Kd, dt
        self._integral = 0.0
        self._prev_err = 0.0

    def __call__(self, x):
        _, _, theta, _ = x
        err = theta
        self._integral += err * self.dt
        deriv = (err - self._prev_err) / self.dt
        self._prev_err = err
        u = -(self.Kp * err + self.Ki * self._integral + self.Kd * deriv)
        return np.array([np.clip(u, -50, 50)])


pid = PIDController()
CartPoleView(controller=pid).run()


# ── Rede neural com pesos aleatórios (exemplo de integração) ──────────────────
# W1 = np.random.randn(8, 4) * 0.1
# W2 = np.random.randn(1, 8) * 0.1
#
# def neural_ctrl(x):
#     h = np.tanh(W1 @ x)
#     return np.array([float(np.tanh(W2 @ h)[0]) * 50])
#
# CartPoleView(controller=neural_ctrl).run()


# ── Feedback linearização simplificada ────────────────────────────────────────
# m_c, m_p, l, g = 1.0, 0.1, 0.5, 9.81
#
# def feedback_lin(x):
#     pos, vel, theta, thetadot = x
#     sin_t, cos_t = np.sin(theta), np.cos(theta)
#     M = m_c + m_p
#     num = (m_p * l * thetadot**2 * sin_t
#            - m_p * g * sin_t * cos_t
#            - 60 * theta - 20 * thetadot
#            - 2 * pos - 3 * vel)
#     denom = M - m_p * cos_t**2
#     return np.array([np.clip(num / denom * M, -50, 50)])
#
# CartPoleView(controller=feedback_lin).run()
