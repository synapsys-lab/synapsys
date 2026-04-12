"""
Distributed simulation — Plant process.

Run this FIRST, then start controller.py in a separate terminal.

The plant exposes its state on a shared-memory bus with two channels:
    y  — plant output (scalar)
    u  — control input (scalar, written by the controller)

Usage:
    python examples/distributed/plant.py
"""
import time
import numpy as np

from synapsys.transport.shared_memory import SharedMemoryTransport

BUS_NAME = "synapsys_demo"
CHANNELS = {"y": 1, "u": 1}
DT = 0.05   # 20 Hz
N_STEPS = 200

with SharedMemoryTransport(BUS_NAME, CHANNELS, create=True) as bus:
    bus.write("y", np.array([0.0]))
    bus.write("u", np.array([0.0]))
    print("Plant: bus ready.  Starting in 2 s — launch controller.py now.")
    time.sleep(2.0)

    for k in range(N_STEPS):
        u = bus.read("u")[0]
        y = bus.read("y")[0]

        # Discrete first-order dynamics: y(k+1) = 0.9*y(k) + 0.1*u(k)
        y_next = 0.9 * y + 0.1 * u
        bus.write("y", np.array([y_next]))

        print(f"k={k:03d}  u={u:7.3f}  y={y_next:7.3f}")
        time.sleep(DT)

print("Plant: simulation complete.")
