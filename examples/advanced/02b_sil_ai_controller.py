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
                
    model = DummyRLController()
    model.eval()
    print("PyTorch available! Using AI Controller inference.")
    
except ImportError:
    HAS_TORCH = False
    print("PyTorch not installed. Falling back to Numpy arithmetic.")

def ai_control_law(y: np.ndarray) -> np.ndarray:
    """The inference function run by the ControllerAgent at every tick."""
    if HAS_TORCH:
        # Convert incoming sensor signal to Tensor
        state_tensor = torch.tensor(y, dtype=torch.float32)
        with torch.no_grad():
            # Neural network predicts the optimal action u(k)
            action = model(state_tensor).numpy()
        return action
    else:
        # Simple proportional behavior
        return np.array([1.0 - 0.5 * y[0]])

def main():
    print("Connecting to 'sil_bus' as client...")
    try:
        # Create=False implies we are connecting to the Plant's memory block
        transport = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1}, create=False)
    except Exception as e:
        print(f"Error (Is the Plant Process running?): {e}")
        return

    # Run AI inference asynchronously to physical plant step loops
    sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=0.01)

    print("Starting AI ControllerAgent loop...")
    ai_ctrl = ControllerAgent("ai_ctrl", ai_control_law, transport, sync)
    
    try:
        ai_ctrl.start(blocking=True)
    except KeyboardInterrupt:
        print("\nStopping AI controller.")
        ai_ctrl.stop()

if __name__ == "__main__":
    main()
