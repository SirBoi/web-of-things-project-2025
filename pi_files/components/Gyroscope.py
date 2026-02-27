import random
import time
import json

try:
    from smbus2 import SMBus
except Exception:
    SMBus = None


class Gyroscope():
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated
        self.delay = 0.1

        # MPU6050 defaults
        self.bus_id = 1
        self.addr = 0x68
        self._bus = None
        self._warned = False

        # values (deg/s-ish)
        self.gx = 0.0
        self.gy = 0.0
        self.gz = 0.0

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        # init real device if requested
        if not self.simulated:
            self._init_mpu()

        while not break_event.is_set():
            with counter_lock:
                reading = self.get_reading_simulated() if self.simulated else self.get_reading()
                dht_batch.append((self.name, json.dumps(reading), 0, True))

                publish_data_counter["value"] += 1
                if publish_data_counter["value"] >= publish_data_limit["value"]:
                    publish_event.set()

            time.sleep(self.delay)

        try:
            if self._bus:
                self._bus.close()
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def run_command(self, command_value):
        try:
            parts = str(command_value).strip().split()
            if len(parts) == 1:
                v = float(parts[0])
                self.gx = v
                self.gy = 0.0
                self.gz = 0.0
            elif len(parts) == 3:
                self.gx = float(parts[0])
                self.gy = float(parts[1])
                self.gz = float(parts[2])
        except:
            pass

    def _init_mpu(self):
        if SMBus is None:
            self._warn_once("smbus2 not installed; gyroscope running in simulated mode.")
            self.simulated = True
            return

        try:
            self._bus = SMBus(self.bus_id)
            # Wake up MPU6050 (PWR_MGMT_1 = 0x6B, set to 0)
            self._bus.write_byte_data(self.addr, 0x6B, 0x00)
            time.sleep(0.1)
        except Exception as e:
            self._warn_once(f"MPU init failed ({e}); gyroscope running in simulated mode.")
            self.simulated = True

    def _read_i16(self, reg):
        hi = self._bus.read_byte_data(self.addr, reg)
        lo = self._bus.read_byte_data(self.addr, reg + 1)
        val = (hi << 8) | lo
        if val >= 0x8000:
            val -= 0x10000
        return val

    def get_reading(self):
        # If we failed init, we’ll be simulated anyway.
        if self._bus is None:
            return self.get_reading_simulated()

        try:
            # Gyro raw regs: 0x43..0x48
            raw_gx = self._read_i16(0x43)
            raw_gy = self._read_i16(0x45)
            raw_gz = self._read_i16(0x47)

            # default sensitivity: 131 LSB/(deg/s) at ±250 dps
            self.gx = raw_gx / 131.0
            self.gy = raw_gy / 131.0
            self.gz = raw_gz / 131.0
        except Exception as e:
            self._warn_once(f"MPU read failed ({e}); continuing with last values.")

        return self.formated_data()

    def get_reading_simulated(self):
        # gentle drift
        self.gx += (random.randrange(100) - 50) / 400.0
        self.gy += (random.randrange(100) - 50) / 400.0
        self.gz += (random.randrange(100) - 50) / 400.0
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "gx": float(self.gx),
                "gy": float(self.gy),
                "gz": float(self.gz)
            }
        }

    def _warn_once(self, msg):
        if not self._warned:
            print(f"> WARNING [{self.name}]: {msg}")
            self._warned = True