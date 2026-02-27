from flask import Flask, jsonify, request, Response
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import WriteOptions
import paho.mqtt.client as mqtt
import json
import cv2
import time
import threading
import atexit
import socket
from collections import deque

app = Flask(__name__)

token = "F9xWKba1m3XN3Ds69w6eW0F9F18c3i9t5bicNXdfTB4Vv3UFvPkNN7nY2IwjfoOpPi1PoObF9g1-klq6dDQl3Q=="
org = "FTN"
url = "http://localhost:8086"
bucket = "example_db"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)

write_api = influxdb_client.write_api(
    write_options=WriteOptions(batch_size=500, flush_interval=500, jitter_interval=0, retry_interval=5000)
)

MQTT_HOST = "localhost"
MQTT_PORT = 1883

TOPICS = [
    "DS1", "DL", "DUS1", "DB", "DPIR1", "DMS", "DS2", "DUS2", "DPIR2", "4SD",
    "BTN", "DHT3", "GSG", "DHT1", "DHT2", "IR", "BRGB", "LCD", "DPIR3"
]


def clear_retained_messages(client):
    for topic in TOPICS:
        try:
            client.publish(topic, payload=None, retain=True)
        except:
            pass


def on_connect(client, userdata, flags, rc):
    clear_retained_messages(client)
    for t in TOPICS:
        client.subscribe(t)


def save_to_db(data):
    if not data:
        return

    measurement = data.get("name", "unknown")
    p = Point(measurement).tag("name", measurement)

    if "type" in data:
        p = p.tag("type", str(data["type"]))

    fields = data.get("fields")
    if isinstance(fields, dict) and fields:
        for k, v in fields.items():
            if isinstance(v, bool):
                p = p.field(k, int(v))
            elif isinstance(v, int):
                p = p.field(k, v)
            elif isinstance(v, float):
                p = p.field(k, v)
            elif isinstance(v, str):
                p = p.field(k, v)
    else:
        v = data.get("value")
        if isinstance(v, bool):
            p = p.field("value", int(v))
        elif isinstance(v, int):
            p = p.field("value", v)
        elif isinstance(v, float):
            p = p.field("value", v)
        elif isinstance(v, str):
            p = p.field("value", v)

    write_api.write(bucket=bucket, org=org, record=p)


class PeopleCounter:
    def __init__(self):
        self.pairs = {"DPIR1": "DUS1", "DPIR2": "DUS2"}
        self.window_sec = 2
        self.slope_thresh = 0.1
        self.dist_gate = 30.0
        self._dus_hist = {"DUS1": deque(maxlen=400), "DUS2": deque(maxlen=400)}
        self._pir_prev = {"DPIR1": 0, "DPIR2": 0}
        self.people = 0
        self._lock = threading.Lock()

    def _prune(self, q, now):
        cutoff = now - self.window_sec
        while q and q[0][0] < cutoff:
            q.popleft()

    def handle_dus(self, dus_name: str, data: dict):
        try:
            fields = data.get("fields") or {}
            d = fields.get("distance_cm", None)
            if d is None:
                return
            d = float(d)
            now = time.time()
            q = self._dus_hist.get(dus_name)
            if q is None:
                return
            q.append((now, d))
            self._prune(q, now)
        except:
            pass

    def _classify(self, dus_name: str):
        now = time.time()
        q = self._dus_hist.get(dus_name)
        if not q:
            return 0

        self._prune(q, now)
        if len(q) < 4:
            return 0

        t0, d0 = q[0]
        t1, d1 = q[-1]
        dt = t1 - t0
        if dt <= 0.05:
            return 0

        min_d = min(d for _, d in q)
        if min_d > self.dist_gate:
            return 0

        slope = (d1 - d0) / dt
        if slope <= -self.slope_thresh:
            return 1
        if slope >= self.slope_thresh:
            return -1
        return 0

    def handle_pir(self, pir_name: str, data: dict):
        fields = data.get("fields") or {}
        try:
            state = int(fields.get("state", 0))
        except:
            state = 0

        with self._lock:
            prev = self._pir_prev.get(pir_name, 0)
            self._pir_prev[pir_name] = state

        if prev == 0 and state == 1:
            dus_name = self.pairs.get(pir_name)
            if not dus_name:
                return
            delta = self._classify(dus_name)
            if delta == 0:
                return

            with self._lock:
                self.people = max(0, self.people + delta)
                count = self.people

            msg = {
                "name": "PeopleCount",
                "type": "derived",
                "fields": {"count": int(count), "delta": int(delta), "source": str(pir_name)}
            }
            try:
                save_to_db(msg)
            except:
                pass
            try:
                mqtt_client.publish("PEOPLE", payload=json.dumps(msg), qos=0, retain=True)
            except:
                pass

    def handle(self, topic: str, data: dict):
        t = str(topic).upper()
        if t in ("DUS1", "DUS2"):
            self.handle_dus(t, data)
        elif t in ("DPIR1", "DPIR2"):
            self.handle_pir(t, data)
        
    def get_people(self):
        with self._lock:
            return int(self.people)


