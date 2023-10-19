import paho.mqtt.client as mqtt
import json


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/autostream")


def publish(client, topic):
    msg = "PING OBS"
    result = client.publish(topic, msg)
    status = result[0]
    if not status:
        print(f"Send {msg} to {topic}")
    else:
        print(f"Failed to send message to topic {topic}")


def on_message(client, userdata, msg):
    if str(msg.payload).startswith("PING DATA:"):
        data = json.load(msg)
        print(msg.topic)
        print(data)


topic = "/autostream"
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("recorder", "recorder2020")
# connect_async to allow background processing
client.connect_async("172.18.130.40", 1883, 60)

client.loop_forever()
