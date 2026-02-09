from components.Component import Component
from random import random
import time

class Buzzer(Component):
    def __init__(self, name, simulated):
        super().__init__(name, simulated)
        self.delay = 1
        self.is_buzzing = False
    
    def execute(self, command_code):
        0 # Implement later

    def execute_simulated(self, command_code):
        if command_code == "on":
            if self.is_buzzing: return

            self.is_buzzing = True

            print(f"\n> [SIMULATED] Component {self.id} (Buzzer)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> Buzzer has started buzzing")
        elif command_code == "off":
            if not self.is_buzzing: return

            self.is_buzzing = False

            print(f"\n> [SIMULATED] Component {self.id} (Buzzer)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> Buzzer has stopped buzzing")
        else:
            print("\n> Unknown command.")
    
    def get_reading(self):
        0 # Implement later

    def get_reading_simulated(self):
        if random() <= 0.1:
            self.is_buzzing = not self.is_buzzing

        return {
            "name": self.name,
            "id": self.id,
            "description": "Buzzer",
            "simulated": True,
            "timestamp": time.strftime('%H:%M:%S', time.localtime()),
            "value": self.is_buzzing,
            "message": "Buzzer has started buzzing" if self.is_pressed else "Buzzer has stopped buzzing"
        }