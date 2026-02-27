import json
import threading
import time
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import os
import socket
import uuid
from component_factory import create_component



all_components = []

dht_batch = []
publish_data_counter = {"value": 0}
publish_data_limit = {"value": 1}
counter_lock = threading.Lock()

DISABLE_WEBC = os.environ.get("DISABLE_WEBC", "0").strip() in ["1", "true", "TRUE", "yes", "YES"]



def console_task(break_event):
    try:
        while not break_event.is_set():
            raw = input().strip()
            if not raw:
                continue

            cmdline = raw.strip()
            if cmdline.lower() == "x":
                break_event.set()
                continue

            parts = cmdline.split()
            if len(parts) >= 2:
                component_name = parts[0]
                command_value = " ".join(parts[1:])

                for component in all_components:
                    if str(component.name).lower() == str(component_name).lower():
                        component.run_command(command_value)
                        break
            else:
                print("\n> Unknown command.")
    except:
        print("\n> Unknown command.")

def publisher_task(event, hostname, port):
    while True:
        event.wait(timeout=0.5)

        with counter_lock:
            local = dht_batch.copy()
            dht_batch.clear()
            publish_data_counter["value"] = 0

        if local:
            publish.multiple(local, hostname=hostname, port=port)

        event.clear()

def command_listener_task(break_event, hostname, port):
    def on_connect(client, userdata, flags, rc):
        print(f"> CMD listener connected rc={rc}")
        client.subscribe("CMD/#")

    def on_disconnect(client, userdata, rc):
        print(f"> CMD listener disconnected rc={rc}")

    def on_message(client, userdata, msg):
        try:
            parts = msg.topic.split("/")
            if len(parts) != 2:
                return
            target = parts[1].strip()
            payload = msg.payload.decode("utf-8", errors="ignore")

            for component in all_components:
                if str(component.name).upper() == str(target).upper():
                    component.run_command(payload)
                    return
        except Exception as e:
            print(f"> Command listener error: {e}")

    client_id = f"cmd-listener-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
    client = mqtt.Client(client_id=client_id, clean_session=True)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    client.reconnect_delay_set(min_delay=1, max_delay=10)

    client.connect(hostname, port, 60)
    client.loop_start()

    try:
        while not break_event.is_set():
            time.sleep(0.1)
    finally:
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass



def main():
    threads = []
    break_event = threading.Event()

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        publish_data_limit["value"] = config["publish-data-limit"]
        devices = config["devices"]

        active_devices = [(name, dev) for name, dev in devices.items() if dev.get("used")]
        if not active_devices:
            raise Exception("No active device found in config (set at least one 'used': true).")

        print("> Active devices:", ", ".join([name for name, _ in active_devices]))
        if DISABLE_WEBC:
            print("> DISABLE_WEBC=1 -> WEBC component will be skipped (prevents webcam conflicts).")

        publish_event = threading.Event()
        publisher_thread = threading.Thread(
            name="PT",
            target=publisher_task,
            args=(publish_event, config["hostname"], config["port"]),
            daemon=True,
        )

        threads.append(threading.Thread(name="CT", target=console_task, args=(break_event,), daemon=True))
        threads.append(threading.Thread(name="CMD", target=command_listener_task, args=(break_event, config["hostname"], config["port"]), daemon=True))

        for device_name, device in active_devices:
            print(f"> Loading components for {device_name}...")

            for component_name in device:
                try:
                    if component_name == "used":
                        continue

                    if DISABLE_WEBC and component_name.upper() == "WEBC":
                        print(f"> [{device_name}] Component WEBC skipped (DISABLE_WEBC=1).")
                        continue

                    component_cfg = device[component_name]

                    c = create_component(component_name, component_cfg, simulated=bool(component_cfg.get("simulated")))
                    all_components.append(c)

                    threads.append(
                        threading.Thread(
                            name=f"T-{device_name}-{c.name}",
                            target=c.run,
                            args=(break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event),
                            daemon=True,
                        )
                    )

                    print(f"> [{device_name}] {'SIMULATED ' if c.simulated else ''}Component {c.name} ({component_cfg['type']}) started.")
                except Exception as e:
                    print(e)

        publisher_thread.start()
        for t in threads:
            t.start()

        while not break_event.is_set():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n> Device execution interrupted. Shutting down...")
    finally:
        break_event.set()
        for t in threads:
            try:
                t.join()
            except:
                pass
        print("\n> Device turned off.")



if __name__ == "__main__":
    main()