class SecurityController:
    def __init__(self):
        self.pin = "1234"
        self.arm_delay = 10.0
        self.entry_delay = 10.0
        self.alarm_target = "DB"

        self.armed = False
        self.alarm_on = False
        self.pending_arm_until = 0.0
        self.pending_entry_until = {"DS1": 0.0, "DS2": 0.0}

        self._ds_prev = {"DS1": 0, "DS2": 0}
        self.unlock_threshold = 5.0
        self._ds_active_since = {"DS1": None, "DS2": None}
        self._unlock_alarm_on = False

        self._pin_buf = []
        self._last_key_code = None

        self._pir_prev = {"DPIR1": 0, "DPIR2": 0, "DPIR3": 0}
        self.empty_building_alarm_enabled = True

        self.gsg_threshold = 80.0
        self.gsg_cooldown_sec = 2.0
        self._gsg_last_trigger = 0.0

        self._lock = threading.Lock()
        self._last_state = None

    def handle_gsg_magnitude(self, data: dict):
        fields = data.get("fields") or {}
        try:
            gx = float(fields.get("gx", 0.0))
            gy = float(fields.get("gy", 0.0))
            gz = float(fields.get("gz", 0.0))
        except:
            return

        magnitude = (gx * gx + gy * gy + gz * gz) ** 0.5
        now = time.time()

        with self._lock:
            if self.alarm_on:
                return
            if magnitude < self.gsg_threshold:
                return
            if (now - self._gsg_last_trigger) < self.gsg_cooldown_sec:
                return

            self._gsg_last_trigger = now
            self.alarm_on = True

        self._publish_alarm(True)
        self._emit_state()
    
    def handle_pir_empty_building(self, pir_name: str, data: dict, people_count: int):
        fields = data.get("fields") or {}
        try:
            state = int(fields.get("state", 0))
        except:
            state = 0

        with self._lock:
            prev = self._pir_prev.get(pir_name, 0)
            self._pir_prev[pir_name] = state
            alarm_on = self.alarm_on
            enabled = self.empty_building_alarm_enabled

        if not enabled:
            return
        if people_count != 0:
            return
        if alarm_on:
            return
        if prev == 0 and state == 1:
            with self._lock:
                self.alarm_on = True
            self._publish_alarm(True)
            self._emit_state()

    def _publish_alarm(self, on: bool):
        try:
            mqtt_client.publish(f"CMD/{self.alarm_target}", payload="on" if on else "off", qos=0, retain=False)
        except:
            pass

    def _emit_state(self):
        with self._lock:
            now = time.time()
            st = {
                "armed": int(self.armed),
                "alarm": int(self.alarm_on),
                "arming_pending": int(now < self.pending_arm_until),
                "entry_pending_ds1": int(now < self.pending_entry_until["DS1"]),
                "entry_pending_ds2": int(now < self.pending_entry_until["DS2"]),
            }
            if st == self._last_state:
                return
            self._last_state = dict(st)

        msg = {"name": "SecurityState", "type": "derived", "fields": st}
        try:
            save_to_db(msg)
        except:
            pass
        try:
            mqtt_client.publish("SECURITY", payload=json.dumps(msg), qos=0, retain=True)
        except:
            pass

    def _disarm_and_silence(self):
        with self._lock:
            self.armed = False
            self.alarm_on = False
            self.pending_arm_until = 0.0
            self.pending_entry_until["DS1"] = 0.0
            self.pending_entry_until["DS2"] = 0.0
        self._publish_alarm(False)
        self._emit_state()

    def _schedule_arm(self):
        with self._lock:
            if self.armed:
                return
            now = time.time()
            if now < self.pending_arm_until:
                return
            self.pending_arm_until = now + self.arm_delay
        self._emit_state()

    def _accept_keypress(self, kc: int) -> str | None:
        with self._lock:
            if self._last_key_code is not None and int(kc) == int(self._last_key_code):
                return None
            self._last_key_code = int(kc)
        try:
            ch = chr(int(kc))
        except:
            return None
        if ch not in "0123456789":
            return None
        return ch

    def handle_dms(self, data: dict):
        fields = data.get("fields") or {}
        kc = fields.get("key_code", None)
        if kc is None:
            return
        try:
            kc = int(kc)
        except:
            return

        ch = self._accept_keypress(kc)
        if ch is None:
            return

        entered = None
        with self._lock:
            self._pin_buf.append(ch)
            if len(self._pin_buf) > 4:
                self._pin_buf = self._pin_buf[-4:]
            if len(self._pin_buf) == 4:
                entered = "".join(self._pin_buf)

        if entered is None:
            return

        if entered == self.pin:
            with self._lock:
                now = time.time()
                alarm = self.alarm_on
                armed = self.armed
                pending_arm = now < self.pending_arm_until
                ds_pending = any(
                    (self._ds_active_since.get(k) is not None and (now - self._ds_active_since.get(k)) < self.unlock_threshold)
                    for k in ("DS1", "DS2")
                )

            if pending_arm:
                return

            if alarm:
                with self._lock:
                    self.alarm_on = False
                    for k in ("DS1", "DS2"):
                        if self._ds_active_since.get(k) is not None:
                            self._ds_active_since[k] = now
                self._publish_alarm(False)
                self._emit_state()
                return

            if armed:
                if ds_pending:
                    with self._lock:
                        for k in ("DS1", "DS2"):
                            if self._ds_active_since.get(k) is not None:
                                self._ds_active_since[k] = now
                    self._emit_state()
                    return
                else:
                    with self._lock:
                        self.armed = False
                        self.pending_arm_until = 0.0
                    self._emit_state()
                    return

            self._schedule_arm()
            return

        else:
            with self._lock:
                armed = self.armed
                pending_arm = time.time() < self.pending_arm_until
                if armed and (not pending_arm):
                    self.alarm_on = True
                    now = time.time()
                    for k in ("DS1", "DS2"):
                        if self._ds_active_since.get(k) is not None:
                            self._ds_active_since[k] = now
            if armed and (not pending_arm):
                self._publish_alarm(True)
                self._emit_state()

    def handle_ds(self, ds_name: str, data: dict):
        fields = data.get("fields") or {}
        try:
            state = int(fields.get("state", 0))
        except:
            state = 0

        now = time.time()
        with self._lock:
            if state == 1:
                if self._ds_active_since.get(ds_name) is None:
                    self._ds_active_since[ds_name] = now
            else:
                self._ds_active_since[ds_name] = None

        with self._lock:
            prev = self._ds_prev.get(ds_name, 0)
            self._ds_prev[ds_name] = state
            armed = self.armed
            alarm_on = self.alarm_on

        if prev == 0 and state == 1 and armed and (not alarm_on):
            with self._lock:
                self.pending_entry_until[ds_name] = time.time() + self.entry_delay
            self._emit_state()

    def tick(self):
        now = time.time()
        need_emit = False
        need_alarm_publish = None

        with self._lock:
            if (not self.armed) and (self.pending_arm_until > 0.0) and (now >= self.pending_arm_until):
                self.armed = True
                self.pending_arm_until = 0.0
                need_emit = True

            if self.armed and (not self.alarm_on):
                for k in ("DS1", "DS2"):
                    t0 = self._ds_active_since.get(k)
                    if t0 is not None and (now - t0) >= self.ds_alarm_delay:
                        self.alarm_on = True
                        need_emit = True
                        need_alarm_publish = True
                        break

            if (not self.armed) and (not self.alarm_on):
                exceeded = False
                for k in ("DS1", "DS2"):
                    t0 = self._ds_active_since.get(k)
                    if t0 is not None and (now - t0) >= self.unlock_threshold:
                        exceeded = True
                        break
                if exceeded and (not self._unlock_alarm_on):
                    self._unlock_alarm_on = True
                    self.alarm_on = True
                    need_emit = True
                    need_alarm_publish = True

            if self._unlock_alarm_on:
                ds_any_active = any(self._ds_active_since.get(k) is not None for k in ("DS1", "DS2"))
                if not ds_any_active:
                    self._unlock_alarm_on = False
                    self.alarm_on = False
                    need_emit = True
                    need_alarm_publish = False

        if need_alarm_publish is True:
            self._publish_alarm(True)
        elif need_alarm_publish is False:
            self._publish_alarm(False)

        if need_emit:
            self._emit_state()

    def handle(self, topic: str, data: dict):
        t = str(topic).upper()
        if t == "DMS":
            self.handle_dms(data)
        elif t in ("DS1", "DS2"):
            self.handle_ds(t, data)


