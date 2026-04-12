import time
import sys
from synapsys.transport import SharedMemoryTransport

def main():
    print("==== Synapsys Real-Time Headless Monitor ====")
    print("Connecting to 'sil_bus' to plot values in text...")
    
    try:
        monitor = SharedMemoryTransport("sil_bus", {"y": 1, "u": 1}, create=False)
    except Exception as e:
        print(f"Error connecting to bus. Run 02a_sil_plant.py first! ({e})")
        return
        
    start_time = time.time()
    
    try:
        # We run the loop much faster to 'sample' the bus
        # A true GUI (like PyQtGraph) would run this in a QTimer or update loop.
        while True:
            y = monitor.read("y")[0]
            u = monitor.read("u")[0]
            elapsed = time.time() - start_time
            
            sys.stdout.write(f"\r[t={elapsed:6.2f}s] Sensor y(t): {y:8.4f} | Inference u(t): {u:8.4f}")
            sys.stdout.flush()
            time.sleep(0.05) 
            
    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")

if __name__ == "__main__":
    main()
