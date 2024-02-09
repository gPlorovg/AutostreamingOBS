import asyncio
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
import paho.mqtt.client as mqtt
import time

# MQTT broker configuration
MQTT_BROKER_HOST = "172.18.130.40"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "autostream/ping_sources"
RESPONSE = None
REQ_ID = ""

# Define MQTT client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set("recorder", "recorder2020")

app = FastAPI()
test = TestClient(app)


# Define callback functions
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(MQTT_TOPIC)


def publish(client, topic, data):
    msg = json.dumps(data)
    result = mqtt_client.publish(MQTT_TOPIC, msg)
    status = result[0]

    if status:
        print(f"Failed to send message to topic {MQTT_TOPIC}")
    else:
        print("SEND to topic:" + MQTT_TOPIC)


def on_message(client, userdata, msg):
    global RESPONSE

    resp = json.loads(msg.payload)
    if "resp_id" in resp and resp["resp_id"] == REQ_ID:
        RESPONSE = resp


# Assign callbacks to client
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT broker
mqtt_client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)


@app.get("/")
async def read_root():
    print("HERE")
    global RESPONSE, REQ_ID

    OBS_NAME = "localhost:4455"
    REQ_ID = hash(OBS_NAME)

    req = {
        "req_id": REQ_ID,
        "obs_name": OBS_NAME,
        "request": "GetVersion",
        "data": None
    }
    RESPONSE = None

    mqtt_client.loop_start()
    await asyncio.sleep(0.1)
    publish(mqtt_client, MQTT_TOPIC, req)

    while not RESPONSE:
        await asyncio.sleep(0.1)

    mqtt_client.loop_stop()
    print(RESPONSE)



