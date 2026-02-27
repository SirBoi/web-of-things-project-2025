import random
import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO
try:
    from RPLCD.i2c import CharLCD
except Exception:
    CharLCD = None


class LcdDisplay():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1

        self.text = ""
        self._last_published_text = None

        self._lcd = None

        self.I2C_ADDRESS = 0x27
        self.COLS = 16
        self.ROWS = 2

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if not self.simulated:
            self._init_lcd()

        while not break_event.is_set():
            reading = self.get_reading_simulated() if self.simulated else self.get_reading()
            current_text = self.text

            with counter_lock:
                if self._last_published_text is None or current_text != self._last_published_text:
                    dht_batch.append((self.name, json.dumps(reading), 0, True))
                    self._last_published_text = current_text

                    publish_data_counter["value"] += 1
                    if publish_data_counter["value"] >= publish_data_limit["value"]:
                        publish_event.set()

            time.sleep(self.delay)

        try:
            if self._lcd:
                try:
                    self._lcd.clear()
                except:
                    pass
            GPIO.cleanup()
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def _init_lcd(self):
        if CharLCD is None:
            print(f"> WARNING [{self.name}]: RPLCD not installed; LCD will not be written, but data will still publish.")
            return
        try:
            self._lcd = CharLCD('PCF8574', self.I2C_ADDRESS, cols=self.COLS, rows=self.ROWS)
            self._lcd.clear()
        except Exception as e:
            print(f"> WARNING [{self.name}]: LCD init failed ({e}); continuing without hardware output.")
            self._lcd = None

    def run_command(self, command_value):
        try:
            self.text = str(command_value)
        except:
            pass

    def get_reading(self):
        if self._lcd:
            try:
                self._lcd.clear()

                s = (self.text or "")
                line1 = s[:self.COLS]
                line2 = s[self.COLS:self.COLS * 2]

                self._lcd.write_string(line1)
                if self.ROWS > 1:
                    self._lcd.crlf()
                    self._lcd.write_string(line2)
            except Exception as e:
                print(f"> WARNING [{self.name}]: LCD write failed ({e})")

        return self.formated_data()

    def get_reading_simulated(self):
        if not self.text and random.randrange(200) == 0:
            self.text = f"Sim {time.strftime('%H:%M:%S')}"
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "text": str(self.text)
            }
        }