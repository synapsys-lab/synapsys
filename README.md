# Synapsys

Modern Python control systems framework with distributed multi-agent simulation.

## Features

- **MATLAB-compatible API** — `tf()`, `ss()`, `step()`, `bode()`, `feedback()`
- **LTI core** — `TransferFunction` and `StateSpace` with full operator overloading
- **Algorithms** — PID (with anti-windup), LQR
- **Multi-agent simulation** — FIPA ACL messaging, lock-step and wall-clock sync
- **Ultra-low-latency transport** — shared memory (zero-copy) and ZeroMQ (distributed)
- **Hardware abstraction** — pluggable interface for FPGA/microcontrollers

## Quick start

```python
from synapsys.api import tf, step

G = tf([1], [1, 2, 1])   # 1 / (s+1)^2
t, y = step(G)
```

## Distributed simulation

```bash
# Terminal 1
python examples/distributed/plant.py

# Terminal 2
python examples/distributed/controller.py
```

## License

MIT
