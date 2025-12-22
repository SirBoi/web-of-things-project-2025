from components.Component import Component
from random import random
import time

class Buzzer(Component):
    def __init__(self, simulated):
        super().__init__(simulated)
        self.delay = 1
        self.is_buzzing = False

    def run(self, break_event):
        0 # Not needed for actuators
    
    def run_simulated(self, break_event):
        0 # Not needed for actuators
    
    def execute(self, command_code):
        0 # Implement later

    def execute_simulated(self, command_code):
        if command_code == "on":
            if self.is_buzzing: return

            self.is_buzzing = True

            print(f"\n> Component {self.id} (Buzzer)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> Buzzer has started buzzing")
        elif command_code == "off":
            if not self.is_buzzing: return

            self.is_buzzing = False

            print(f"\n> Component {self.id} (Buzzer)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> Buzzer has stopped buzzing")
        else:
            print("\n> Unknown command.")