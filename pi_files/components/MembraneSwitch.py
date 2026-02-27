import random
import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class MembraneSwitch:
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1

        self.PIN_R1 = 1
        self.PIN_R2 = 2
        self.PIN_R3 = 3
        self.PIN_R4 = 4
        self.PIN_C1 = 5
        self.PIN_C2 = 6
        self.PIN_C3 = 7
        self.PIN_C4 = 8

        self.options = ['1','2','3','4','5','6','7','8','9','0','*','#','A','B','C','D']
        self.value = '1'

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if not self.simulated:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)

            GPIO.setup(self.PIN_R1, GPIO.OUT)
            GPIO.setup(self.PIN_R2, GPIO.OUT)
            GPIO.setup(self.PIN_R3, GPIO.OUT)
            GPIO.setup(self.PIN_R4, GPIO.OUT)
            GPIO.setup(self.PIN_C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.PIN_C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.PIN_C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            GPIO.setup(self.PIN_C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

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
            s = str(command_value).strip()
            if s in self.options:
                self.value = s
        except:
            pass

    def get_reading(self):
        self.readLine(self.PIN_R1, ["1","2","3","A"])
        self.readLine(self.PIN_R2, ["4","5","6","B"])
        self.readLine(self.PIN_R3, ["7","8","9","C"])
        self.readLine(self.PIN_R4, ["*","0","#","D"])
        return self.formated_data()

    def get_reading_simulated(self):
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "key_code": int(ord(self.value))
            }
        }

    def readLine(self, line, characters):
        GPIO.output(line, GPIO.HIGH)

        if GPIO.input(self.PIN_C1) == 1:
            self.value = str(characters[0])
        if GPIO.input(self.PIN_C2) == 1:
            self.value = str(characters[1])
        if GPIO.input(self.PIN_C3) == 1:
            self.value = str(characters[2])
        if GPIO.input(self.PIN_C4) == 1:
            self.value = str(characters[3])

        GPIO.output(line, GPIO.LOW)