from obswebsocket import obsws, requests


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


# obs websocket connection
obs_host = "localhost"
obs_port = 4455
obs_password = "KERA3InQESizeUSa"
obs = obsws(obs_host, obs_port, obs_password)
obs.connect()
screenshot = obs.call(requests.GetSourceScreenshot(sourceName="Захват окна", imageWidth=100, imageHeight=100, imageFormat="png"))
screenshot_bad = obs.call(requests.GetSourceScreenshot(sourceName="Источник медиа", imageWidth=100, imageHeight=100, imageFormat="png"))
# screenshot = obs.call(requests.SaveSourceScreenshot(sourceName="Захват окна", imageWidth=100, imageHeight=100, imageFormat="png"))
print(screenshot)
print(screenshot_bad)
# print(obs.call(requests.GetVersion()))
# print(ping_sources())
obs.disconnect()
