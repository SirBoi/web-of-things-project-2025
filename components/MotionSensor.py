from components.Component import Component
from random import random
import time

class MotionSensor(Component):
    def __init__(self, name, simulated):
        super().__init__(name, simulated)
        self.delay = 1
        self.value = False
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors

    def get_reading(self):
        0 # Implement later

    def get_reading_simulated(self):
        if random() <= 0.1:
            self.value = not self.value

        return {
            "name": self.name,
            "id": self.id,
            "description": "Motion sensor",
            "simulated": True,
            "timestamp": time.strftime('%H:%M:%S', time.localtime()),
            "value": float(self.value),
            "message": "Motion detected" if self.value else "Motion not detected"
        }