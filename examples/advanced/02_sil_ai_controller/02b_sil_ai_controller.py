import collections

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np

from synapsys.agents import ControllerAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

# Optional: Using PyTorch to demonstrate AI integration.
# If pytorch is not installed, we fallback to a dummy logic.
try:
    import torch
    import torch.nn as nn
    HAS_TORCH = True

    # Simple dummy linear layer masquerading as our RL Model
    class DummyRLController(nn.Module):
        def __init__(self):
            super().__init__()
            self.linear = nn.Linear(1, 1)
            # Hardcode weight so it acts predictably (like a P controller)
            with torch.no_grad():
                self.linear.weight.fill_(-0.5)
                self.linear.bias.fill_(1.0)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.linear(x)

    model = DummyRLController()
    model.eval()
    print("PyTorch available! Using AI Controller inference.")

except ImportError:
    HAS_TORCH = False
    print("PyTorch not installed. Falling back to Numpy arithmetic.")

# ── Real-time data buffers (3 s window at 100 Hz) ─────────────────────────────
WINDOW = 300
_tick = [0]
t_buf: collections.deque = collections.deque(maxlen=WINDOW)
y_buf: collections.deque = collections.deque(maxlen=WINDOW)
u_buf: collections.deque = collections.deque(maxlen=WINDOW)
DT = 0.01


def ai_control_law(y: np.ndarray) -> np.ndarray:
    """The inference function run by the ControllerAgent at every tick."""
    if HAS_TORCH:
        state_tensor = torch.tensor(y, dtype=torch.float32)
        with torch.no_grad():
            u = model(state_tensor).numpy()
    else:
        u = np.array([1.0 - 0.5 * y[0]])

    # Capture samples for the real-time plot (thread-safe append on deque)
    _tick[0] += 1
    t_buf.append(_tick[0] * DT)
    y_buf.append(float(y[0]))
    u_buf.append(float(u[0]))
    return u


def main():
    print("Connecting to 'sil_bus' as client...")
    try:
        transport = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1}, create=False)
    except Exception as e:
        print(f"Error (Is the Plant Process running?): {e}")
        return

    sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=DT)
    ai_ctrl = ControllerAgent("ai_ctrl", ai_control_law, transport, sync)

    # Run agent in background — main thread drives the plot
    ai_ctrl.start(blocking=False)
    print("AI Controller running. Close the plot window to stop.")

    # ── Plot setup ─────────────────────────────────────────────────────────────
    fig, (ax_y, ax_u) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    fig.suptitle("SIL — AI Controller (real-time)", fontsize=13)

    (line_y,) = ax_y.plot([], [], color="#2563eb", lw=1.5, label="y(t) — plant output")
    ax_y.set_ylabel("y")
    ax_y.legend(loc="upper right")
    ax_y.grid(True, alpha=0.3)

    (line_u,) = ax_u.plot([], [], color="#dc2626", lw=1.5, label="u(t) — control action")
    ax_u.set_ylabel("u")
    ax_u.set_xlabel("Time (s)")
    ax_u.legend(loc="upper right")
    ax_u.grid(True, alpha=0.3)

    def update(_frame):
        if len(t_buf) < 2:
            return line_y, line_u
        t = list(t_buf)
        line_y.set_data(t, list(y_buf))
        line_u.set_data(t, list(u_buf))
        for ax in (ax_y, ax_u):
            ax.relim()
            ax.autoscale_view()
        return line_y, line_u

    ani = animation.FuncAnimation(
        fig, update, interval=100, blit=False, cache_frame_data=False
    )
    _ = ani  # keep reference so GC does not collect it

    try:
        plt.tight_layout()
        plt.show()
    finally:
        print("\nStopping AI controller.")
        ai_ctrl.stop()


if __name__ == "__main__":
    main()
