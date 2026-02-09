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


# MQTT Configuration
mqtt_client = mqtt.Client()
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

def on_connect(client, userdata, flags, rc):
    client.subscribe("DS1")
    client.subscribe("DL")
    client.subscribe("DUS1")
    client.subscribe("DB")
    client.subscribe("DPIR1")
    client.subscribe("DMS")
    client.subscribe("WEBC")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = lambda client, userdata, msg: save_to_db(json.loads(msg.payload.decode('utf-8')))


def save_to_db(data):
    if data == None: return
    write_api = influxdb_client.write_api(write_options=SYNCHRONOUS)
    point = (
        Point(data["name"])
        .tag("name", data["name"])
        .tag("id", data["id"])
        .tag("description", data["description"])
        .tag("simulated", data["simulated"])
        #.tag("timestamp", data["timestamp"])
        #.tag("message", data["message"])
        .field("value", data["value"])
    )
    write_api.write(bucket=bucket, org=org, record=point)

# Route to store dummy data
@app.route('/store_data', methods=['POST'])
def store_data():
    try:
        data = request.get_json()
        store_data(data)
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
    app.run(debug=True)
