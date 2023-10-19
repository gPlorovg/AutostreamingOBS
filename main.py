import subprocess
import os
import signal
import paho.mqtt.client as mqtt
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


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/autostream")


def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("recorder", "recorder2020")

client.connect("172.18.130.40", 1883, 60)

client.loop_forever()
