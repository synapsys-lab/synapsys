"""Plant process — 2-DOF mass-spring-damper.

Topology
--------
  [k]         [k]
──/\/\/──[m1]──/\/\/──[m2]──→ F(t)
  [c]                  [c]

State:  x = [x1, x2, v1, v2]  (positions + velocities of m1, m2)
Input:  F  (force on m2 via the coupling spring)
Output: full state vector written to the broker bus every 10 ms.

Run FIRST, then start 02b_sil_ai_controller.py in a second terminal.
"""

import numpy as np

from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.api import c2d, ss
from synapsys.broker import MessageBroker, SharedMemoryBackend, Topic
from synapsys.utils import StateEquations

# ── System parameters ─────────────────────────────────────────────────────────
M, C_DAMP, K_SPR = 1.0, 0.1, 2.0
DT = 0.01  # 100 Hz

# ── 2-DOF model via named equations ──────────────────────────────────────────
eqs = (
    StateEquations(states=["x1", "x2", "v1", "v2"], inputs=["F"])
    .eq("x1", v1=1)
    .eq("x2", v2=1)
    .eq("v1", x1=-2 * K_SPR / M, x2=K_SPR / M, v1=-C_DAMP / M)
    .eq("v2", x1=K_SPR / M, x2=-2 * K_SPR / M, v2=-C_DAMP / M, F=K_SPR / M)
)

plant_c = ss(eqs.A, eqs.B, np.eye(4), np.zeros((4, 1)))
plant_d = c2d(plant_c, dt=DT)

print("=" * 58)
print("  2-DOF Mass-Spring-Damper — SIL Plant")
print("=" * 58)
print(f"  m={M} kg   c={C_DAMP} N·s/m   k={K_SPR} N/m   Ts={DT * 1000:.0f} ms")
print(f"  n_states={plant_d.n_states}  stable={plant_d.is_stable()}")
print("=" * 58)

# ── Broker setup ──────────────────────────────────────────────────────────────
topic_state = Topic("sil/state", shape=(4,))
topic_u = Topic("sil/u", shape=(1,))

broker = MessageBroker()
broker.declare_topic(topic_state)
broker.declare_topic(topic_u)
broker.add_backend(SharedMemoryBackend("sil_2dof", [topic_state, topic_u], create=True))
broker.publish("sil/state", np.zeros(4))
broker.publish("sil/u", np.zeros(1))

# ── Agent ─────────────────────────────────────────────────────────────────────
sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=DT)
plant = PlantAgent(
    "2dof_plant",
    plant_d,
    None,
    sync,
    channel_y="sil/state",
    channel_u="sil/u",
    broker=broker,
)

print("\nStarting PlantAgent — waiting for AI controller…")
print("Press Ctrl+C to stop.\n")
try:
    plant.start(blocking=True)
except KeyboardInterrupt:
    print("\nStopping plant.")
    plant.stop()
finally:
    broker.close()
