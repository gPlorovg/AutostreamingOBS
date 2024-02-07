import json
import sys
import os
import time
from getpass import getpass
import paho.mqtt.client as mqtt
from obswebsocket import obsws, exceptions


def check_configure(path: str) -> bool:
    return os.path.isfile(path + "config.json")


def check_mqtt_connection(username: str, password: str, host: str, port: int) -> bool:
    client = mqtt.Client()
    client.username_pw_set(username, password)
    client.connect_async(host, port)
    client.loop_start()
    # sleep!
    time.sleep(0.5)
    state = client.is_connected()
    client.loop_stop()

    if state:
        client.disconnect()

    return state


def check_obsws_connection(host: str, port: int, password: str) -> bool:
    obs = obsws(host, port, password)
    try:
        obs.connect()
    except exceptions.ConnectionFailure:
        return False
    else:
        return True


def create_env_file(mqtt_username: str, mqtt_password: str, obsws_password: str):
    with open(".env", "w") as f:
        f.write("MQTT_USERNAME=" + mqtt_username + "\n")
        f.write("MQTT_PASSWORD=" + mqtt_password + "\n")
        f.write("OBSWS_PASSWORD=" + obsws_password + "\n")


def get_mqtt_creds() -> dict:
    host = input("Input MQTT broker host (form: '0.0.0.0'): ")
    port = input("Input MQTT broker port: ")

    while not port.isnumeric():
        print("Port is incorrect!")
        port = input("Input MQTT broker port: ")

    port = int(port)
    username = input("Input MQTT username: ")
    password = getpass("Input MQTT password: ")

    while not check_mqtt_connection(username, password, host, port):
        print("Connection error! Check your information and try again.\n")

        host = input("Input MQTT broker host (form: '0.0.0.0'): ")
        port = input("Input MQTT broker port: ")

        while not port.isnumeric():
            print("Port is incorrect!")
            port = input("Input MQTT broker port: ")

        port = int(port)
        username = input("Input MQTT username:")
        password = getpass("Input MQTT password:")

    resp = {
        "host": host,
        "port": port,
        "username": username,
        "password": password
    }

    return resp


def get_obsws_creds() -> dict:
    host = input("Input OBS websocket host:")
    port = input("Input OBS websocket port:")

    while not port.isnumeric():
        print("Port is incorrect!")
        port = input("Input OBS websocket port:")

    port = int(port)

    password = getpass("Input OBS websocket password:")

    while not check_obsws_connection(host, port, password):
        print("Connection error! Check your information and try again.\n")
        host = input("Input OBS websocket host:")
        port = input("Input OBS websocket port:")

        while not port.isnumeric():
            print("Port is incorrect!")
            port = input("Input OBS websocket port:")

        port = int(port)
        password = getpass("Input OBS websocket password:")

    resp = {
        "host": host,
        "port": port,
        "password": password
    }

    return resp


def main() -> dict:
    mqtt_creds = get_mqtt_creds()
    obsws_creds = get_obsws_creds()

    schedule_run_command = "schtasks /create /sc ONLOGON /tn Autostreaming /tr " + "\"" + PYTHON_PATH + "pythonw.exe " \
                           + WORK_DIRECTORY + "client.py" + "\""

    print("\nAutorun command for Autostreaming client app:")
    print(schedule_run_command)
    print()

    resp = {
        "mqtt": mqtt_creds,
        "obsws": obsws_creds
    }

    return resp


def create_config(conf: dict):
    with open("config.json", "w") as f:
        json.dump(conf, f)


# find path to obs64.exe in disk C:\
def get_obs_path() -> str:
    path = ""

    for root, _, files in os.walk("C:\\"):
        if "obs64.exe" in files:
            path = os.path.join(root)
            break

    return path


PYTHON_PATH = sys.executable.rstrip("python.exe")
WORK_DIRECTORY = os.getcwd() + "\\"

if check_configure(WORK_DIRECTORY):
    print("Reading configure...")

    with open(WORK_DIRECTORY + "config.json") as f:
        config = json.load(f)

    print("File was read successfully!")
else:
    print("Create configure file...")
    default_conf = {
        "obs_path": "",
        "update_loop_time": 1,
        "obs_name": "",
        "mqtt": {
            "host": "0.0.0.0",
            "port": 1883,
            "keep_alive_time": 60,
            "state_topic": "autostream/obs_state",
            "ping_topic": "autostream/ping_sources"
        },
        "obsws": {
            "host": "0.0.0.0",
            "port": 4455,
        }
    }
    create_config(default_conf)
    config = default_conf.copy()
    print("File was created successfully!")

print("Finding obs.exe file...")
obs_path = get_obs_path()

if obs_path:
    print("obs.exe file was found!")
    config["obs_path"] = obs_path

    creds = main()
    config["mqtt"]["host"] = creds["mqtt"]["host"]
    config["mqtt"]["port"] = creds["mqtt"]["port"]

    config["obsws"]["host"] = creds["obsws"]["host"]
    config["obsws"]["port"] = creds["obsws"]["port"]

    config["obs_name"] = creds["obsws"]["host"] + ":" + str(creds["obsws"]["port"])

    print("Writing information...")
    create_env_file(creds["mqtt"]["username"], creds["mqtt"]["password"], creds["obsws"]["password"])
    create_config(config)
    print("Successfully completed!")
else:
    exit("Error: obs.exe file was not found!")
