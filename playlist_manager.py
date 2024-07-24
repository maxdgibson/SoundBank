import os
import json
from dotenv import load_dotenv
import paho.mqtt.client as paho
from pytube import Search, YouTube
from paho import mqtt

# Load .env variables
load_dotenv()

# Path to the directory containing the songs
songs_directory = r'C:\Users\Nehemiah Skandera\Desktop\ECE140B\Spotipy\mvp-project-sound-bank\SoundBankFiles'
# Path to the playlists file
playlists_file = 'playlists.json'

# Load existing playlists from the JSON file
def load_playlists(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}

# Save playlists to the JSON file
def save_playlists(playlists, file_path):
    with open(file_path, 'w') as file:
        json.dump(playlists, file, indent=4)

# Function to add a song to a playlist
def add_song_to_playlist(playlist_name, song_path):
    playlists = load_playlists(playlists_file)
    if playlist_name not in playlists:
        playlists[playlist_name] = []
    if song_path not in playlists[playlist_name]:
        playlists[playlist_name].append(song_path)
        save_playlists(playlists, playlists_file)

# Function to download a song from YouTube
def download_song(song_query):
    s = Search(song_query)
    first_result = s.results[0].watch_url

    yt = YouTube(first_result)
    audio_stream = yt.streams.filter(only_audio=True).first()
    if audio_stream:
        song_path = os.path.join(songs_directory, song_query + ".mp4")
        audio_stream.download(output_path=songs_directory, filename=song_query + ".mp4")
        return song_path
    return None

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)
    client.subscribe("songs/add")

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    try:
        playlist_name, song_title = payload.split(', ')
        playlist_name = playlist_name.strip('"')
        song_title = song_title.strip('"')
        song_path = os.path.join(songs_directory, song_title + ".mp4")
        if not os.path.exists(song_path):
            print(f"Song '{song_title}' not found locally. Downloading...")
            song_path = download_song(song_title)
        add_song_to_playlist(playlist_name, song_path)
    except ValueError:
        print("Invalid instruction format. Use '\"PlaylistName\", \"SongTitle\".'")

if __name__ == '__main__':
    load_dotenv()

    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_publish = on_publish
    client.on_subscribe = on_subscribe

    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    client.username_pw_set(username, password)
    client.connect(broker_address, broker_port)

    client.loop_forever()