people_counter = PeopleCounter()
security = SecurityController()


def security_task():
    while True:
        try:
            security.tick()
        except:
            pass
        time.sleep(0.05)


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8", errors="ignore")
        data = json.loads(payload)
        save_to_db(data)
        people_counter.handle(msg.topic, data)

        t = str(msg.topic).upper()
        if t in ("DPIR1", "DPIR2", "DPIR3"):
            try:
                pc = people_counter.get_people()
            except:
                pc = 0
            security.handle_pir_empty_building(t, data, pc)

        security.handle(msg.topic, data)

        t = str(msg.topic).upper()
        if t == "GSG":
            security.handle_gsg_magnitude(data)
    except Exception as e:
        print(f"> MQTT message parse/save error on topic {msg.topic}: {e}")


mqtt_client = mqtt.Client(client_id=f"server-{socket.gethostname()}", clean_session=True)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
mqtt_client.loop_start()

try:
    save_to_db({"name": "PeopleCount", "type": "derived", "fields": {"count": 0, "delta": 0, "source": "server_boot"}})
    mqtt_client.publish("PEOPLE", payload=json.dumps({"name": "PeopleCount", "type": "derived", "fields": {"count": 0, "delta": 0, "source": "server_boot"}}), qos=0, retain=True)
    mqtt_client.publish("CMD/DB", payload="off", qos=0, retain=False)
