import subprocess
import os
import signal
import time
import logging
import paho.mqtt.client as mqtt
from obswebsocket import obsws, requests
import json
from dotenv import load_dotenv


log = logging.getLogger("client")
log.setLevel(logging.INFO)
log_handler = logging.FileHandler("client.log")
log_handler.setFormatter(logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s"))
log.addHandler(log_handler)


def check_configure(path: str) -> bool:
    return os.path.isfile(path + "config.json")


def get_obs_pid() -> int or None:
    def obs_is_running(check_obs: list) -> bool:
        # 9 - length of shell output if obs process was found
        return len(check_obs) == 9

    obs_pid = None
    shell_output = subprocess.check_output('tasklist /fi "IMAGENAME eq obs64.exe" /fo "CSV"').decode(
        encoding="windows-1251").replace('"', '').split(",")

    if obs_is_running(shell_output):
        obs_pid = int(shell_output[5])

    return obs_pid


def kill_process(pid: int):
    # !!! DANGER
    os.kill(pid, signal.SIGTERM)


def check_obs_path(path: str):
    return os.path.isfile(path + "\\" + "obs64.exe")


def start_obs_process() -> subprocess.Popen or None:
    # !!! obs_process.pid = pid of shell
    obs_process = None

    if check_obs_path(OBS_PATH):
        obs_process = subprocess.Popen(OBS_PATH + "\\" + "obs64.exe", cwd=OBS_PATH)

    return obs_process


def ping_sources(obs_ws: obsws) -> dict:
    obs_ws.connect()
    resp = dict()
    scenes = obs_ws.call(requests.GetSceneList())
    scenes_names = [scene["sceneName"] for scene in scenes.datain["scenes"]]

    for scene_name in scenes_names:
        resp[scene_name] = list()
        sources = obs_ws.call(requests.GetSceneItemList(sceneName=scene_name))
        gstreamer_sources_names = [source["sourceName"] for source in sources.datain["sceneItems"]
                                   if source["inputKind"] == "gstreamer-source"]

        for source_name in gstreamer_sources_names:
            screenshot = obs_ws.call(requests.GetSourceScreenshot(sourceName=source_name, imageWidth=8, imageHeight=8,
                                                                  imageFormat="png")).datain["imageData"]
            # 146 - length of base64 data string about empty png image
            state = False if len(screenshot) == 146 else True

            resp[scene_name].append({
                "source": source_name,
                "state": state
            })

    obs_ws.disconnect()
    return resp


# MQTT connection
def on_connect(client, userdata, flags, rc):
    if not rc:
        log.info(f"mqtt connected to broker with result code {rc}")
    else:
        log.error(f"mqtt connected to broker with result code {rc}")

    client.subscribe("autostream/ping_sources")


def publish_ping(client, topic):
    msg = json.dumps({OBS_NAME: ping_sources(obs_websockets)})
    '''
    {OBS_NAME: {
                scene_name: [ {"source": source_name, "state": True}, {"source": source_name2, "state": False}, {}],
                scene_name2: [ {}, {}, {}],
                ...
                }
    }
    '''
    result = client.publish(topic, msg)
    status = result[0]

    if status:
        log.warning(f"Failed to send message to topic {topic}")


def publish_state(client, topic, obs_state):
    msg = json.dumps(obs_state)
    result = client.publish(topic, msg)
    status = result[0]

    if status:
        log.warning(f"Failed to send message to topic {topic}")


def on_message(client, userdata, msg):
    # PING_OBS - special command that sign client app to do and send ping data
    if b'PING_OBS' == msg.payload:
        publish_ping(client, msg.topic)
        log.info("ping published")
    # if json.loads(msg.payload) == "PING_OBS":
    #     publish_ping(client, msg.topic)


def create_mqtt_client(username: str, password: str, host: str, port: int) -> mqtt.Client or None:
    def check_mqtt_connection(client: mqtt.Client, host: str, port: int) -> bool:
        client.connect_async(host, port)
        client.loop_start()
        # sleep!
        time.sleep(0.5)
        state = client.is_connected()
        client.loop_stop()

        if state:
            client.disconnect()

        return state

    client = mqtt.Client()
    client.username_pw_set(username, password)

    if check_mqtt_connection(client, host, port):
        client.on_connect = on_connect
        client.on_message = on_message
        return client

    return None


def poll_process(process: subprocess.Popen) -> dict:
    poll = process.poll()
    time_stamp = time.strftime("%Y.%m.%d %H:%M:%S")
    state = poll is None
    msg = {
        "name": OBS_NAME,
        "time": time_stamp,
        "state": state,
    }
    return msg


WORK_DIRECTORY = os.getcwd() + "\\"

load_dotenv(WORK_DIRECTORY + ".env")

# get local variables
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
OBSWS_PASSWORD = os.getenv("OBSWS_PASSWORD")

if not(MQTT_USERNAME and MQTT_PASSWORD and OBSWS_PASSWORD):
    log.error(f"environment variables are empty. Path to env-file: {WORK_DIRECTORY + '.env'}")

if check_configure(WORK_DIRECTORY):
    with open(WORK_DIRECTORY + "config.json") as f:
        config = json.load(f)
        OBSWS_HOST = config["obsws"]["host"]
        OBSWS_PORT = config["obsws"]["port"]
        OBS_PATH = config["obs_path"]
        MQTT_BROKER_HOST = config["mqtt"]["host"]
        MQTT_BROKER_PORT = config["mqtt"]["port"]
        MQTT_BROKER_KEEP_ALIVE_TIME = config["mqtt"]["keep_alive_time"]
        UPDATE_LOOP_TIME = config["update_loop_time"]
        OBS_NAME = config["obs_name"]
        STATE_TOPIC = config["mqtt"]["state_topic"]
        PING_TOPIC = config["mqtt"]["ping_topic"]
else:
    log.critical(f"config.json not found. Path to config-file: {WORK_DIRECTORY + 'config.json'}")
    exit("Error: config.json not found")

# check if obs is running before program was started
obs_pid = get_obs_pid()

if obs_pid is not None:
    kill_process(obs_pid)
    log.info("obs was killed")
    # sleep!
    time.sleep(2)

# start obs64.exe
obs_process = start_obs_process()

if not obs_process:
    log.error("obs process was not created. Path to obs-file: " + OBS_PATH + "\\" + "obs64.exe")
else:
    log.info("obs was started")

# create obs websockets object
obs_websockets = obsws(OBSWS_HOST, OBSWS_PORT, OBSWS_PASSWORD)
# create mqtt_client
mqtt_client = create_mqtt_client(MQTT_USERNAME, MQTT_PASSWORD, MQTT_BROKER_HOST, MQTT_BROKER_PORT)

if mqtt_client:
    # connect_async to allow background processing
    mqtt_client.connect_async(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_BROKER_KEEP_ALIVE_TIME)
    mqtt_client.loop_start()

    while True:
        # sleep!
        time.sleep(UPDATE_LOOP_TIME)
        obs_state_msg = poll_process(obs_process)
        publish_state(mqtt_client, STATE_TOPIC, obs_state_msg)

        if not obs_state_msg["state"]:
            # try restart obs64.exe 3 times
            try_count = 1
            log.info("obs restarting")
            obs_process = start_obs_process()

            while obs_process is None and try_count <= 3:
                # sleep !
                time.sleep(1)
                log.error(f"obs failed to restart. try: {try_count}")
                obs_process = start_obs_process()
                try_count += 1
else:
    log.critical(f"Mqtt connection was not established.\nMqtt broker: {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    log.info("obs was killed")
    obs_process.kill()
