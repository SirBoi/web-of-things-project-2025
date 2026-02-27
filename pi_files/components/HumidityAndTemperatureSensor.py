import random
import time
import json
try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class HumidityAndTemperatureSensor():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1
        self.PIN_NUMBER = 17

        self.dht = None
        self.sumCnt = None
        self.okCnt = None

        self.humidity = 0.0
        self.temperature = 0.0

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if (not self.simulated):
            self.dht = self.DHT(self.PIN_NUMBER)
            self.sumCnt = 0
            self.okCnt = 0

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

    def get_reading(self):
        if (self.dht is not None and self.sumCnt is not None and self.okCnt is not None):
            self.sumCnt += 1
            chk = self.dht.readDHT11()

            if chk == 0:
                self.okCnt += 1
                # update values only on OK read
                if self.dht.humidity != self.DHT.DHTLIB_INVALID_VALUE:
                    self.humidity = float(self.dht.humidity)
                if self.dht.temperature != self.DHT.DHTLIB_INVALID_VALUE:
                    self.temperature = float(self.dht.temperature)

        return self.formated_data()

    def get_reading_simulated(self):
        # simulated: plausible indoor values
        self.temperature += (random.randrange(100) - 50) / 200.0
        self.humidity += (random.randrange(100) - 50) / 200.0

        if self.temperature < 15: self.temperature = 15
        if self.temperature > 35: self.temperature = 35
        if self.humidity < 20: self.humidity = 20
        if self.humidity > 80: self.humidity = 80

        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "humidity_pct": float(self.humidity),
                "temperature_c": float(self.temperature)
            }
        }

    class DHT(object):
        DHTLIB_OK = 0
        DHTLIB_ERROR_CHECKSUM = -1
        DHTLIB_ERROR_TIMEOUT = -2
        DHTLIB_INVALID_VALUE = -999

        DHTLIB_DHT11_WAKEUP = 0.020
        DHTLIB_TIMEOUT = 0.0001

        humidity = 0
        temperature = 0

        def __init__(self, pin):
            self.pin = pin
            self.bits = [0, 0, 0, 0, 0]
            GPIO.setmode(GPIO.BCM)

        def readSensor(self, pin, wakeupDelay):
            mask = 0x80
            idx = 0
            self.bits = [0, 0, 0, 0, 0]
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(wakeupDelay)
            GPIO.output(pin, GPIO.HIGH)
            GPIO.setup(pin, GPIO.IN)

            loopCnt = self.DHTLIB_TIMEOUT

            t = time.time()
            while GPIO.input(pin) == GPIO.LOW:
                if (time.time() - t) > loopCnt:
                    return self.DHTLIB_ERROR_TIMEOUT

            t = time.time()
            while GPIO.input(pin) == GPIO.HIGH:
                if (time.time() - t) > loopCnt:
                    return self.DHTLIB_ERROR_TIMEOUT

            for i in range(0, 40, 1):
                t = time.time()
                while GPIO.input(pin) == GPIO.LOW:
                    if (time.time() - t) > loopCnt:
                        return self.DHTLIB_ERROR_TIMEOUT

                t = time.time()
                while GPIO.input(pin) == GPIO.HIGH:
                    if (time.time() - t) > loopCnt:
                        return self.DHTLIB_ERROR_TIMEOUT

                if (time.time() - t) > 0.00005:
                    self.bits[idx] |= mask

                mask >>= 1
                if mask == 0:
                    mask = 0x80
                    idx += 1

            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
            return self.DHTLIB_OK

        def readDHT11(self):
            rv = self.readSensor(self.pin, self.DHTLIB_DHT11_WAKEUP)
            if rv != self.DHTLIB_OK:
                self.humidity = self.DHTLIB_INVALID_VALUE
                self.temperature = self.DHTLIB_INVALID_VALUE
                return rv

            self.humidity = self.bits[0]
            self.temperature = self.bits[2] + self.bits[3] * 0.1

            sumChk = ((self.bits[0] + self.bits[1] + self.bits[2] + self.bits[3]) & 0xFF)
            if self.bits[4] != sumChk:
                return self.DHTLIB_ERROR_CHECKSUM

            return self.DHTLIB_OK