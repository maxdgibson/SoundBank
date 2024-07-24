### This is an outdated file and is no longer used. However, I keep it for reference. 



import os
import json
import time
from moviepy.editor import AudioFileClip
from pytube import Search, YouTube

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

# Playlists data structure
playlists = load_playlists(playlists_file)

# Function to add a song to a playlist
def add_song_to_playlist(playlist_name, song_path):
    if playlist_name not in playlists:
        playlists[playlist_name] = []
    if song_path not in playlists[playlist_name]:
        playlists[playlist_name].append(song_path)
        save_playlists(playlists, playlists_file)

# Function to play songs from a playlist
def play_playlist(playlist_name):
    if playlist_name in playlists:
        for song in playlists[playlist_name]:
            play_audio(song)
    else:
        print(f"Playlist '{playlist_name}' does not exist.")

# Function to play an audio file
def play_audio(file_path):
    print(f"Playing {file_path}")
    audio = AudioFileClip(file_path)
    audio.preview()

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

# Function to handle instruction strings
def handle_instruction(instruction):
    try:
        playlist_name, song_title = instruction.split('", "')
        playlist_name = playlist_name.strip('"')
        song_title = song_title.strip('"')
        song_path = os.path.join(songs_directory, song_title + ".mp4")
        
        if not os.path.exists(song_path):
            print(f"Song '{song_title}' not found locally. Downloading...")
            song_path = download_song(song_title)
        
        if song_path:
            add_song_to_playlist(playlist_name, song_path)
        else:
            print(f"Failed to download song '{song_title}'.")
    except ValueError:
        print("Invalid instruction format. Use '\"PlaylistName\", \"SongTitle\"'.")

# Example usage: Add song to playlist based on instruction string
instruction = '"Pop", "Emanuel Andrea Bocelli"'
handle_instruction(instruction)

# Example usage: play songs from the "Pop" playlist
play_playlist("Pop")
