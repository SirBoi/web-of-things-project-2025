from components.Button import Button
from components.LedDiode import LedDiode
from components.UltrasonicSensor import UltrasonicSensor
from components.Buzzer import Buzzer
from components.MotionSensor import MotionSensor
from components.MembraneSwitch import MembraneSwitch
from components.WebCamera import WebCamera
from components.FourDigitSevenSegmentDisplay import FourDigitSevenSegmentDisplay
from components.HumidityAndTemperatureSensor import HumidityAndTemperatureSensor
from components.Gyroscope import Gyroscope
from components.InfraredSensor import InfraredSensor
from components.RgbLedDiode import RgbLedDiode
from components.LcdDisplay import LcdDisplay


def create_component(component_name, component, simulated=False):
    if component["type"] == "button": return create_button(component_name, component, simulated)
    if component["type"] == "led_diode": return create_led_diode(component_name, component, simulated)
    if component["type"] == "ultrasonic_sensor": return create_ultrasonic_sensor(component_name, component, simulated)
    if component["type"] == "buzzer": return create_buzzer(component_name, component, simulated)
    if component["type"] == "motion_sensor": return create_motion_sensor(component_name, component, simulated)
    if component["type"] == "membrane_switch": return create_membrane_switch(component_name, component, simulated)
    if component["type"] == "web_camera": return create_web_camera(component_name, component, simulated)
    if component["type"] == "four_digit_seven_segment_display": return create_four_digit_seven_segment_display(component_name, component, simulated)
    if component["type"] == "humidity_and_temperature_sensor": return create_humidity_and_temperature_sensor(component_name, component, simulated)
    if component["type"] == "gyroscope": return create_gyroscope(component_name, component, simulated)
    if component["type"] == "infrared_sensor": return create_infrared_sensor(component_name, component, simulated)
    if component["type"] == "rgb_led_diode": return create_rgb_led_diode(component_name, component, simulated)
    if component["type"] == "lcd_display": return create_lcd_display(component_name, component, simulated)

    raise Exception("> ERROR: Failed to create component " + component_name)

def create_button(component_name, component, simulated):
    return Button(component_name, component['type'], simulated)

def create_led_diode(component_name, component, simulated):
    return LedDiode(component_name, component['type'], simulated)

def create_ultrasonic_sensor(component_name, component, simulated):
    return UltrasonicSensor(component_name, component['type'], simulated)

def create_buzzer(component_name, component, simulated):
    return Buzzer(component_name, component['type'], simulated)

def create_motion_sensor(component_name, component, simulated):
    return MotionSensor(component_name, component['type'], simulated)

def create_membrane_switch(component_name, component, simulated):
    return MembraneSwitch(component_name, component['type'], simulated)

def create_web_camera(component_name, component, simulated):
    return WebCamera(component_name, component['type'], simulated)

def create_four_digit_seven_segment_display(component_name, component, simulated):
    return FourDigitSevenSegmentDisplay(component_name, component['type'], simulated)

def create_humidity_and_temperature_sensor(component_name, component, simulated):
    return HumidityAndTemperatureSensor(component_name, component['type'], simulated)

def create_gyroscope(component_name, component, simulated):
    return Gyroscope(component_name, component['type'], simulated)

def create_infrared_sensor(component_name, component, simulated):
    return InfraredSensor(component_name, component['type'], simulated)

def create_rgb_led_diode(component_name, component, simulated):
    return RgbLedDiode(component_name, component['type'], simulated)

def create_lcd_display(component_name, component, simulated):
    return LcdDisplay(component_name, component['type'], simulated)