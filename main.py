"""This module is the beginning of our journey to become Billionaire"""

from fastapi import FastAPI
import socketio
import utils
import config
from signaling_server import ConnectionHandler, RTCSessionDescription
from aiortc import RTCPeerConnection
from aiortc.contrib.media import MediaPlayer

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
    """
    Offer and sid is provided and answer is being emitted from Server
    """
    player = MediaPlayer('./media_stream.mp3')
    
    user_peer_connection: RTCPeerConnection = peerConnectionMethods.peer_connections[sid]
    
    track = player.audio
    track.enabled = True
    user_peer_connection.addTrack(player.audio)
    
    remote_description = RTCSessionDescription(sdp=offer['sdp'], type=offer['type'])
    # set description
    await user_peer_connection.setRemoteDescription(remote_description)
    
    answer: RTCSessionDescription = await user_peer_connection.createAnswer()

    await user_peer_connection.setLocalDescription(answer)
    
    await sio.emit(event="media", data={
    'sdp': answer.sdp,
    'type': answer.type
    }, to=sid)

@sio.on("disconect")
async def disconnect(sid):
    """Disconects the user"""
    await sio.leave_room(sid, "Akame")
    
    
@sio.on("media:offer")
async def media_offer(sid, offer):
    print("media:offer is functionning")
    await sio.emit(event="media:incoming:offer", data=offer, skip_sid=sid, to="Akame")

@sio.on("media:answer")
async def media_offer(sid, offer):
    print("media:answer is functionning")
    await sio.emit(event="media:incoming:answer", data=offer, skip_sid=sid, to="Akame")

@sio.on("new-ice-candidate")
async def new_ice_candidate(sid, icecandidate):
    print("ice candidate-working")
    await sio.emit(event="new-ice-candidate:incoming", data=icecandidate, skip_sid=sid, to="Akame")