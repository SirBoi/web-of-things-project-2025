import random
import time
import json

try:
    import tm1637  # common library name
except Exception:
    tm1637 = None


class FourDigitSevenSegmentDisplay():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1

        # For TM1637 you typically need CLK and DIO pins
        self.CLK = 21
        self.DIO = 20
        self._disp = None

        self.value = 0  # 0..9999
        self._last_published = None

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if not self.simulated:
            self._init_display()

        while not break_event.is_set():
            reading = self.get_reading_simulated() if self.simulated else self.get_reading()
            curr = int(self.value)

            with counter_lock:
                if self._last_published is None or curr != self._last_published:
                    dht_batch.append((self.name, json.dumps(reading), 0, True))
                    self._last_published = curr

                    publish_data_counter["value"] += 1
                    if publish_data_counter["value"] >= publish_data_limit["value"]:
                        publish_event.set()

            time.sleep(self.delay)

        try:
            if self._disp:
                self._disp.show("    ")
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def _init_display(self):
        if tm1637 is None:
            print(f"> WARNING [{self.name}]: tm1637 library not found; running simulated.")
            self.simulated = True
            return
        try:
            self._disp = tm1637.TM1637(clk=self.CLK, dio=self.DIO)
            self._disp.brightness(2)
        except Exception as e:
            print(f"> WARNING [{self.name}]: TM1637 init failed ({e}); running simulated.")
            self.simulated = True

    def run_command(self, command_value):
        try:
            v = int(float(command_value))
            if v < 0: v = 0
            if v > 9999: v = 9999
            self.value = v
        except:
            pass

    def get_reading(self):
        if self._disp:
            s = f"{int(self.value):4d}"[-4:]
            try:
                self._disp.show(s)
            except:
                pass
        return self.formated_data()

    def get_reading_simulated(self):
        # If you want it to “do something” in sim:
        if random.randrange(200) == 0:
            self.value = random.randrange(0, 10000)
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "value": int(self.value)
            }
        }