from flask import Flask, jsonify, request, Response
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import cv2
import time
import threading
import atexit



app = Flask(__name__)

# InfluxDB configuration
token = "F9xWKba1m3XN3Ds69w6eW0F9F18c3i9t5bicNXdfTB4Vv3UFvPkNN7nY2IwjfoOpPi1PoObF9g1-klq6dDQl3Q=="
org = "FTN"
url = "http://localhost:8086"
bucket = "example_db"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)

write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

# MQTT settings
MQTT_HOST = "localhost"
MQTT_PORT = 1883

TOPICS = [
    "DS1", "DL", "DUS1", "DB", "DPIR1", "DMS", "DS2", "DUS2", "DPIR2", "4SD",
    "BTN", "DHT3", "GSG", "DHT1", "DHT2", "IR", "BRGB", "LCD", "DPIR3"
]



def clear_retained_messages(client):
    for topic in TOPICS:
        client.publish(topic, payload=None, retain=True)

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
                continue
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

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        save_to_db(data)
    except Exception as e:
        print(f"> MQTT message parse/save error on topic {msg.topic}: {e}")



# MQTT configuration
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_HOST, MQTT_PORT, 60)
mqtt_client.loop_start()



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
    print("> Server console ready. Type: <target> <command...>  (example: dpir1 on 10)")
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

@app.route("/store_data", methods=["POST"])
def store_data_route():
    try:
        data = request.get_json()
        save_to_db(data)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def handle_influx_query(query):
    try:
        query_api = influxdb_client.query_api()
        tables = query_api.query(query, org=org)
        container = []
        for table in tables:
            for record in table.records:
                container.append(record.values)
        return jsonify({"status": "success", "data": container})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/simple_query", methods=["GET"])
def retrieve_simple_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Humidity")"""
    return handle_influx_query(query)

@app.route("/aggregate_query", methods=["GET"])
def retrieve_aggregate_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Humidity")
    |> mean()"""
    return handle_influx_query(query)



# Camera configuration
_cam_lock = threading.Lock()
_cam = None

def get_camera():
    global _cam
    with _cam_lock:
        if _cam is None:
            _cam = cv2.VideoCapture(0)
            _cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            _cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            _cam.set(cv2.CAP_PROP_FPS, 20)
        return _cam

def gen_frames():
    cam = get_camera()
    while True:
        ok, frame = cam.read()
        if not ok:
            time.sleep(0.05)
            continue

        frame = cv2.flip(frame, 1)

        ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
        if not ok:
            continue

        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
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
    app.run(debug=True, use_reloader=False)