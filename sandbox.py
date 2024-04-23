import asyncio
import json
from fastapi import FastAPI
from fastapi.testclient import TestClient
import paho.mqtt.client as mqtt


# MQTT broker configuration
MQTT_BROKER_HOST = "172.18.130.40"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "autostream/obsws_request"
RESPONSE = None
REQ_ID = ""
OBS_NAME = "localhost:4455"
global_lock = asyncio.Lock()

# Define MQTT client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set("recorder", "recorder2020")

app = FastAPI()
test = TestClient(app)


# async def _wait_for_cond(cond, func):
#     async with cond:
#         await cond.wait_for(func)


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


@app.get("/obsws_request")
async def run_obsws_request():
    global RESPONSE, REQ_ID

    mqtt_client.loop_start()
    await asyncio.sleep(0.5)
    await global_lock.acquire()
    RESPONSE = None
    REQ_ID = hash(OBS_NAME)
    req = {
        "req_id": REQ_ID,
        "obs_name": OBS_NAME,
        "request": "GetVersion",
        "data": None
    }

    publish(mqtt_client, MQTT_TOPIC, req)
    print(RESPONSE)
    print(REQ_ID)
    while not RESPONSE:
        await asyncio.sleep(0.1)

    print(RESPONSE)
    global_lock.release()
    mqtt_client.loop_stop()


i = 0
while i < 10:
    test.get("/obsws_request")
    i += 1
