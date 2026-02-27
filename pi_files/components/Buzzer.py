import random
import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class Buzzer():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1
        self.PIN_NUMBER = 1

        self.pitch = 440
        self.duration = 0.1
        self.value = False

        self._last_published = None

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if (not self.simulated):
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN_NUMBER, GPIO.OUT)

        while not break_event.is_set():
            prev = int(bool(self.value))
            reading = self.get_reading_simulated() if self.simulated else self.get_reading()
            curr = int(bool(self.value))

            with counter_lock:
                if self._last_published is None or curr != self._last_published:
                    dht_batch.append((self.name, json.dumps(reading), 0, True))
                    self._last_published = curr

                    publish_data_counter["value"] += 1
                    if publish_data_counter["value"] >= publish_data_limit["value"]:
                        publish_event.set()

            time.sleep(self.delay)

        try:
            GPIO.cleanup()
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def run_command(self, command_value):
        if (command_value in [1, 'on', True, 'True', "True"]):
            self.value = True
        elif (command_value in [0, 'off', False, 'False', "False"]):
            self.value = False

    def get_reading(self):
        # buzz only when state is ON (one pulse per loop would be noisy)
        # We buzz only on rising edge by checking _last_published here:
        if self.value and (self._last_published is None or self._last_published == 0):
            self.buzz()
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

    def buzz(self):
        period = 1.0 / self.pitch
        delay = period / 2
        cycles = int(self.duration * self.pitch)

        for _ in range(cycles):
            GPIO.output(self.PIN_NUMBER, True)
            time.sleep(delay)
            GPIO.output(self.PIN_NUMBER, False)
            time.sleep(delay)