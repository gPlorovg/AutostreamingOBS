import os
import json
import subprocess
import obspython as obs


global OBS_PING_FILE


def find():
    for root, _, files in os.walk("C:\\"):
        if "obs_ping_sources.json" in files:
            return os.path.join(root, "obs_ping_sources.json")


def ping_sources():
    resp = dict()
    for source in obs.obs_enum_sources():
        source_name = obs.obs_source_get_name(source)
        input_address = obs.obs_data_get_string(obs.obs_source_get_settings(source), "input")
        if input_address:
            # if "rtsp://" in input_address:
            cut_address = input_address.split("//")[1].split("/")[0]
            is_online = subprocess.call("ping -n 1 " + cut_address, shell=True)

            resp[source_name] = {
                "address": input_address,
                "is_online": is_online
            }
    resp_json = json.dumps(resp)

    with open(OBS_PING_FILE, "w") as f:
        f.write(resp_json)


def script_description():
    return "Ping all ip cameras"


def script_load(settings):
    global OBS_PING_FILE
    OBS_PING_FILE = find()
    obs.timer_add(ping_sources, 5000)


def script_unload():
    obs.timer_remove(ping_sources)
