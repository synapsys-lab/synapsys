import time
import numpy as np
from synapsys.api import tf, c2d
from synapsys.agents import PlantAgent, SyncEngine, SyncMode
from synapsys.transport import SharedMemoryTransport

def main():
    print("Initializing SIL Plant Process (Physics Engine)...")

    # 1. Mathematical model -> Discretised for digital simulation at 100 Hz
    plant_c = tf([10], [1, 3, 10])  # G(s) = 10 / (s^2 + 3s + 10)
    plant_d = c2d(plant_c, dt=0.01)
    
    # 2. Set up Transport Bus (This process OWNS the memory block)
    print("Allocating Shared Memory Bus 'sil_bus'...")
    bus_server = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1}, create=True)
    
    # Needs its own transport handle specifically for the agent loop
    agent_transport = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1})
    
    # 3. Synchronisation configuration
    sync = SyncEngine(mode=SyncMode.WALL_CLOCK, dt=0.01)

    print("Starting physics PlantAgent...")
    plant_agent = PlantAgent("physics_plant", plant_d, agent_transport, sync)
    
    try:
        plant_agent.start(blocking=True)
    except KeyboardInterrupt:
        print("\nStopping plant simulation.")
        plant_agent.stop()
        bus_server.close()

if __name__ == "__main__":
    main()
