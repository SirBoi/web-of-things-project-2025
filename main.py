from component_factory import create_component
import json
import threading
import time


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

def main():
    try:
        print("> Starting PI1 device...")

        with open(CONFIG_FILE_PATH) as f:
            config = json.load(f)

        threads = []
        break_event = threading.Event()

        threads.append(threading.Thread(
            name="CT",
            target=console_thread,
            args=(break_event,),
            daemon=True
        ))

        if config['debug']:
            components = config['components']

            for c in components:
                try:
                    if components[c]['simulated']:
                        component = create_component(components[c], simulated=True)
                        all_components.append(component)
                        started_components[components[c]['type']].append(component)
                        threads.append(threading.Thread(
                            name=f"T{component.id}",
                            target=component.run_simulated if component.simulated else component.run,
                            args=(break_event,)
                        ))
                        print(f"> Component {component.id} ({components[c]['type']}) started.")
                except Exception as e:
                    print(e)
        else:
            0 # Actual implementation
        
        for thread in threads:
            thread.start()
        while not break_event.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n> PI1 device execution interrupted...")
    
    finally:
        break_event.set()


        for thread in threads:
            thread.join()
        
        # Implement later. Turn off power to actuators.
        '''
        if GPIO:
            GPIO.cleanup()
        '''

        print("\n> PI1 device turned off")

if __name__ == "__main__":
    main()