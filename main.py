import threading
import os
from dotenv import load_dotenv

def run_playlist_manager():
    os.system("python playlist_manager.py")

# def run_app():
#     os.system("python app.py")

def install_requirements():
    os.system("pip install -r requirements.txt")

def check_requirements():
    required_libraries = ['fastapi', 'uvicorn', 'pytube', 'paho-mqtt', 'python-dotenv']
    installed_libraries = os.popen("pip list").read()
    for lib in required_libraries:
        if lib not in installed_libraries:
            return False
    return True

if __name__ == '__main__':
    # Load environment variables
    load_dotenv()

    # Check if requirements are installed
    if not check_requirements():
        # Install the environment requirements
        install_requirements()

    # Create threads for running the scripts
    playlist_manager_thread = threading.Thread(target=run_playlist_manager)
    # app_thread = threading.Thread(target=run_app)

    # Start the threads
    playlist_manager_thread.start()
    # app_thread.start()

    # Wait for both threads to complete
    playlist_manager_thread.join()
    # app_thread.join()
