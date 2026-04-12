"""
Distributed simulation via ZeroMQ — Plant process.

The plant publishes y on tcp://0.0.0.0:5555 (PUB)
and subscribes to u from tcp://localhost:5556 (SUB).

Can run on a different machine from controller_zmq.py.
Change CONTROLLER_HOST to the controller's IP address if remote.

Usage:
    python examples/distributed/plant_zmq.py
"""
import time
import numpy as np

from synapsys.api.matlab_compat import ss, c2d
from synapsys.transport.network import ZMQTransport

CONTROLLER_HOST = "localhost"
DT = 0.05
N_STEPS = 300

# G(s) = 1/(s+1) discretised with ZOH
plant_d = c2d(ss([[-1.0]], [[1.0]], [[1.0]], [[0.0]]), dt=DT)
x = np.zeros(plant_d.n_states)

pub = ZMQTransport("tcp://0.0.0.0:5555", mode="pub")
sub = ZMQTransport(f"tcp://{CONTROLLER_HOST}:5556", mode="sub")
sub._socket.setsockopt(0x8, 100)  # ZMQ_RCVTIMEO = 100 ms

print(f"Plant: publishing y on :5555, subscribing u from :{5556}")
time.sleep(1.0)  # give sockets time to bind

u = np.array([0.0])

for k in range(N_STEPS):
    t0 = time.monotonic()

    x, y = plant_d.evolve(x, u)
    pub.write("y", y)

    # Non-blocking read — use last u if controller hasn't sent yet (ZOH)
    try:
        u = sub.read("u")
    except Exception:
        pass  # keep previous u

    print(f"k={k:03d}  u={u[0]:7.3f}  y={y[0]:7.3f}")

    elapsed = time.monotonic() - t0
    if DT - elapsed > 0:
        time.sleep(DT - elapsed)

pub.close()
sub.close()
print("Plant: done.")
