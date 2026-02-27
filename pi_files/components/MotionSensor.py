import random
import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class MotionSensor():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1
        self.PIN_NUMBER = 1

        self.value = False
        self.dht_batch = None

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        self.dht_batch = dht_batch

        if (not self.simulated):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN_NUMBER, GPIO.IN)
            GPIO.add_event_detect(self.PIN_NUMBER, GPIO.BOTH, callback=self.handle_motion, bouncetime=100)

        while not break_event.is_set():
            with counter_lock:
                reading = self.get_reading_simulated() if self.simulated else self.get_reading()
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
            if command_value in [1, "1"]:
                self.value = True
            elif command_value in [0, "0"]:
                self.value = False

            if self.dht_batch is not None:
                self.dht_batch.append((self.name, json.dumps(self.formated_data()), 0, True))
        except:
            pass

    def get_reading(self):
        return self.formated_data()

    def get_reading_simulated(self):
        if random.randrange(50) == 0:
            self.value = not self.value
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "state": int(bool(self.value))
            }
        }

    def handle_motion(self, channel):
        self.value = (GPIO.input(self.PIN_NUMBER) == GPIO.HIGH)