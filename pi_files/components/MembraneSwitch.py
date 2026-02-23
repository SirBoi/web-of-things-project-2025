import random
import time
import json
import RPi.GPIO as GPIO


class MembraneSwitch():
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

        self.options = ['1','2','3','4','5','6','7','8','9','0','*','#']
        self.value = '1'
        self.dht_batch = None

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        self.dht_batch = dht_batch

        if (not self.simulated):
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
            with counter_lock:
                if (self.simulated):
                    dht_batch.append((self.name, json.dumps(self.get_reading_simulated()), 0, True))
                else:
                    dht_batch.append((self.name, json.dumps(self.get_reading()), 0, True))

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
            if (command_value in self.options):
                self.value = ord(str(command_value))

                if (self.dht_batch != None):
                    self.dht_batch.append((self.name, json.dumps(self.formated_data()), 0, True))
        except:
            pass

    def get_reading(self):
        self.readLine(self.PIN_R1, ["1","2","3","A"])
        self.readLine(self.PIN_R2, ["4","5","6","B"])
        self.readLine(self.PIN_R3, ["7","8","9","C"])
        self.readLine(self.PIN_R4, ["*","0","#","D"])

        return self.formated_data()
    
    def get_reading_simulated(self):
        if random.randrange(50) == 0:
            self.value = ord(str(random.choice(self.options)))

        return self.formated_data()
    
    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "value": ord(str(self.value))
        }

    def readLine(self, line, characters):
        GPIO.output(line, GPIO.HIGH)

        if(GPIO.input(self.PIN_C1) == 1):
            self.value = ord(str(characters[0]))
        if(GPIO.input(self.PIN_C2) == 1):
            self.value = ord(str(characters[1]))
        if(GPIO.input(self.PIN_C3) == 1):
            self.value = ord(str(characters[2]))
        if(GPIO.input(self.PIN_C4) == 1):
            self.value = ord(str(characters[3]))

        GPIO.output(line, GPIO.LOW)