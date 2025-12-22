from components.Component import Component
from random import random
import time

class UltrasonicSensor(Component):
    def __init__(self, simulated):
        super().__init__(simulated)
        self.delay = 1
        self.distance = 10

    def run(self, break_event):
        0 # Implement later
    
    def run_simulated(self, break_event):
        while not break_event.is_set():
            self.distance += random() * 2 - 1
            
            if self.distance < 5: self.distance = 5
            if self.distance > 15: self.distance = 15

            print(f"\n> Component {self.id} (Ultrasonic sensor)" \
                  f"\n> Timestamp: {time.strftime('%H:%M:%S', time.localtime())}" \
                  f"\n> Current value: {round(self.distance, ndigits=2)}")

            time.sleep(self.delay)
        
        print(f"> Component {self.id} turned off")
    
    def execute(self, command_code):
        0 # Not needed for sensors
    
    def execute_simulated(self, command_code):
        0 # Not needed for sensors