from moviepy.editor import AudioFileClip
import json

# Function to play songs from a playlist for a specified genre
def play_genre(playlist, genre):
    if genre in playlist:
        print("Genre:", genre)
        for song_path in playlist[genre]:
            play_audio(song_path)
    else:
        print(f"Genre '{genre}' does not exist in the playlist.")

# Function to play an audio file
def play_audio(file_path):
    print(f"Playing {file_path}")
    audio = AudioFileClip(file_path)
    audio.preview()

# Load the playlist from JSON
with open('playlists.json') as f:
    playlist = json.load(f)

# Prompt the user to specify the genre
while True:
    selected_genre = input("Enter the genre you want to play (or 'q' to quit): ")
    if selected_genre.lower() == 'q':
        break
    play_genre(playlist, selected_genre)
