from components.Component import Component
from random import random, choice
import time

class MembraneSwitch(Component):
    def __init__(self, name, simulated):
        super().__init__(name, simulated)
        self.delay = 1
        self.input = ""
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors
    
    def get_reading(self):
        0 # Implement later

    def get_reading_simulated(self):
        options = ['1','2','3','4','5','6','7','8','9','0','*','#']

        if random() <= 0.1:
            input = choice(options)
            self.input += input

            return {
                "name": self.name,
                "id": self.id,
                "description": "Membrane switch",
                "simulated": True,
                "timestamp": time.strftime('%H:%M:%S', time.localtime()),
                "value": input,
                "message": f"Button pressed: {input} Current value: {self.input}"
            }