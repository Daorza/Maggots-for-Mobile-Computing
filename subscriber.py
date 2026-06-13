import paho.mqtt.client as mqtt
import json

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode())
    print(f"Suhu: {data['temp']} °C | Kelembaban: {data['hum']} %")
client = mqtt.Client()
client.connect("10.30.91.86", 1883)
client.subscribe("iot/sensor")
client.on_message = on_message
client.loop_forever()