import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from component_factory import create_component
import json
import threading
import time
import paho.mqtt.publish as publish


CONFIG_FILE_PATH = "config.json"
all_components = []
started_components = {
    "button": [],
    "led_diode": [],
    "ultrasonic_sensor": [],
    "buzzer": [],
    "motion_sensor": [],
    "membrane_switch": [],
    "web_camera": []
}

dht_batch = []
publish_data_counter = {"value": 0}
publish_data_limit = {"value": 1}
counter_lock = threading.Lock()


def console_thread(break_event):
    try:
        while not break_event.is_set():
            command = input().strip().lower()

            if command == "x":
                break_event.set()
            elif len(command.split(" ")) == 2:
                component_id = command.split(" ")[0]
                command_code = command.split(" ")[1]

                for component in all_components:
                    if str(component.id) == str(component_id):
                        if component.simulated: component.execute_simulated(command_code)
                        else: component.execute(command_code)
                        break

                # Separate component types
                '''
                for led_diode in started_components["led_diode"]:
                    if led_diode.id == component_id:
                        led_diode.execute(command_code)
                        break
                for buzzer in started_components["buzzer"]:
                    if buzzer.id == component_id:
                        buzzer.execute(command_code)
                        break
                '''
            else:
                print("\n> Unknown command.")
    except:
        0

def publisher_task(event, config):
    while True:
        event.wait()

        with counter_lock:
            local_dht_batch = dht_batch.copy()
            publish_data_counter["value"] = 0
            dht_batch.clear()
        
        publish.multiple(local_dht_batch, hostname=config['device']['hostname'], port=config['device']['port'])
        print(f'Published {publish_data_limit["value"]} DHT values at {time.strftime("%H:%M:%S", time.localtime())}.')
        event.clear()

def main():
    try:
        print("> Starting PI2 device...")

        with open(CONFIG_FILE_PATH) as f:
            config = json.load(f)

        threads = []
        break_event = threading.Event()
        publish_data_limit["value"] = config['device']['publish-data-limit']

        publish_event = threading.Event()
        publisher_thread = threading.Thread(
            name="PT",
            target=publisher_task,
            args=(publish_event, config),
            daemon=True
        )
        publisher_thread.start()

        threads.append(threading.Thread(
            name="CT",
            target=console_thread,
            args=(break_event,),
            daemon=True
        ))

        if config['device']['simulated']:
            components = config['components']

            for c in components:
                try:
                    if components[c]['simulated']:
                        component = create_component(c, components[c], True)
                        all_components.append(component)
                        started_components[components[c]['type']].append(component)
                        threads.append(threading.Thread(
                            name=f"T{component.id}",
                            target=component.run_simulated,
                            # target=component.run_simulated if component.simulated else component.run,
                            args=(break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event)
                        ))
                        print(f"> [SIMULATED] Component {component.id} ({components[c]['type']}) started.")
                except Exception as e:
                    print(e)
        else:
            0 # Actual implementation
        
        for thread in threads:
            thread.start()
        
        while not break_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n> {config['device']['id']} device execution interrupted...")
    
    finally:
        break_event.set()

        for thread in threads:
            thread.join()
        
        # Implement later. Turn off power to actuators.
        '''
        if GPIO:
            GPIO.cleanup()
        '''

        print(f"\n> {config['device']['id']} device turned off")

if __name__ == "__main__":
    main()