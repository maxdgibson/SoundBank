from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import json
import paho.mqtt.client as paho
from paho import mqtt
from dotenv import load_dotenv
import os
import time

app = FastAPI()
app.mount('/static', StaticFiles(directory='static'), name='static')
queue_list=[]


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

# Print which topic was subscribed to
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

def initialize_playlists_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            json.dump({}, file)
    elif os.stat(file_path).st_size == 0:
        with open(file_path, 'w') as file:
            json.dump({}, file)

@app.get("/playlists")
async def get_playlists():
    # Load existing playlists from the JSON file
    playlists_file = 'playlists.json'
    initialize_playlists_file(playlists_file)
    if os.path.exists(playlists_file):
        with open(playlists_file, 'r') as file:
            try:
                playlists = json.load(file)
                return JSONResponse(content=list(playlists.keys()))
            except json.JSONDecodeError:
                return JSONResponse(content=[])
    else:
        return JSONResponse(content=[])

def on_message(client, userdata, msg):
    global queue_list
    """
        Prints a mqtt message to stdout ( used as callback for subscribe )
        :param client: the client itself
        :param userdata: userdata is set when initiating the client, here it is userdata=None
        :param msg: the message with topic and payload
    """
    print("heyyyyy")
    print(msg.topic)

    if(msg.topic=="queue/state"):
        
        queue_list=json.loads(msg.payload)


@app.get("/")
async def get():
    with open('index.html', 'r') as file:
        return HTMLResponse(file.read())

@app.get("/healthy")
async def healthy():
    return JSONResponse({"healthy":"maybe"})

@app.get("/queuepage")
async def redirect():
    with open('queue.html', 'r') as file:
        return HTMLResponse(file.read())
    
    
@app.post("/download_add")
async def download_add(request: Request):
    data = await request.json()
    print(data)
    playlist = data.get("playlist")
    song = data.get("song")
    print(f"Received request to add song: {song} to playlist: {playlist}")

    if playlist and song:
        # Format the message as required: '"playlist", "song name"'
        formatted_message = f'"{playlist}", "{song}"'
        print(formatted_message)
        client.publish("songs/add", payload=formatted_message, qos=1)
        return {"message": f"Song '{song}' added to the playlist '{playlist}'"}
    else:
        return {"message": "Playlist or song not provided"}

@app.get("/queue")
async def get_queue():
    
    return JSONResponse(content=queue_list)

@app.post("/queue_add")
async def queue_add(request: Request):
    data = await request.json()
    song = data.get("song")

    if song:
        client.publish("queue/songs", payload=song, qos=1)
        time.sleep(3)
        return {"message": "Song added to the queue"}
    else:
        return {"message": "No song provided"}
    

@app.post("/queue_command")
async def queue_command(request: Request):
    data = await request.json()
    command = data.get("command")
    print(command)

    if command:
        client.publish("queue/commands", payload=command, qos=1)
        time.sleep(3)
        return {"message": "command sent"}
    else:
        return {"message": "No command provided"}

if __name__ == '__main__':
    load_dotenv()

    client = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)

    broker_address = os.environ.get('BROKER_ADDRESS')
    broker_port = int(os.environ.get('BROKER_PORT'))
    username = os.environ.get('USER_NAME')
    password = os.environ.get('PASSWORD')

    # Enable TLS for secure connection
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client.connect(broker_address, broker_port)

    client_sub = paho.Client(callback_api_version=paho.CallbackAPIVersion.VERSION1, client_id="", userdata=None, protocol=paho.MQTTv5)
    client_sub.on_connect = on_connect

     # enable TLS for secure connection
    client_sub.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
    # set username and password
    client_sub.username_pw_set(username, password)
    # connect to HiveMQ Cloud on port 8883 (default for MQTT)
    client_sub.connect(broker_address, broker_port)

    client_sub.on_message = on_message
    client_sub.on_publish = on_publish

    # subscribe to all topics of numbers by using the wildcard "#"
    
    client_sub.subscribe("queue/#", qos=0)

    time.sleep(3)


    client_sub.loop_start()

    uvicorn.run(app,host="0.0.0.0", port=8000)
    #change to 8000 when running locally