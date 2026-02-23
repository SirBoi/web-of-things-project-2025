from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from influxdb_client import InfluxDBClient
import cv2
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "YOUR_TOKEN"
INFLUX_ORG = "YOUR_ORG"
INFLUX_BUCKET = "sensors"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

query_api = client.query_api()

DEVICES = {
    "pi1": ["temperature", "humidity", "motion"],
    "pi2": ["temperature", "door", "light"],
    "pi3": ["temperature", "humidity", "camera"]
}

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "devices": DEVICES
    })


@app.get("/api/data/{device_id}/{component}")
def get_data(device_id: str, component: str, start: str, stop: str):
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: time(v: "{start}"), stop: time(v: "{stop}"))
      |> filter(fn: (r) => r["device_id"] == "{device_id}")
      |> filter(fn: (r) => r["component"] == "{component}")
    '''

    tables = query_api.query(query)
    results = []

    for table in tables:
        for record in table.records:
            results.append({
                "time": record.get_time().isoformat(),
                "value": record.get_value()
            })

    return results

@app.get("/api/current/{device_id}/{component}")
def get_current(device_id: str, component: str):
    query = f'''
    from(bucket: "{INFLUX_BUCKET}")
      |> range(start: -5m)
      |> filter(fn: (r) => r["device_id"] == "{device_id}")
      |> filter(fn: (r) => r["component"] == "{component}")
      |> last()
    '''

    tables = query_api.query(query)

    for table in tables:
        for record in table.records:
            return {"value": record.get_value()}

    return {"value": "No data"}

def generate_camera():
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        time.sleep(0.05)

@app.get("/camera")
def camera_feed():
    return StreamingResponse(
        generate_camera(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )