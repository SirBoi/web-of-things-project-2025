import random
import time
import json
import RPi.GPIO as GPIO


class UltrasonicSensor():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1
        self.TRIG_PIN_NUMBER = 1
        self.ECHO_PIN_NUMBER = 2

        self.value = 20
        self.dht_batch = None

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        self.dht_batch = dht_batch

        if (not self.simulated):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.TRIG_PIN_NUMBER, GPIO.OUT)
            GPIO.setup(self.ECHO_PIN_NUMBER, GPIO.IN)

        while not break_event.is_set():
            with counter_lock:
                if (self.simulated):
                    dht_batch.append((self.name, json.dumps(self.get_reading_simulated()), 0, True))
                else:
                    dht_batch.append((self.name, json.dumps(self.get_reading()), 0, True))

                publish_data_counter["value"] += 1
                
                if publish_data_counter["value"] >= publish_data_limit["value"]:
                    publish_event.set()

            time.sleep(self.delay)
        
        try:
            GPIO.cleanup()
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def run_command(self, command_value):
        try:
            if (command_value >= 1 and command_value <= 30):
                self.value = command_value

                if (self.dht_batch != None):
                    self.dht_batch.append((self.name, json.dumps(self.formated_data()), 0, True))
        except:
            0

    def get_reading(self):
        GPIO.output(self.TRIG_PIN_NUMBER, False)
        time.sleep(0.2)
        GPIO.output(self.TRIG_PIN_NUMBER, True)
        time.sleep(0.00001)
        GPIO.output(self.TRIG_PIN_NUMBER, False)

        pulse_start_time = time.time()
        pulse_end_time = time.time()

        max_iter = 100

        iter = 0
        while GPIO.input(self.ECHO_PIN_NUMBER) == 0:
            if iter > max_iter:
                #self.value = 0
                return self.formated_data()
            
            pulse_start_time = time.time()
            iter += 1

        iter = 0
        while GPIO.input(self.ECHO_PIN_NUMBER) == 1:
            if iter > max_iter:
                #self.value = 0
                return self.formated_data()
            
            pulse_end_time = time.time()
            iter += 1

        pulse_duration = pulse_end_time - pulse_start_time
        self.value = (pulse_duration * 34300) / 2

        return self.formated_data()
    
    def get_reading_simulated(self):
        self.value += (random.randrange(100) - 50) / 100

        if self.value < 1: self.value = 1
        if self.value > 30: self.value = 30

        return self.formated_data()
    
    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "value": float(self.value)
        }

'''
GPIO.output(self.TRIG_PIN_NUMBER, False)
time.sleep(0.06)
GPIO.output(self.TRIG_PIN_NUMBER, True)
time.sleep(0.00001)
GPIO.output(self.TRIG_PIN_NUMBER, False)

timeout = 0.04
start_time = time.perf_counter()

while GPIO.input(self.ECHO_PIN_NUMBER) == 0:
    if time.perf_counter() - start_time > timeout:
        self.value = 0
        return self.formated_data()

pulse_start = time.perf_counter()

while GPIO.input(self.ECHO_PIN_NUMBER) == 1:
    if time.perf_counter() - pulse_start > timeout:
        self.value = 0
        return self.formated_data()

pulse_end = time.perf_counter()

pulse_duration = pulse_end - pulse_start

self.value = round((pulse_duration * 34300) / 2, 2)

return self.formated_data()
'''