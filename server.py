from flask import Flask, jsonify, request
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import paho.mqtt.client as mqtt
import json


app = Flask(__name__)

# InfluxDB Configuration
token = "F9xWKba1m3XN3Ds69w6eW0F9F18c3i9t5bicNXdfTB4Vv3UFvPkNN7nY2IwjfoOpPi1PoObF9g1-klq6dDQl3Q=="
org = "FTN"
url = "http://localhost:8086"
bucket = "example_db"
influxdb_client = InfluxDBClient(url=url, token=token, org=org)


TOPICS = [
    "DS1", "DL", "DUS1", "DB", "DPIR1", "DMS", "DS2", "DUS2", "DPIR2", "4SD",
    "BTN", "DHT3", "GSG", "DHT1", "DHT2", "IR", "BRGB", "LCD", "DPIR3"
]

def clear_retained_messages(client):
    for topic in TOPICS:
        client.publish(topic, payload=None, retain=True)

def on_connect(client, userdata, flags, rc):
    clear_retained_messages(client)

    client.subscribe("DS1")
    client.subscribe("DL")
    client.subscribe("DUS1")
    client.subscribe("DB")
    client.subscribe("DPIR1")
    client.subscribe("DMS")
    #client.subscribe("WEBC")
    client.subscribe("DS2")
    client.subscribe("DUS2")
    client.subscribe("DPIR2")
    client.subscribe("4SD")
    client.subscribe("BTN")
    client.subscribe("DHT3")
    client.subscribe("GSG")
    client.subscribe("DHT1")
    client.subscribe("DHT2")
    client.subscribe("IR")
    client.subscribe("BRGB")
    client.subscribe("LCD")
    client.subscribe("DPIR3")

# MQTT Configuration
mqtt_client = mqtt.Client()

mqtt_client.on_connect = on_connect
mqtt_client.on_message = lambda client, userdata, msg: save_to_db(json.loads(msg.payload.decode('utf-8')))

mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

def save_to_db(data):
    if data == None: return

    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)

    point = (
        Point(data["name"])
        .tag("name", data["name"])
        .tag("type", data["type"])
        .field("value", data["value"])
    )

    write_api.write(bucket=bucket, org=org, record=point)

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

@app.route('/store_data', methods=['POST'])
def store_data():
    try:
        data = request.get_json()

        store_data(data)
        
        return jsonify({"status": "success"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/simple_query', methods=['GET'])
def retrieve_simple_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Humidity")"""
    
    return handle_influx_query(query)

@app.route('/aggregate_query', methods=['GET'])
def retrieve_aggregate_data():
    query = f"""from(bucket: "{bucket}")
    |> range(start: -10m)
    |> filter(fn: (r) => r._measurement == "Humidity")
    |> mean()"""

    return handle_influx_query(query)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)