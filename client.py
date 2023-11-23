import subprocess
import os
import signal
import time
import paho.mqtt.client as mqtt
# from obswebsocket import obsws, requests
import json
from dotenv import load_dotenv


load_dotenv()
# obs websocket connection
# obs_host = "localhost"
# obs_port = 4455
# obs_password = "TKoxvvk9TPgJNkt4"
# obs = obsws(obs_host, obs_port, obs_password)


# def ping_sources() -> dict:
#     resp = dict()
#     scenes = obs.call(requests.GetSceneList())
#     scenes_names = [scene["sceneName"] for scene in scenes.datain["scenes"]]
#     for scene_name in scenes_names:
#         sources = obs.call(requests.GetSceneItemList(sceneName=scene_name))
#         sources_names = [source["sourceName"] for source in sources.datain["sceneItems"]]
#         resp[scene_name] = dict()
#         for source_name in sources_names:
#             source_activity = obs.call(requests.GetSourceActive(sourceName=source_name))
#             resp[scene_name][source_name] = {"videoActive": source_activity.datain["videoActive"],
#                                              "videoShowing": source_activity.datain["videoShowing"]}
#     return resp

def create_obs_script():
    USERNAME = str(os.getenv("NAME"))
    PASSWORD = str(os.getenv("PASSWORD"))

    with open("obs_script_template") as t, open("obs_script.py", "w") as f:
        for line in t:
            
            match line:
                case "# username =\n":
                    line = "username = \"" + USERNAME + "\"\n"
                case "# password =\n":
                    line = "password = \"" + PASSWORD + "\"\n"

            f.write(line)


# find path to obs64.exe in disk C:\
def find():
    for root, _, files in os.walk("C:\\"):
        if "obs64.exe" in files:
            return os.path.join(root)


if not os.path.isfile("config.conf"):
    OBS_PATH = find()
    with open("config.conf", "w") as f:
        f.write(OBS_PATH)
else:
    with open("config.conf") as f:
        OBS_PATH = f.readline()

# create obs_script.py file
create_obs_script()

# check if obs is running before program was started
check_obs = subprocess.check_output('tasklist /fi "IMAGENAME eq obs64.exe" /fo "CSV"').decode(encoding="windows-1251")\
    .replace('"', '').split(",")

# !!! DANGER
if len(check_obs) == 9:
    print("obs PID: ", check_obs[5])
    os.kill(int(check_obs[5]), signal.SIGTERM)
else:
    print("No obs detected!")

# start obs64.exe
# !!! obs_process.pid - pid of shell
obs_process = subprocess.Popen(OBS_PATH + "\\" + "obs64.exe", cwd=OBS_PATH)

# mqtt connection
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("autostream")


def publish(client, topic, obs_status):
    msg = json.dumps(obs_status)
    result = client.publish(topic, msg)
    status = result[0]
    if not status:
        print(f"Send {msg} to {topic}")
    else:
        print(f"Failed to send message to topic {topic}")


# def on_message(client, userdata, msg):
#     if json.loads(msg.payload) == "PING_OBS":
#         publish(client, msg.topic)


topic = "autostream/obs_state"
client = mqtt.Client()
client.on_connect = on_connect
# client.on_message = on_message
# get local variables

USERNAME = os.getenv("NAME")
PASSWORD = os.getenv("PASSWORD")

client.username_pw_set(USERNAME, PASSWORD)
# connect_async to allow background processing
client.connect_async("172.18.130.40", 1883, 60)

client.loop_start()
while True:
    time.sleep(1)
    poll = obs_process.poll()
    if poll is None:
        publish(client, topic, "UP")
    else:
        publish(client, topic, "DOWN")
        # start obs64.exe
        obs_process = subprocess.Popen(OBS_PATH + "\\" + "obs64.exe", cwd=OBS_PATH)
