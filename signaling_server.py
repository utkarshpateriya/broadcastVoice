import asyncio
import time
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, RTCConfiguration, RTCIceServer
from aiortc.contrib.signaling import BYE, add_signaling_arguments, create_signaling

class ConnectionHandler:
    myrtc_ice_server = RTCIceServer(        
        urls="stun:stun.l.google.com:19302"
    )
    
    rtc_conf = RTCConfiguration() 
    rtc_conf.iceServers = [myrtc_ice_server]
    
    def __init__(self):
        self.users = set()
        self.peer_connections = {}
        
    def add_user(self, user_sid):
        self.users.add(user_sid)
        self.peer_connections[user_sid] = RTCPeerConnection(self.rtc_conf)
        
    def remove_user(self, user_sid):
        self.users.remove(user_sid)
        del self.peer_connections[user_sid]
        
    def get_users(self):
        return list(self.users)