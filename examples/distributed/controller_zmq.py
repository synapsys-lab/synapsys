"""
Distributed simulation via ZeroMQ — Controller process.

The controller subscribes to y from tcp://localhost:5555 (SUB)
and publishes u on tcp://0.0.0.0:5556 (PUB).

Can run on a different machine from plant_zmq.py.
Change PLANT_HOST to the plant's IP address if remote.

Usage:
    python examples/distributed/controller_zmq.py
"""
import time
import numpy as np

from synapsys.algorithms.pid import PID
from synapsys.transport.network import ZMQTransport

PLANT_HOST = "localhost"
DT = 0.025      # controller runs at 2× plant rate
SETPOINT = 5.0

pid = PID(Kp=3.0, Ki=0.5, dt=DT, u_min=-20.0, u_max=20.0)

sub = ZMQTransport(f"tcp://{PLANT_HOST}:5555", mode="sub")
pub = ZMQTransport("tcp://0.0.0.0:5556", mode="pub")
sub._socket.setsockopt(0x8, 50)  # ZMQ_RCVTIMEO = 50 ms

print(f"Controller: subscribing y from :{5555}, publishing u on :{5556}")
print(f"Setpoint = {SETPOINT}")
time.sleep(0.5)  # let plant start first

try:
    while True:
        t0 = time.monotonic()

        try:
            y = sub.read("y")
            u = pid.compute(setpoint=SETPOINT, measurement=y[0])
            pub.write("u", np.array([u]))
        except Exception:
            pass  # plant not ready yet; keep looping

        elapsed = time.monotonic() - t0
        if DT - elapsed > 0:
            time.sleep(DT - elapsed)

except KeyboardInterrupt:
    print("\nController: stopped.")
finally:
    sub.close()
    pub.close()
