import subprocess
import os
import signal
import paho.mqtt.client as mqtt
from obswebsocket import obsws, requests
import json

# obs websocket connection
obs_host = "localhost"
obs_port = 4455
obs_password = "TKoxvvk9TPgJNkt4"
obs = obsws(obs_host, obs_port, obs_password)


def ping_sources() -> dict:
    resp = dict()
    scenes = obs.call(requests.GetSceneList())
    scenes_names = [scene["sceneName"] for scene in scenes.datain["scenes"]]
    for scene_name in scenes_names:
        sources = obs.call(requests.GetSceneItemList(sceneName=scene_name))
        sources_names = [source["sourceName"] for source in sources.datain["sceneItems"]]
        resp[scene_name] = dict()
        for source_name in sources_names:
            source_activity = obs.call(requests.GetSourceActive(sourceName=source_name))
            resp[scene_name][source_name] = {"videoActive": source_activity.datain["videoActive"],
                                             "videoShowing": source_activity.datain["videoShowing"]}
    return resp


# find path to obs64.exe in disk C:\
def find():
    for root, _, files in os.walk("C:\\"):
        if "obs64.exe" in files:
            return os.path.join(root)


OBS_PATH = find()
# check if obs is running before program was started
check_obs = subprocess.check_output('tasklist /fi "IMAGENAME eq obs64.exe" /fo "CSV"').decode(encoding="windows-1251")\
    .replace('"', '').split(",")

if len(check_obs) == 9:
    print("obs PID: ", check_obs[5])
    os.kill(int(check_obs[5]), signal.SIGTERM)
else:
    print("No obs detected!")

# start obs64.exe
# !!! obs_process.pid - pid of shell
obs_process = subprocess.Popen(f'start /d "{OBS_PATH}" obs64.exe', shell=True)
# check if obs_process is running
if obs_process.poll() is None:
    print("alive")


# mqtt connection
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/autostream")


def publish(client, topic):
    obs.connect()
    msg = json.dumps(ping_sources())
    obs.disconnect()
    result = client.publish(topic, msg)
    status = result[0]
    if not status:
        print(f"Send {msg} to {topic}")
    else:
        print(f"Failed to send message to topic {topic}")


def on_message(client, userdata, msg):
    if json.loads(msg.payload) == "PING_OBS":
        publish(client, msg.topic)


topic = "/autostream"
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("recorder", "recorder2020")
# connect_async to allow background processing
client.connect_async("172.18.130.40", 1883, 60)

client.loop_forever()
