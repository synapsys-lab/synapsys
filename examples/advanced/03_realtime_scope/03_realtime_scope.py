import time
import sys

from synapsys.broker import MessageBroker, Topic, SharedMemoryBackend


def main():
    print("==== Synapsys Real-Time Headless Monitor ====")
    print("Connecting to 'sil_2dof' bus to plot values in text...")

    try:
        topic_state = Topic("sil/state", shape=(4,))
        topic_u     = Topic("sil/u",     shape=(1,))
        broker = MessageBroker()
        broker.declare_topic(topic_state)
        broker.declare_topic(topic_u)
        broker.add_backend(
            SharedMemoryBackend("sil_2dof", [topic_state, topic_u], create=False)
        )
    except Exception as e:
        print(f"Error connecting to bus. Run 02a_sil_plant.py first! ({e})")
        return

    start_time = time.time()

    try:
        while True:
            state = broker.read("sil/state")
            u     = broker.read("sil/u")[0]
            elapsed = time.time() - start_time

            sys.stdout.write(
                f"\r[t={elapsed:6.2f}s]  "
                f"x1={state[0]:7.4f}  x2={state[1]:7.4f}  "
                f"v1={state[2]:7.4f}  v2={state[3]:7.4f}  "
                f"u={u:8.4f}"
            )
            sys.stdout.flush()
            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\nMonitor stopped.")
    finally:
        broker.close()


if __name__ == "__main__":
    main()
