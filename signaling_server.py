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
    
class Signaling:
    def __init__(self):
        pass
    
    def channel_log(self, channel, t, message):
        print("channel(%s) %s %s" % (channel.label, t, message))


    def channel_send(self, channel, message):
        self.channel_log(channel, ">", message)
        channel.send(message)
    
    async def consume_signaling(self, pc, signaling):
        while True:
            obj = await signaling.receive()

            if isinstance(obj, RTCSessionDescription):
                await pc.setRemoteDescription(obj)

                if obj.type == "offer":
                    # send answer
                    await pc.setLocalDescription(await pc.createAnswer())
                    await signaling.send(pc.localDescription)
            elif isinstance(obj, RTCIceCandidate):
                await pc.addIceCandidate(obj)
            elif obj is BYE:
                print("Exiting")
                break
            
    time_start = None


    def current_stamp():
        global time_start

        if time_start is None:
            time_start = time.time()
            return 0
        else:
            return int((time.time() - time_start) * 1000000)


    async def run_answer(self, pc, signaling):
        await signaling.connect()

        @pc.on("datachannel")
        def on_datachannel(channel):
            self.channel_log(channel, "-", "created by remote party")

            @channel.on("message")
            def on_message(message):
                self.channel_log(channel, "<", message)

                if isinstance(message, str) and message.startswith("ping"):
                    # reply
                    self.channel_send(channel, "pong" + message[4:])

        await self.consume_signaling(pc, signaling)


    async def run_offer(self, pc, signaling):
        await signaling.connect()

        channel = pc.createDataChannel("chat")
        self.channel_log(channel, "-", "created by local party")

        async def send_pings():
            while True:
                self.channel_send(channel, "ping %d" % self.current_stamp())
                await asyncio.sleep(1)

        @channel.on("open")
        def on_open():
            asyncio.ensure_future(send_pings())

        @channel.on("message")
        def on_message(message):
            self.channel_log(channel, "<", message)

            if isinstance(message, str) and message.startswith("pong"):
                elapsed_ms = (self.current_stamp() - int(message[5:])) / 1000
                print(" RTT %.2f ms" % elapsed_ms)

        # send offer
        await pc.setLocalDescription(await pc.createOffer())
        await signaling.send(pc.localDescription)

        await self.consume_signaling(pc, signaling)