import os
import vlc
import RPi.GPIO as GPIO
import json
import time
import threading
import subprocess


# Define the function to run main.py
def run_main():
    os.system('python3 main.py')


# Function to run musicQueueRaspPi.py
def run_music_queue():
    global current_process
    current_process = subprocess.Popen(['python3', 'musicQueueRaspPi.py'])


# Function to stop the musicQueueRaspPi.py process
def stop_music_queue():
    global current_process
    if current_process is not None:
        current_process.terminate()
        current_process.wait()
        current_process = None


# GPIO Pin Definitions (Physical pin numbers)
BUTTON1_PIN = 18
BUTTON2_PIN = 22
BUTTON3_PIN = 21
SWITCH_PIN = 12  # Pin for the switch

# Initialize GPIO
GPIO.setmode(GPIO.BOARD)


def setup_gpio(pin, direction, pull_up_down=GPIO.PUD_DOWN):
    try:
        GPIO.setup(pin, direction, pull_up_down=pull_up_down)
        print(f"Successfully set up pin {pin}")
    except Exception as e:
        print(f"Error setting up pin {pin}: {e}")


# Load the playlist from JSON
with open('playlists.json') as f:
    playlists = json.load(f)

# Initialize GPIO pins
try:
    setup_gpio(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    setup_gpio(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    setup_gpio(BUTTON3_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    setup_gpio(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
except Exception as e:
    print(f"Error initializing GPIO pins: {e}")
    GPIO.cleanup()
    exit(1)


# Function to play an audio file using VLC
def play_audio(file_path):
    print(f"Playing {file_path}")
    player = vlc.MediaPlayer(file_path)
    player.play()
    return player


# Function to handle button press events
def check_button_press():
    global current_playlist_index, current_song_index, player, is_playing

    # Button 1: Iterate through playlists
    if not GPIO.input(BUTTON1_PIN):
        current_playlist_index = (current_playlist_index + 1) % len(playlists)
        current_song_index = 0  # Reset song index when changing playlist
        print("Switched to Playlist:", list(playlists.keys())[current_playlist_index])
        time.sleep(0.5)  # Debounce delay

    # Button 2: Iterate through songs within playlist
    elif not GPIO.input(BUTTON2_PIN):
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

    # Button 3: Pause or Play current song
    elif not GPIO.input(BUTTON3_PIN):
        if player is not None:
            if is_playing:
                print("Paused")
                is_playing = False
                player.pause()
            else:
                print("Playing")
                is_playing = True
                player.play()


# Initialize global variables
current_playlist_index = 0
current_song_index = 0
player = None
is_playing = False
current_process = None

# Start main.py in its own thread
main_thread = threading.Thread(target=run_main)
main_thread.start()

# Main loop
try:
    last_switch_state = GPIO.input(SWITCH_PIN)
    while True:
        current_playlist = list(playlists.keys())[current_playlist_index]
        playlist_songs = playlists[current_playlist]

        # Ensure playlist and song indices are within range
        if current_playlist_index < len(playlists) and current_song_index < len(playlist_songs):
            current_song = playlist_songs[current_song_index]

            # If player is not created or song ended, create a new player
            if player is None or player.get_state() == vlc.State.Ended:
                player = play_audio(current_song)

            check_button_press()

            # Check if the switch state changes
            current_switch_state = GPIO.input(SWITCH_PIN)
            if current_switch_state != last_switch_state:
                last_switch_state = current_switch_state
                if current_switch_state == GPIO.LOW:
                    print("Switching to musicQueueRaspPi.py")
                    if player is not None and player.get_state() == vlc.State.Playing:
                        player.stop()
                    run_music_queue()
                else:
                    print("Switching to main.py")
                    stop_music_queue()
                    # Resume playing the current song
                    if player is not None and not is_playing:
                        player.play()
                        is_playing = True
                time.sleep(1)  # Debounce delay

        else:
            print("Index out of range.")

        time.sleep(0.1)  # Small delay to reduce CPU usage

except KeyboardInterrupt:
    pass
finally:
    if current_process is not None:
        current_process.terminate()
        current_process.wait()
    GPIO.cleanup()