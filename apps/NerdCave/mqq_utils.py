import paho.mqtt.client as mqtt
import queue
import datetime as dt
import pandas as pd 

import pathlib

class MQTTCONFIG:
    HOST = "192.168.1.23"
    PORT = 1883
    KEEPALIVE = 60
    SUBSCRIPTIONS = ["house/light", "house/toast", "busMonitor/departures", "houseMonitor/temperature"]

def get_configured_mqtt_client(list_messages ):
    client = mqtt.Client()
    client.on_connect = on_connect_closure()
    client.on_message = on_message_closure(list_messages)

    client.connect(MQTTCONFIG.HOST, MQTTCONFIG.PORT, MQTTCONFIG.KEEPALIVE)
    client.loop_start() 
    
    for subs in MQTTCONFIG.SUBSCRIPTIONS:
        print("Subscribed to: " + subs)
        client.subscribe(subs)
    return client 

# The callback for when the client receives a CONNACK response from the server.
def on_connect_closure():
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code "+str(rc))

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        # client.subscribe("$SYS/#")
    return on_connect

# The callback for when a PUBlLISH message is received from the server.
def on_message_closure(list_messages: queue.Queue):
    def on_message(client, userdata, msg):
        df = convert_message_to_pandas(msg)
        save_message_to_csv(df)
        list_messages.put(df)
    return on_message

def convert_message_to_pandas(msg):
    now = dt.datetime.now()
    data = {"Registration Timestamp":[now],"Topic":[msg.topic], "Value": [msg.payload.decode('UTF-8')]}
    df = pd.DataFrame.from_dict(data).set_index("Registration Timestamp")
    return df

def get_message_path(topic):
    path_list = str(pathlib.Path(__file__)).split("/")
    path_list.pop(-1)
    path = "/".join(path_list) + "/data/"

    path = path + topic.replace("/","_") + ".csv"
    return path

def load_topic_df(topic):
    csv_file = get_message_path(topic)
    try:
        print("Loading topic: ", topic, csv_file)
        all_df = pd.read_csv(csv_file).set_index("Registration Timestamp")
    except:
        # There was no file, first entry.
        return pd.DataFrame(columns= ["Registration Timestamp", "Topic", "Value"]).set_index("Registration Timestamp")

    return all_df

def save_message_to_csv(df: pd.DataFrame):
    print (df)
    topic = df["Topic"][0]
    all_df = load_topic_df(topic)
    all_df = pd.concat([all_df, df])
    csv_file = get_message_path(topic)
    all_df.to_csv(csv_file)