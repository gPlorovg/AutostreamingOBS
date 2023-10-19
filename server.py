import paho.mqtt.client as mqtt
import json
import time

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/autostream")


def publish(client, topic):
    msg = json.dumps("PING_OBS")
    result = client.publish(topic, msg)
    status = result[0]
    if not status:
        print(f"Send {msg} to {topic}")
    else:
        print(f"Failed to send message to topic {topic}")


def on_message(client, userdata, msg):
    if json.loads(msg.payload) != "PING_OBS":
        print(json.loads(msg.payload))


topic = "/autostream"
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("recorder", "recorder2020")
# connect_async to allow background processing
client.connect_async("172.18.130.40", 1883, 60)
client.loop_start()
while True:
    time.sleep(2)
    publish(client, topic)
