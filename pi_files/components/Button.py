import time
import json
import threading
import socket
import uuid
import paho.mqtt.client as mqtt

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    from mock_gpio import GPIO


class Button:
    def __init__(self, name, type, simulated):
        self.name = name
        self.type = type
        self.simulated = simulated

        self.delay = 0.1
        self.PIN_NUMBER = 1

        self.value = False
        self._mqtt = None
        self._mqtt_lock = threading.Lock()
        self._broker_host = "localhost"
        self._broker_port = 1883

    def run(self, break_event, dht_batch, publish_data_counter, publish_data_limit, counter_lock, publish_event):
        if not self.simulated:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.PIN_NUMBER, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._start_mqtt()

        while not break_event.is_set():
            reading = self.get_reading_simulated() if self.simulated else self.get_reading()

            with counter_lock:
                dht_batch.append((self.name, json.dumps(reading), 0, True))
                publish_data_counter["value"] += 1
                if publish_data_counter["value"] >= publish_data_limit["value"]:
                    publish_event.set()

            time.sleep(self.delay)

        try:
            if self._mqtt:
                try:
                    self._mqtt.loop_stop()
                    self._mqtt.disconnect()
                except:
                    pass
            GPIO.cleanup()
        finally:
            print(f"> {'SIMULATED ' if self.simulated else ''}Component {self.name} ({self.__class__.__name__}) turned off.")

    def _start_mqtt(self):
        try:
            client_id = f"{self.name.lower()}-pub-{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
            self._mqtt = mqtt.Client(client_id=client_id, clean_session=True)
            self._mqtt.reconnect_delay_set(min_delay=1, max_delay=10)
            self._mqtt.connect(self._broker_host, self._broker_port, 60)
            self._mqtt.loop_start()
        except Exception as e:
            print(f"> WARNING [{self.name}]: MQTT client init failed: {e}")
            self._mqtt = None

    def _publish_cmd(self, target, command):
        if not self._mqtt:
            return
        try:
            with self._mqtt_lock:
                self._mqtt.publish(f"CMD/{str(target).upper()}", payload=str(command), qos=0, retain=False)
        except:
            pass

    def run_command(self, command_value):
        try:
            s = str(command_value).strip().lower()
            parts = s.split()
            if len(parts) >= 1:
                if parts[0] in ["1", "on", "true"]:
                    self.value = True
                elif parts[0] in ["0", "off", "false"]:
                    self.value = False
        except:
            pass

    def get_reading(self):
        try:
            pin_val = GPIO.input(self.PIN_NUMBER)
            self.value = (pin_val == GPIO.LOW)
        except:
            pass
        return self.formated_data()

    def get_reading_simulated(self):
        return self.formated_data()

    def formated_data(self):
        return {
            "name": self.name,
            "type": self.type,
            "fields": {
                "state": int(bool(self.value))
            }
        }