from components.Component import Component
from random import random
import time

class Button(Component):
    def __init__(self, simulated):
        super().__init__(simulated)
        self.delay = 1
        self.is_pressed = False

    def run(self, break_event):
        0 # Implement later
    
    def run_simulated(self, break_event):
        while not break_event.is_set():
            if random() <= 0.1:
                self.is_pressed = not self.is_pressed

                print(f"\n> Component {self.id} (Button)" \
                      f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                      f"\n> Current value: {'pressed' if self.is_pressed else 'released'}")

            time.sleep(self.delay)
        
        print(f"> Component {self.id} turned off")
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors