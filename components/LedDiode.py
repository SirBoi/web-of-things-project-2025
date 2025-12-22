from components.Component import Component
from random import random
import time

class LedDiode(Component):
    def __init__(self, simulated):
        super().__init__(simulated)
        self.delay = 1
        self.is_on = False

    def run(self, break_event):
        0 # Not needed for actuators

    def run_simulated(self, break_event):
        0 # Not needed for actuators
    
    def execute(self, command_code):
        0 # Implement later

    def execute_simulated(self, command_code):
        if command_code == "on":
            if self.is_on: return
            
            self.is_on = True

            print(f"\n> Component {self.id} (LED Diode)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> LED Diode has been turned on")
        elif command_code == "off":
            if not self.is_on: return

            self.is_on = False

            print(f"\n> Component {self.id} (LED Diode)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> LED Diode has been turned off")
        else:
            print("\n> Unknown command.")