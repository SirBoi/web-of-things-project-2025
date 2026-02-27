import json
import threading
import time
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import os
from component_factory import create_component



all_components = []

dht_batch = []
publish_data_counter = {"value": 0}
publish_data_limit = {"value": 1}
counter_lock = threading.Lock()



def console_task(break_event):
    try:
        while not break_event.is_set():
            command = input().strip().lower()

            if command == "x":
                break_event.set()
            elif len(command.split(" ")) == 2:
                component_name = command.split(" ")[0]
                command_value = command.split(" ")[1]

                for component in all_components:
                    if str(component.name) == str(component_name):
                        component.run_command(command_value)
                        break
            else:
                print("\n> Unknown command.")
    except:
        print("\n> Unknown command.")

def publisher_task(event, hostname, port):
    while True:
        event.wait()

        with counter_lock:
            local_dht_batch = dht_batch.copy()
            publish_data_counter["value"] = 0
            dht_batch.clear()
        
        publish.multiple(local_dht_batch, hostname=hostname, port=port)
        print(f'Published {publish_data_limit["value"]} DHT values at {time.strftime("%H:%M:%S", time.localtime())}.')
        event.clear()

def command_listener_task(break_event, hostname, port):
    def on_connect(client, userdata, flags, rc):
        client.subscribe("CMD/#")

    def on_message(client, userdata, msg):
        try:
            parts = msg.topic.split("/")
            if len(parts) != 2:
                return
            target = parts[1].strip()

            payload = msg.payload.decode("utf-8")

            for component in all_components:
                if str(component.name).upper() == str(target).upper():
                    try:
                        component.run_command(payload)
                    except Exception as e:
                        print(f"> Command execution error for {target}: {e}")
                    return
        except Exception as e:
            print(f"> Command listener error: {e}")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

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
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        publish_data_limit["value"] = config["publish-data-limit"]
        devices = config["devices"]

        active_devices = []
        for device_name, device in devices.items():
            if device.get("used"):
                active_devices.append((device_name, device))

        if not active_devices:
            raise Exception("No active device found in config (set at least one 'used': true).")

        print("> Active devices:", ", ".join([name for name, _ in active_devices]))

        threads = []

        publish_event = threading.Event()
        publisher_thread = threading.Thread(
            name="PT",
            target=publisher_task,
            args=(publish_event, config['hostname'], config['port']),
            daemon=True
        )

        break_event = threading.Event()
        threads.append(threading.Thread(
            name="CT",
            target=console_task,
            args=(break_event,),
            daemon=True
        ))

        threads.append(threading.Thread(
            name="CMD",
            target=command_listener_task,
            args=(break_event, config["hostname"], config["port"]),
            daemon=True
        ))

        for device_name, device in active_devices:
            print(f"> Loading components for {device_name}...")

            for component_name in device:
                try:
                    if component_name == 'used':
                        continue

                    component_cfg = device[component_name]

                    if component_cfg.get('simulated'):
                        c = create_component(component_name, component_cfg, simulated=True)
                    else:
                        c = create_component(component_name, component_cfg, simulated=False)

                    all_components.append(c)

                    threads.append(threading.Thread(
                        name=f"T-{device_name}-{c.name}",
                        target=c.run,
                        args=(break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event),
                        daemon=True
                    ))

                    print(f"> [{device_name}] {'SIMULATED ' if c.simulated else ''}Component {c.name} ({component_cfg['type']}) started.")
                except Exception as e:
                    print(e)

        publisher_thread.start()

        for thread in threads:
            thread.start()

        while not break_event.is_set():
            time.sleep(0.1)

    except KeyboardInterrupt:
        print(f"\n> Device execution interrupted. Shutting down...")

    finally:
        break_event.set()

        for thread in threads:
            try:
                thread.join()
            except:
                pass

        print(f"\n> Device turned off.")

if __name__ == "__main__":
    main()