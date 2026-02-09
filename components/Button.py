from components.Component import Component
from random import random
import time

class Button(Component):
    def __init__(self, name, simulated):
        super().__init__(name, simulated)
        self.delay = 1
        self.is_pressed = False
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors
    
    def get_reading(self):
        0 # Implement later

    def get_reading_simulated(self):
        if random() <= 0.1:
            self.is_pressed = not self.is_pressed

        return {
            "name": self.name,
            "id": self.id,
            "description": "Button",
            "simulated": True,
            "timestamp": time.strftime('%H:%M:%S', time.localtime()),
            "value": self.is_pressed,
            "message": "Button pressed" if self.is_pressed else "Button released"
        }