import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class RgbLedDiode():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1

        # pick your pins
        self.PIN_R = 17
        self.PIN_G = 27
        self.PIN_B = 22

        self.r = 0
        self.g = 0
        self.b = 0

        self._last_published = None
        self._pwm_r = None
        self._pwm_g = None
        self._pwm_b = None

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if not self.simulated:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN_R, GPIO.OUT)
            GPIO.setup(self.PIN_G, GPIO.OUT)
            GPIO.setup(self.PIN_B, GPIO.OUT)

            self._pwm_r = GPIO.PWM(self.PIN_R, 500)
            self._pwm_g = GPIO.PWM(self.PIN_G, 500)
            self._pwm_b = GPIO.PWM(self.PIN_B, 500)
            self._pwm_r.start(0)
            self._pwm_g.start(0)
            self._pwm_b.start(0)

        while not break_event.is_set():
            reading = self.get_reading_simulated() if self.simulated else self.get_reading()
            curr = (int(self.r), int(self.g), int(self.b))

            with counter_lock:
                if self._last_published is None or curr != self._last_published:
                    dht_batch.append((self.name, json.dumps(reading), 0, True))
                    self._last_published = curr

                    publish_data_counter["value"] += 1
                    if publish_data_counter["value"] >= publish_data_limit["value"]:
                        publish_event.set()

            time.sleep(self.delay)

        try:
            if self._pwm_r: self._pwm_r.stop()
            if self._pwm_g: self._pwm_g.stop()
            if self._pwm_b: self._pwm_b.stop()
            GPIO.cleanup()
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def run_command(self, command_value):
        s = str(command_value).strip().lower()

        named = {
            "off": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "white": (255, 255, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
        }
        if s in named:
            self.r, self.g, self.b = named[s]
            return

        # "r,g,b"
        try:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) == 3:
                r = int(float(parts[0])); g = int(float(parts[1])); b = int(float(parts[2]))
                self.r = max(0, min(255, r))
                self.g = max(0, min(255, g))
                self.b = max(0, min(255, b))
        except:
            pass

    def get_reading(self):
        # map 0..255 -> 0..100 duty
        if self._pwm_r and self._pwm_g and self._pwm_b:
            self._pwm_r.ChangeDutyCycle(self.r * 100.0 / 255.0)
            self._pwm_g.ChangeDutyCycle(self.g * 100.0 / 255.0)
            self._pwm_b.ChangeDutyCycle(self.b * 100.0 / 255.0)
        return self.formated_data()

    def get_reading_simulated(self):
        # no random toggling by default; stays at commanded value
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "r": int(self.r),
                "g": int(self.g),
                "b": int(self.b)
            }
        }