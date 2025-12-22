from components.Button import Button
from components.LedDiode import LedDiode
from components.UltrasonicSensor import UltrasonicSensor
from components.Buzzer import Buzzer
from components.MotionSensor import MotionSensor
from components.MembraneSwitch import MembraneSwitch
from components.WebCamera import WebCamera


def create_component(component, simulated=False):
    # Add implementation for non-simulated components

    if component["type"] == "button": return create_button(component, simulated)
    if component["type"] == "led_diode": return create_led_diode(component, simulated)
    if component["type"] == "ultrasonic_sensor": return create_ultrasonic_sensor(component, simulated)
    if component["type"] == "buzzer": return create_buzzer(component, simulated)
    if component["type"] == "motion_sensor": return create_motion_sensor(component, simulated)
    if component["type"] == "membrane_switch": return create_membrane_switch(component, simulated)
    if component["type"] == "web_camera": return create_web_camera(component, simulated)

    raise Exception("> ERROR: Failed to create component " + component)

def create_button(component, simulated):
    return Button(simulated)

def create_led_diode(component, simulated):
    return LedDiode(simulated)

def create_ultrasonic_sensor(component, simulated):
    return UltrasonicSensor(simulated)

def create_buzzer(component, simulated):
    return Buzzer(simulated)

def create_motion_sensor(component, simulated):
    return MotionSensor(simulated)

def create_membrane_switch(component, simulated):
    return MembraneSwitch(simulated)

def create_web_camera(component, simulated):
    return WebCamera(simulated)