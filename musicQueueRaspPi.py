import os
import threading
import json
import vlc
import time
import paho.mqtt.client as paho
from dotenv import load_dotenv
from pytube import Search, YouTube

#note to any reader, the handle_end_of_song or anythign to do with the events of an end of song
#crash the vlc media player instance and does not allow you to send any information to it
#meaning we as a group had to write a janky work around called monitor_song_end which checks
#how much time is left then calls the skip funciton becasue that all worked great.

load_dotenv()

broker_address = os.getenv('BROKER_ADDRESS')
broker_port = int(os.getenv('BROKER_PORT'))
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')

music_queue_list=[]

#DOWNLOAD_PATH = r'C:\Users\mtyse\Documents\ece140\ECE140B\Tech2\mvp-project-sound-bank\soundbankfiles'
#DOWNLOAD_PATH = r'QueueFiles'

#
DOWNLOAD_PATH = r'C:\\Users\\maxdg\\PycharmProjects\\ee140\\mvp-project-sound-bank\\song_folder'
#DOWNLOAD_PATH = r'SoundBankQueue'

def get_first_audio_stream(song_query):
    try:
        s = Search(song_query)
        first_result = s.results[0].watch_url
        yt = YouTube(first_result)
        return yt.streams.filter(only_audio=True).first()
    except Exception as e:
        print(f"Error retrieving '{song_query}': {e}")
        return None

def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)

def on_publish(client, userdata, mid, properties=None):
    print("mid: " + str(mid))

def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def print_queue(self):
    if self.queue:
        print("Current Queue:")
        for song in self.queue:
            print(f" - {song}")
    else:
        print("The queue is empty.")

