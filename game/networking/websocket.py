from dataclasses import asdict
import logging
from game.const.networking import HOST
from ws4py.client.threadedclient import WebSocketClient
import json

from shared.types.player_info import PlayerInfo

class MatchWS(WebSocketClient):
    def __init__(self, match_id, player_id, player_name, recv_callback,protocols=None, extensions=None, heartbeat_freq=None, ssl_options=None, headers=None, exclude_headers=None):
        self.url = f"ws://{HOST}/match/{match_id}/{player_id}/{player_name}"
        super().__init__(self.url, protocols, extensions, heartbeat_freq, ssl_options, headers, exclude_headers)
        self.recv_cb = recv_callback
        self.logger = logging.getLogger("")
        self.connected = False
        self.connect()
        self.last_packet: PlayerInfo = PlayerInfo()

    def opened(self):
        self.logger.info("Match connection established...")
        self.connected = True
        
    def closed(self, code, reason=None):
        self.logger.warning(f"Match connection closed (reason={reason if reason is not None else 'unspecified'}, code={code})")
        self.connected = False

    def send_game_data(self, data: PlayerInfo):
        if not self.connected:
            self.logger.error("Tried to send websocket data but connection was not yet established.")
            return
        # Don't send duplicate packages
        if self.last_packet.__hash__() == data.__hash__():
            return
        self.send(json.dumps(asdict(data)))
        self.last_packet = data

    def received_message(self, message):
        if message.is_text:
            recvStr = message.data.decode("utf-8")
            self.recv_cb(recvStr)