except:
    pass

with security._lock:
    security.alarm_on = False
try:
    security._emit_state()
except:
    pass

def normalize_target(t: str) -> str:
    return str(t).strip().upper()


def parse_command_line(line: str):
    if not line:
        return None, None
    parts = line.strip().split()
    if len(parts) < 2:
        return None, None
    target = normalize_target(parts[0])
    cmd = " ".join(parts[1:])
    return target, cmd


def send_command(target, command):
    mqtt_client.publish(f"CMD/{normalize_target(target)}", payload=str(command), qos=0, retain=False)


def server_console_task():
    print("> Server console ready. Type: <target> <command...>")
    print("> Type: x  to stop the server console (Flask will keep running).")

    while True:
        try:
            line = input().strip()
        except EOFError:
            return
        except Exception:
            continue

        if not line:
            continue
        if line.lower() == "x":
            print("> Server console stopped.")
            return

        target, cmd = parse_command_line(line)
        if not target or cmd is None:
            print("> Invalid command. Format: <target> <command...>")
            continue

        send_command(target, cmd)
        print(f"> Sent: CMD/{target}  payload='{cmd}'")


@app.route("/command", methods=["POST"])
def command():
    data = request.get_json(force=True)
    target = data.get("target")
    cmd = data.get("command")

    if not target or cmd is None:
        return jsonify({"status": "error", "message": "target and command are required"}), 400

    send_command(target, cmd)
    return jsonify({"status": "success", "target": normalize_target(target), "command": str(cmd)})


@app.route("/command_text", methods=["POST"])
def command_text():
    if request.is_json:
        data = request.get_json(force=True)
        line = data.get("line", "")
    else:
        line = request.data.decode("utf-8", errors="ignore")

    target, cmd = parse_command_line(line)
    if not target or cmd is None:
        return jsonify({"status": "error", "message": "Expected: '<target> <command...>'"}), 400

    send_command(target, cmd)
    return jsonify({"status": "success", "target": target, "command": cmd})


_cam_lock = threading.Lock()
_cam = None
_CAP_BACKEND = cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0


def _open_camera():
    cam = cv2.VideoCapture(0, _CAP_BACKEND) if _CAP_BACKEND else cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv2.CAP_PROP_FPS, 20)
    return cam


def get_camera():
    global _cam
    with _cam_lock:
        if _cam is None:
            _cam = _open_camera()
        elif not _cam.isOpened():
            try:
                _cam.release()
            except:
                pass
            _cam = _open_camera()
        return _cam


def gen_frames():
    fail = 0
    while True:
        cam = get_camera()
        ok, frame = cam.read()
        if not ok or frame is None:
            fail += 1
            if fail >= 30:
                with _cam_lock:
                    try:
                        cam.release()
                    except:
                        pass
                    globals()["_cam"] = None
                fail = 0
            time.sleep(0.05)
            continue

        fail = 0
        frame = cv2.flip(frame, 1)
        ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        )


@app.route("/camera")
def camera_feed():
    return Response(gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@atexit.register
def _release_cam():
    global _cam
    with _cam_lock:
        if _cam is not None:
            try:
                _cam.release()
            except:
                pass
            _cam = None


if __name__ == "__main__":
    threading.Thread(target=server_console_task, name="ServerConsole", daemon=True).start()
    threading.Thread(target=security_task, name="SecurityTask", daemon=True).start()
    app.run(debug=True, use_reloader=False)