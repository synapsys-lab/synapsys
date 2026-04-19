import matplotlib.pyplot as plt
import numpy as np

from synapsys.api import tf

print("Running Custom Signals Batch Simulation...")

# System G(s) = 10 / (s^2 + 5s + 10)
print("Creating plant LTI model...")
G = tf([10], [1, 5, 10])

# Time vector (0 to 10 seconds, 1000 points)
t = np.linspace(0, 10, 1000)

# 1. Base Sine Wave (Simulating mechanical vibration at 1.5 Hz)
u_sine = np.sin(2 * np.pi * 1.5 * t)

# 2. Logic Step Injection (Triggers active only after t = 5s with amplitude 2)
u_step = np.where(t >= 5, 2.0, 0.0)

# Principle of Superposition: Combine the signals
u_total = u_sine + u_step

print("Simulating response to arbitrary signal array...")
# Simulate the LTI plant with the complex signal
t_out, y_out = G.simulate(t, u_total)

print("Plotting results (close window to exit)...")
plt.figure(figsize=(10, 5))
plt.title("Arbitrary Test Signal Injection (MIL/Batch)")
plt.plot(t_out, u_total, label="Input u(t) - Sine + Step", linestyle="--", alpha=0.8)
plt.plot(t_out, y_out, label="Output y(t)", linewidth=2)
plt.xlabel("Time [s]")
plt.ylabel("Amplitude")
plt.grid(True)
plt.legend()
plt.show()
