import random
import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class LcdDisplay():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1
        self.PIN_NUMBER = 1

        self.value = False
        self._last_published = None

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        while not break_event.is_set():
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