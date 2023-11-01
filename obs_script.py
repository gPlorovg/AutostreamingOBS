import os
import subprocess
import json
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import obspython as obs


global client


def ping_sources() -> dict:
    resp = dict()
    for source in obs.obs_enum_sources():
        source_name = obs.obs_source_get_name(source)
        input_address = obs.obs_data_get_string(obs.obs_source_get_settings(source), "input")
        if input_address:
            # if "rtsp://" in input_address:
            cut_address = input_address.split("//")[1].split("/")[0]
            is_online = subprocess.call("ping -n 1 " + cut_address, shell=True) == 0

            resp[source_name] = {
                "address": input_address,
                "is_online": is_online
            }
    print(resp)
    return resp


# find path to obs64.exe in disk C:\
def find():
    for root, _, files in os.walk("C:\\"):
        if "autostreaming.env" in files:
            return os.path.join(root + "\\autostreaming.env")


def script_description():
    return "Ping all ip cameras"


def on_connect(client_, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client_.subscribe("autostream/ping_sources")


def publish(client_, topic):
    msg = json.dumps(ping_sources())
    print(msg)
    result = client_.publish(topic, msg)
    # status = result[0]
    # if not status:
    #     print(f"Send {msg} to {topic}")
    # else:
    #     print(f"Failed to send message to topic {topic}")


def on_message(client_, userdata, msg):
    if json.loads(msg.payload) == "PING_OBS":
        publish(client_, msg.topic)


def script_load(settings):
    global client
    topic = "autostream/ping_sources"
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # get local variables
    env_path = find()
    load_dotenv(env_path)
    username = os.getenv("NAME")
    password = os.getenv("PASSWORD")
    client.username_pw_set(username, password)
    # connect_async to allow background processing
    client.connect_async("172.18.130.40", 1883, 60)
    client.loop_start()
    # obs.timer_add(ping_sources, 5000)


def script_unload():
    print("STOP")
    client.loop_stop()
