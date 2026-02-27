import random
import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class UltrasonicSensor:
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1
        self.TRIG_PIN_NUMBER = 1
        self.ECHO_PIN_NUMBER = 2
        self.value = 20.0

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if not self.simulated:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.TRIG_PIN_NUMBER, GPIO.OUT)
            GPIO.setup(self.ECHO_PIN_NUMBER, GPIO.IN)

        while not break_event.is_set():
            reading = self.get_reading_simulated() if self.simulated else self.get_reading()

            with counter_lock:
                dht_batch.append((self.name, json.dumps(reading), 0, True))
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
            v = float(command_value)
            if 1.0 <= v <= 30.0:
                self.value = v
        except:
            pass

    def get_reading(self):
        GPIO.output(self.TRIG_PIN_NUMBER, False)
        time.sleep(0.2)
        GPIO.output(self.TRIG_PIN_NUMBER, True)
        time.sleep(0.00001)
        GPIO.output(self.TRIG_PIN_NUMBER, False)

        pulse_start_time = time.time()
        pulse_end_time = time.time()

        max_iter = 100

        it = 0
        while GPIO.input(self.ECHO_PIN_NUMBER) == 0:
            if it > max_iter:
                return self.formated_data()
            pulse_start_time = time.time()
            it += 1

        it = 0
        while GPIO.input(self.ECHO_PIN_NUMBER) == 1:
            if it > max_iter:
                return self.formated_data()
            pulse_end_time = time.time()
            it += 1

        pulse_duration = pulse_end_time - pulse_start_time
        self.value = (pulse_duration * 34300.0) / 2.0
        return self.formated_data()

    def get_reading_simulated(self):
        self.value += (random.randrange(100) - 50) / 100.0
        if self.value < 1:
            self.value = 1
        if self.value > 30:
            self.value = 30
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "distance_cm": float(self.value)
            }
        }