def on_message(client, userdata, msg):
    if msg.topic == "queue/songs":
        song_query = msg.payload.decode("utf-8").strip()
        print(f"Received song request: {song_query}")
        audio_stream = get_first_audio_stream(song_query)
        if audio_stream:
            music_queue.add_song(audio_stream.title)
        else:
            print(f"Failed to handle song request for '{song_query}'")
    elif msg.topic == "queue/commands":
        command = msg.payload.decode("utf-8").strip().lower()
        print(f"Received command: {command}")
        if command == 'play':
            music_queue.play_audio(music_queue.currently_playing)
            print(f"Playing: {music_queue.currently_playing}")
        elif command == 'toggle_play':
            music_queue.toggle_play()
        elif command == 'stop':
            music_queue.player.stop()
            music_queue.delete_song_file()
            print("Playback stopped")
        elif command == 'skip':
            music_queue.skip()
        elif command == 'next':
            music_queue.play_next()
        elif command == 'restart':
            music_queue.restart()
        elif command == 'test':
            broadcast_queue_state()

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.currently_playing = None
        self.last_song = None  # Reference to the last song played
        self.player = vlc.MediaPlayer()
        self.player_events = self.player.event_manager()
        self.player_events.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_end_of_song)
        #I want to add a reference to self.last_song so that I can use it before handle_end_of_song
        #I think if i then reference it in handle_end_of_Song i need to be abel to access the path
        #and I need it to be moving to the next song so I need the system to not delete the next song up
        #
    def move_song(self, current_index, new_index):
        """Move a song in the queue from current_index to new_index."""
        if 0 <= current_index < len(self.queue) and 0 <= new_index < len(self.queue):
            song = self.queue.pop(current_index)
            self.queue.insert(new_index, song)
            print(f"Moved song from position {current_index} to {new_index}.")
        else:
            print("Invalid index.")
    def add_song(self, song):
        self.queue.append(song)
        print(f"Added '{song}' to the queue.")
        self.download_song(song)
        #download immediately instead
        self.publish_queue_state()
        if not self.currently_playing:
            self.play_next()

    def play_next(self):
        if self.queue:
            # Ensure the previous song file is deleted if it exists
            print("queue exists")
            if self.currently_playing is not None :
                print("deleting old song")
                self.delete_song_file(self.currently_playing)
            print("popping")
            self.currently_playing = self.queue.pop(0)
            #self.download_and_play(self.currently_playing)
            self.play_audio(self.currently_playing)
            self.last_song = self.currently_playing
            self.publish_queue_state()
        else:
            print("No songs")
            self.currently_playing = None
            self.publish_queue_state()

    def download_and_play(self, song):
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        if not os.path.exists(file_path):
            self.download_song(song)
        self.play_audio(song)
        self.last_song = self.currently_playing

    def download_song(self, song):
        audio_stream = get_first_audio_stream(song)
        if audio_stream:
            audio_stream.download(output_path=DOWNLOAD_PATH, filename=song + '.mp4')
            print(f"Downloaded '{song}' to {DOWNLOAD_PATH}.")
        else:
            print(f"Failed to download '{song}'.")

    def play_audio(self, song):
        print("in play_audio")
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        self.player.set_media(vlc.Media(file_path))
        self.player.play()
        time.sleep(1)  # Allow some time for the media to start and gather information
        self.monitor_song_end()

    def monitor_song_end(self):
        #print(str(self.player.get_length()) + " FIND THIS")

        """ Monitors the remaining time of the currently playing song and triggers skip if near end. """
        def monitor():
            while self.player.is_playing():
                time.sleep(1)  # Check every 100ms
                remaining_time = self.player.get_length() - self.player.get_time()
                #print(f"Remaining time: {remaining_time} ms") #trouble shooting
                if remaining_time < 5000:  # Less than 5 second remaining
                    print("Song is about to end. Triggering skip...")
                    self.skip()
                    break

        thread = threading.Thread(target=monitor)
        thread.start()

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            print("Toggled: Playback Paused")
        else:
            self.player.play()
            print("Toggled: Playing Again")
            time.sleep(1)  # Allow some time for the media to start and gather information
            self.monitor_song_end()

    def skip(self):
        print("skipping: " + self.currently_playing)
        if self.player.is_playing():
            self.player.stop()
            self.delete_song_file(self.currently_playing)
            print("Skipping current song...")
        self.play_next()

    def restart(self):
        print("restarting current song")
        self.player.set_time(3) #sets the time to the begining

    def handle_end_of_song(self, event): #this should never be called now
        print("Critical error, restart the soundbank")
        self.play_next_end()

    def play_next_end(self): #this should never be called either
        #delete old song:
        print("about to delete the old song")
        print(self.last_song)
        self.delete_song_file(self.last_song)
        print("deleted song that was just done playing: " + self.last_song)
        #call play next in a way that doesnt fuck the system
        self.currently_playing = self.queue.pop(0)
        print(self.currently_playing)
        #hopefully this works and doesnt shit the bed
        self.play_audio(self.currently_playing)

    def delete_song_file(self, song):
        file_path = os.path.join(DOWNLOAD_PATH, song + '.mp4')
        print(file_path)
        if os.path.exists(file_path):
            print("lalalal")
            # self.player.stop()  # Ensure VLC is not using the file
            # print("stopped player")
            retry_attempts = 3
            for attempt in range(retry_attempts):
                print("Retrying: " + str(attempt))
                try:
                    print("first try os file remove")
                    os.remove(file_path)
                    print(f"Deleted '{file_path}'.")
                    #music_queue_list.pop()
                    break
                except PermissionError:
                    if attempt < retry_attempts - 1:  # Avoid sleeping on the last attempt
                        print(f"Unable to delete file on attempt {attempt + 1}. Retrying...")
                        time.sleep(1)  # Wait a bit before retrying
                    else:
                        print(f"Failed to delete file after {retry_attempts} attempts.")

    def publish_queue_state(self):
        # Initialize the string with the currently playing song if it exists
        if self.currently_playing:
            queue_state = self.currently_playing
        else:
            queue_state = "No song currently playing"

        # Append upcoming songs with semicolon separation
        if self.queue:
            if self.currently_playing:  # Add a semicolon only if there's a currently playing song
                queue_state += ";"
            queue_state += ";".join(self.queue)

        encoded_list = json.dumps(queue_state)
        # Publish the song titles as a single string
        client.publish("queue/state", encoded_list, qos=0)


def broadcast_queue_state():
    for i in music_queue_list:
        print(i)

music_queue = MusicQueue()

client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="uniqueid235", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect
client.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)
client.username_pw_set(username, password=password)
client.connect(broker_address, broker_port)
client.on_subscribe = on_subscribe
client.on_message = on_message
client.subscribe("queue/#", qos=0)
client.loop_forever()
