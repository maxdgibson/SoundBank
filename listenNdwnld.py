import time
import paho.mqtt.client as paho
from paho import mqtt
from pytube import Search, YouTube
from moviepy.editor import *
import os

# Path to save the downloaded files
download_path = r'C:\Users\Nehemiah Skandera\Desktop\ECE140B\Spotipy\mvp-project-sound-bank\SoundBankFiles'

def on_connect(client, userdata, flags, rc, properties=None):
    """
        Prints the result of the connection with a reasoncode to stdout ( used as callback for connect )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param flags: these are response flags sent by the broker
        :param rc: stands for reasonCode, which is a code for the connection result
        :param properties: can be used in MQTTv5, but is optional
    """
    print("CONNACK received with code %s." % rc)


# with this callback you can see if your publish was successful
def on_publish(client, userdata, mid, properties=None):
    """
        Prints mid to stdout to reassure a successful publish ( used as callback for publish )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param properties: can be used in MQTTv5, but is optional
    """
    print("mid: " + str(mid))


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
        Prints a reassurance for successfully subscribing
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param mid: variable returned from the corresponding publish() call, to allow outgoing messages to be tracked
        :param granted_qos: this is the qos that you declare when subscribing, use the same one for publishing
        :param properties: can be used in MQTTv5, but is optional
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def play_audio(file_path):
    audio = AudioFileClip(file_path)
    audio.preview()

def on_message(client, userdata, msg):
    song_query = str(msg.payload)
    print(f"Received song request: {song_query}")

    # Search on YouTube
    s = Search(song_query)
    first_result = s.results[0].watch_url

    # Download audio from the first result
    yt = YouTube(first_result)
    audio_stream = yt.streams.filter(only_audio=True).first()
    if audio_stream:
        audio_stream.download(output_path=download_path)
        print(f"Downloaded: {audio_stream.title}")
    full_file_path = os.path.join(download_path, audio_stream.title + '.mp4')
    play_audio(full_file_path)


client3 = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="uniqueid235", userdata=None, protocol=paho.MQTTv5)
client3.on_connect = on_connect

# enable TLS for secure connection
client3.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client3.username_pw_set("ECE140@UCSD", "Password1")
# connect to HiveMQ Cloud on port 8883 (default for MQTT)

client3.on_subscribe = on_subscribe
client3.connect("777630be8b4a40a182440428578a0533.s1.eu.hivemq.cloud", 8883)
time.sleep(1)
client3.on_message = on_message
client3.subscribe("music/#", qos=0)

client3.loop_forever()  # This will block and continuously listen for incoming messages

