import RPi.GPIO as GPIO
import subprocess
import time
import vlc
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
load_dotenv()

broker_address = os.getenv('BROKER_ADDRESS')
broker_port = int(os.getenv('BROKER_PORT'))
username = os.getenv('USER_NAME')
password = os.getenv('PASSWORD')

# Initialize the MQTT Client
mqtt_client = mqtt.Client("MusicQueueController")
mqtt_client.username_pw_set(username, password)

# Connect to the MQTT Broker
def connect_to_broker():
    try:
        mqtt_client.connect(broker_address, broker_port, 60)
        mqtt_client.loop_start()
        print("Connected to MQTT Broker")
    except Exception as e:
        print(f"Failed to connect to MQTT Broker: {e}")

# Function to publish messages to MQTT
def publish_command(command):
    topic = 'queue/commands'
    mqtt_client.publish(topic, command)
    print(f"Published '{command}' to '{topic}'")

# Pin definitions
BUTTON1_PIN = 18
BUTTON2_PIN = 22
BUTTON3_PIN = 21
SWITCH_PIN = 12  # Pin for the switch

# Setup GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

current_script_process = None

def play_audio(file_path):
    print(f"Playing {file_path}")
    player = vlc.MediaPlayer(file_path)
    player.play()
    return player

def run_script(script_name):
    global current_script_process
    if current_script_process:
        current_script_process.kill()
    current_script_process = subprocess.Popen(['python', script_name])

def button_action(button_pin):
    global current_playlist_index, current_song_index, player, is_playing
    switch_state = GPIO.input(SWITCH_PIN)
    if button_pin == BUTTON1_PIN:
        if switch_state:
            if player is not None:
                if is_playing:
                    print("Paused")
                    is_playing = False
                    player.pause()
                else:
                    print("Playing")
                    is_playing = True
                    player.play()
        else:
            print("Toggling play for the Queue")
            publish_command("toggle_play")
            # Add functionality for Button 1, Switch State 2 here
    elif button_pin == BUTTON2_PIN:
        if switch_state:
            current_playlist_index = (current_playlist_index + 1) % len(playlists)
            current_song_index = 0  # Reset song index when changing playlist
            print("Switched to Playlist:", list(playlists.keys())[current_playlist_index])
            time.sleep(0.5)  # Debounce delay
        else:
            print("Rewinding Song to the Begining in Queue")
            publish_command("restart")
            # Add functionality for Button 2, Switch State 2 here
    elif button_pin == BUTTON3_PIN:
        if switch_state:
            current_playlist = list(playlists.keys())[current_playlist_index]
            current_song_index = (current_song_index + 1) % len(playlists[current_playlist])
            print("Switched to Song:", playlists[current_playlist][current_song_index])
            time.sleep(0.5)  # Debounce delay
            # Stop current player if it's playing
            if player is not None and player.get_state() == vlc.State.Playing:
                player.stop()
            time.sleep(0.1)  # Small delay to ensure player is stopped
            # Play the new song
            current_song = playlists[current_playlist][current_song_index]
            player = play_audio(current_song)
        else:
            print("Skipping to next song in the queue")
            publish_command("skip")
            # Add functionality for Button 3, Switch State 2 here

# Store the last state of each button to implement debouncing
last_button_states = {BUTTON1_PIN: False, BUTTON2_PIN: False, BUTTON3_PIN: False}

try:
    while True:
        # Continuously check the switch state and run the corresponding script
        switch_state = GPIO.input(SWITCH_PIN)
        if switch_state:
            run_script('main.py')
        else:
            run_script('musicQueueRaspPi.py')

        # Check each button and perform actions with debouncing
        for button in (BUTTON1_PIN, BUTTON2_PIN, BUTTON3_PIN):
            current_state = GPIO.input(button)
            if current_state and not last_button_states[button]:
                button_action(button)
            last_button_states[button] = current_state

        time.sleep(0.1)  # Small delay to debounce and reduce CPU usage

except KeyboardInterrupt:
    print("Program exited gracefully")

finally:
    GPIO.cleanup()  # Clean up GPIO on normal exit
