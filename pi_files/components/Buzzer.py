import time
import json

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class Buzzer:
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated

        self.delay = 0.1
        self.PIN_NUMBER = 1

        self.value = False

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if not self.simulated:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN_NUMBER, GPIO.OUT)

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
            s = str(command_value).strip().lower()
            if s in ["1", "on", "true"]:
                self.value = True
            elif s in ["0", "off", "false"]:
                self.value = False
        except:
            pass

    def get_reading(self):
        GPIO.output(self.PIN_NUMBER, GPIO.HIGH if self.value else GPIO.LOW)
        return self.formated_data()

    def get_reading_simulated(self):
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "state": int(bool(self.value))
            }
        }