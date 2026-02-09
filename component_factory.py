from components.Button import Button
from components.LedDiode import LedDiode
from components.UltrasonicSensor import UltrasonicSensor
from components.Buzzer import Buzzer
from components.MotionSensor import MotionSensor
from components.MembraneSwitch import MembraneSwitch
from components.WebCamera import WebCamera


def create_component(name, component, simulated=False):
    # Add implementation for non-simulated components

    if component["type"] == "button": return create_button(name, component, simulated)
    if component["type"] == "led_diode": return create_led_diode(name, component, simulated)
    if component["type"] == "ultrasonic_sensor": return create_ultrasonic_sensor(name, component, simulated)
    if component["type"] == "buzzer": return create_buzzer(name, component, simulated)
    if component["type"] == "motion_sensor": return create_motion_sensor(name, component, simulated)
    if component["type"] == "membrane_switch": return create_membrane_switch(name, component, simulated)
    if component["type"] == "web_camera": return create_web_camera(name, component, simulated)

    raise Exception("> ERROR: Failed to create component " + component)

def create_button(name, component, simulated):
    return Button(name, simulated)

def create_led_diode(name, component, simulated):
    return LedDiode(name, simulated)

def create_ultrasonic_sensor(name, component, simulated):
    return UltrasonicSensor(name, simulated)

def create_buzzer(name, component, simulated):
    return Buzzer(name, simulated)

def create_motion_sensor(name, component, simulated):
    return MotionSensor(name, simulated)

def create_membrane_switch(name, component, simulated):
    return MembraneSwitch(name, simulated)

def create_web_camera(name, component, simulated):
    return WebCamera(name, simulated)