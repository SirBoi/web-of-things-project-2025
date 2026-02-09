from components.Component import Component
from random import random
import time

class UltrasonicSensor(Component):
    def __init__(self, name, simulated):
        super().__init__(name, simulated)
        self.delay = 1
        self.distance = 10
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors
    
    def get_reading(self):
        0 # Implement later

    def get_reading_simulated(self):
        self.distance += random() * 2 - 1
            
        if self.distance < 5: self.distance = 5
        if self.distance > 15: self.distance = 15

        return {
            "name": self.name,
            "id": self.id,
            "description": "Ultrasonic sensor",
            "simulated": True,
            "timestamp": time.strftime('%H:%M:%S', time.localtime()),
            "value": float(self.distance),
            "message": f"Current value: {round(self.distance, ndigits=2)}"
        }