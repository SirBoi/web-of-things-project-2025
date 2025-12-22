from components.Component import Component
from random import random, choice
import time

class MembraneSwitch(Component):
    def __init__(self, simulated):
        super().__init__(simulated)
        self.delay = 1
        self.input = ""

    def run(self, break_event):
        0 # Implement later
    
    def run_simulated(self, break_event):
        options = ['1','2','3','4','5','6','7','8','9','0','*','#']

        while not break_event.is_set():
            if random() <= 0.1:
                input = choice(options)
                self.input += input
                
                print(f"\n> Component {self.id} (Membrane switch)" \
                      f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                      f"\n> Button pressed: {input}" \
                      f"\n> Current value: {self.input}")

            time.sleep(self.delay)
        
        print(f"> Component {self.id} turned off")
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors