import time
import json

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class LedDiode:
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated

        self.delay = 0.1
        self.PIN_NUMBER = 1
        self.value = False
        self._lock_until = 0.0

    def _effective_state(self) -> bool:
        return (time.time() < self._lock_until) or bool(self.value)

    def run(
        self,
        break_event,
        dht_batch,
        publish_data_counter,
        publish_data_limit,
        counter_lock,
        publish_event,
    ):
        if not self.simulated:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN_NUMBER, GPIO.OUT)

        try:
            while not break_event.is_set():
                reading = self.get_reading_simulated() if self.simulated else self.get_reading()

                with counter_lock:
                    dht_batch.append((self.name, json.dumps(reading), 0, True))

                    publish_data_counter["value"] += 1
                    if publish_data_counter["value"] >= publish_data_limit["value"]:
                        publish_event.set()

                if time.time() >= self._lock_until:
                    self.value = False

                time.sleep(self.delay)
        finally:
            try:
                GPIO.cleanup()
            except Exception:
                pass
            print(
                f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off."
            )

    def run_command(self, command_value):
        now = time.time()
        s = str(command_value).strip()
        parts = s.split()

        if len(parts) >= 2 and parts[0].lower() == "on":
            try:
                seconds = float(parts[1])
                self._lock_until = max(self._lock_until, now + seconds)
                self.value = True
                return
            except Exception:
                pass

        if now < self._lock_until:
            if parts and parts[0].lower() == "on":
                self.value = True
            return

        if s.lower() in ["1", "on", "true"]:
            self.value = True
        elif s.lower() in ["0", "off", "false"]:
            self.value = False

    def get_reading(self):
        GPIO.output(self.PIN_NUMBER, GPIO.HIGH if self._effective_state() else GPIO.LOW)
        return self.formated_data()

    def get_reading_simulated(self):
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "state": int(self._effective_state())
            }
        }