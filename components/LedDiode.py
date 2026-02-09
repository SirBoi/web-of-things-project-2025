from components.Component import Component
from random import random
import time

class LedDiode(Component):
    def __init__(self, name, simulated):
        super().__init__(name, simulated)
        self.delay = 1
        self.is_on = False

    def execute(self, command_code):
        0 # Implement later

    def execute_simulated(self, command_code):
        if command_code == "on":
            if self.is_on: return
            
            self.is_on = True

            print(f"\n> [SIMULATED] Component {self.id} (LED)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> LED has been turned on")
        elif command_code == "off":
            if not self.is_on: return

            self.is_on = False

            print(f"\n> [SIMULATED] Component {self.id} (LED)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> LED has been turned off")
        else:
            print("\n> Unknown command.")
    
    def get_reading(self):
        0 # Implement later

    def get_reading_simulated(self):
        if random() <= 0.1:
            self.is_on = not self.is_on

        return {
            "name": self.name,
            "id": self.id,
            "description": "LED",
            "simulated": True,
            "timestamp": time.strftime('%H:%M:%S', time.localtime()),
            "value": self.is_on,
            "message": "LED has been turned on" if self.is_on else "LED has been turned off"
        }