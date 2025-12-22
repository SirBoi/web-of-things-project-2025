from components.Component import Component
from random import random
import time

class WebCamera(Component):
    def __init__(self, simulated):
        super().__init__(simulated)
        self.delay = 1

    def run(self, break_event):
        0 # Implement later
    
    def run_simulated(self, break_event):
        while not break_event.is_set():
            if random() <= 0.1:
                print(f"\n> Component {self.id} (Web camera)" \
                      f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                      f"\n> Web camera recording...")

            time.sleep(self.delay)
        
        print(f"> Component {self.id} turned off")
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors