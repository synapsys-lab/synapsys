"""
Basic example: step response of a second-order system.

Usage:
    python examples/basic/step_response.py
"""

import matplotlib.pyplot as plt

from synapsys.api.matlab_compat import step, tf

# Second-order underdamped system: G(s) = wn^2 / (s^2 + 2*zeta*wn*s + wn^2)
wn, zeta = 10.0, 0.5
G = tf([wn**2], [1, 2 * zeta * wn, wn**2])

print(G)
print(f"Poles   : {G.poles()}")
print(f"Stable  : {G.is_stable()}")

t, y = step(G)

plt.figure()
plt.plot(t, y, label="y(t)")
plt.axhline(1.0, color="k", linestyle="--", alpha=0.4, label="setpoint")
plt.title("Step Response — second-order system")
plt.xlabel("Time (s)")
plt.ylabel("y(t)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("step_response.png", dpi=150)
print("Plot saved: step_response.png")
plt.show()
