"""This module is the beginning of our journey to become Billionaire"""

from fastapi import FastAPI
import socketio
import utils
import config
from signaling_server import ConnectionHandler, Signaling, RTCSessionDescription
from aiortc import RTCPeerConnection
from aiortc.contrib.signaling import add_signaling_arguments, create_signaling
from aiortc.contrib.media import MediaPlayer, RelayStreamTrack, MediaStreamTrack

app = FastAPI()

# Skylar's settings
sio=socketio.AsyncServer(async_mode="asgi",cors_allowed_origins='*')
socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="")

app.mount("/ws", socket_app)

# My settings
# sio=socketio.AsyncServer(async_mode="asgi",cors_allowed_origins='*')
# socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="socketio")
# app.mount("/", socket_app)
peerConnectionMethods = ConnectionHandler()
signaling_server_methods = Signaling()

# media_stream_track : MediaStreamTrack = MediaStreamTrack(player)
# vidplayer = MediaPlayer('./videotrack.mp4')

# relay_stream_track = RelayStreamTrack(player.audio,buffered=True)

@app.get('/health')
def check_health():
    """Test doc string"""
    return "OK"

@sio.on("connect")
async def connect(sid, env):
    """This is a connection"""
    
    print(f"New Client id :{sid} conected")
    
    formatted_message = {
        "id":utils.generate_message_id(),
        "type":"message",
        "payload":"You've joined channel Akame",
        "sender":"server"
    }
    await sio.enter_room(sid, "Akame")
    
    peerConnectionMethods.add_user(sid)
    
    print(f"Peer {sid} has been made with peer connection {peerConnectionMethods.peer_connections[sid]}")
    
    await sio.emit(event="message:channel", data=formatted_message, to=sid)

@sio.on("message")
async def message(sid, message):    
    """This recieves message from Client"""
    print(message)
    # responsible for sending message to broadcast to room
    await sio.emit(event='message:channel',to=config.room, data=message)

@sio.on("media")
async def handle_media(sid, offer):
    player = MediaPlayer('./media_stream.mp3')
    
    user_peer_connection: RTCPeerConnection = peerConnectionMethods.peer_connections[sid]
    # print(f"Offer has been trigerred value -> {offer}")
    track = player.audio
    track.enabled = True
    user_peer_connection.addTrack(player.audio)
    
    # user_peer_connection.on('track', event_listner)
    
    
    remote_description = RTCSessionDescription(sdp=offer['sdp'], type=offer['type'])
    # set description
    await user_peer_connection.setRemoteDescription(remote_description)
    
    answer: RTCSessionDescription = await user_peer_connection.createAnswer()
    
    
    # for transreceiver in user_peer_connection.getTransceivers():
    #     print(transreceiver)
    #     user_peer_connection.addTrack(player.audio)
       

    await user_peer_connection.setLocalDescription(answer)
    
    await sio.emit(event="media", data={
    'sdp': answer.sdp,
    'type': answer.type
    }, to=sid)

@sio.on("disconect")
async def disconnect(sid):
    """Disconects the user"""
    await sio.leave_room(sid, "Akame")