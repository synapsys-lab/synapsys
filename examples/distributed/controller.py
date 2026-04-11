"""
Distributed simulation — Controller process.

Run AFTER starting plant.py in a separate terminal.

The controller reads the plant output from shared memory, computes
a PID control action, and writes it back — without sharing any code
with the plant process.

Usage:
    python examples/distributed/controller.py
"""
import time
import numpy as np

from synapsys.transport.shared_memory import SharedMemoryTransport
from synapsys.algorithms.pid import PID

BUS_NAME = "synapsys_demo"
CHANNELS = {"y": 1, "u": 1}
DT = 0.025   # 40 Hz — faster than the plant
SETPOINT = 5.0

pid = PID(Kp=3.0, Ki=0.5, dt=DT, u_min=-10.0, u_max=10.0)

try:
    with SharedMemoryTransport(BUS_NAME, CHANNELS, create=False) as bus:
        print(f"Controller: connected.  Setpoint = {SETPOINT}")
        while True:
            y = bus.read("y")[0]
            u = pid.compute(setpoint=SETPOINT, measurement=y)
            bus.write("u", np.array([u]))
            time.sleep(DT)

except FileNotFoundError:
    print("Error: start plant.py first to initialise the shared-memory bus.")
except KeyboardInterrupt:
    print("\nController: stopped.")
