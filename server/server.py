from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json
import os
import threading
import time

app = Flask(__name__)

# -----------------------------
# InfluxDB Configuration
# -----------------------------
# Preporuka: stavi ove vrednosti u env varijable (ali radi i ovako).
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "XMKp6ipTlmKKLHezzYF1SkTW8KyziJaM0PwK-f4jeywbUpaGw73l4fmGPDvCs9DdK7dtKzHvRPDQ0gLnDSvSDw==")
INFLUX_ORG = os.getenv("INFLUX_ORG", "FTN")
INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "example_db")

influxdb_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)


# -----------------------------
# MQTT Configuration (MULTI-BROKER)
# -----------------------------
# Definiši više brokera ovako (env var):
# MQTT_BROKERS="localhost:1883,localhost:1884,192.168.0.10:1883"
#
# Ako nije setovano, default je localhost:1883
MQTT_BROKERS_RAW = os.getenv("MQTT_BROKERS", "localhost:1883")
MQTT_BROKERS="localhost:1883,localhost:1884,192.168.0.10:1883"

# Wildcard topic: sluša sve (možeš suziti na npr. "devices/#")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "#")

# opcionalno: user/pass ako treba
MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")

mqtt_clients = []


def parse_brokers(raw: str):
    brokers = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            host, port_str = part.split(":", 1)
            brokers.append((host.strip(), int(port_str.strip())))
        else:
            brokers.append((part, 1883))
    return brokers


def safe_json_loads(payload_bytes: bytes):
    try:
        return json.loads(payload_bytes.decode("utf-8", errors="replace"))
    except Exception:
        return None


def save_to_db(data, source=None):
    """
    data očekuje strukturu:
    {
      "name": "...",
      "id": "...",
      "description": "...",
      "simulated": true/false,
      "value": <number/string>
    }
    """
    if data is None:
        return

    # ako ti nekad dođe "null" ili neki čudan payload
    if not isinstance(data, dict):
        return

    required = ["name", "id", "description", "simulated", "value"]
    for k in required:
        if k not in data:
            return

    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    p = (
        Point(str(data["name"]))  # measurement
        .tag("name", str(data["name"]))
        .tag("id", str(data["id"]))
        .tag("description", str(data["description"]))
        .tag("simulated", str(data["simulated"]))
    )

    # ovo ti omogućava da vidiš sa kog brokera/porta je došlo
    if source:
        p = p.tag("source", source)

    # value field
    v = data["value"]
    # Influx field može biti number/string/bool; ovde minimalno normalizujemo
    if isinstance(v, (int, float, bool, str)):
        p = p.field("value", v)
    else:
        # fallback - pretvori u string
        p = p.field("value", json.dumps(v))

    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)


def make_mqtt_client(host, port):
    client_id = f"flask-influx-listener-{host}-{port}-{int(time.time()*1000)}"
    c = mqtt.Client(client_id=client_id)

    if MQTT_USERNAME:
        c.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    def on_connect(client, userdata, flags, rc):
        # rc==0 znači success
        client.subscribe(MQTT_TOPIC)

    def on_message(client, userdata, msg):
        data = safe_json_loads(msg.payload)
        save_to_db(data, source=f"{host}:{port}")

    c.on_connect = on_connect
    c.on_message = on_message
    return c


def start_all_mqtt_listeners():
    brokers = parse_brokers(MQTT_BROKERS_RAW)

    for host, port in brokers:
        c = make_mqtt_client(host, port)
        c.connect(host, port, 60)
        c.loop_start()
        mqtt_clients.append(c)


# start listeners odmah pri startu servera
start_all_mqtt_listeners()


# -----------------------------
# Flask routes
# -----------------------------
@app.route("/store_data", methods=["POST"])
def store_data_route():
    """
    Ručni upis (npr. test). Ne šalje na MQTT, nego direktno upisuje u Influx.
    """
    try:
        data = request.get_json()
        save_to_db(data, source="http")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


def handle_influx_query(query):
    try:
        query_api = influxdb_client.query_api()
        tables = query_api.query(query, org=INFLUX_ORG)

        container = []
        for table in tables:
            for record in table.records:
                container.append(record.values)

        return jsonify({"status": "success", "data": container})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/simple_query", methods=["GET"])
def retrieve_simple_data():
    # Napomena: tvoj upis koristi measurement = data["name"] (npr DUS1, DPIR1...)
    # Ovo "Humidity" verovatno neće ništa vratiti osim ako baš tako šalješ.
    measurement = request.args.get("measurement", "")
    if measurement:
        meas_filter = f'|> filter(fn: (r) => r._measurement == "{measurement}")'
    else:
        meas_filter = ""  # bez filtera

    query = f"""from(bucket: "{INFLUX_BUCKET}")
    |> range(start: -10m)
    {meas_filter}
    |> filter(fn: (r) => r._field == "value")
    """
    return handle_influx_query(query)


@app.route("/aggregate_query", methods=["GET"])
def retrieve_aggregate_data():
    measurement = request.args.get("measurement", "")
    if measurement:
        meas_filter = f'|> filter(fn: (r) => r._measurement == "{measurement}")'
    else:
        meas_filter = ""

    query = f"""from(bucket: "{INFLUX_BUCKET}")
    |> range(start: -10m)
    {meas_filter}
    |> filter(fn: (r) => r._field == "value")
    |> mean()
    """
    return handle_influx_query(query)


if __name__ == "__main__":
    # Flask na default portu 5000
    app.run(debug=True)
