import logging
from time import time
from game.const.networking import HOST, HOST_IS_SECURE, TIME_BETWEEN_PACKAGES_IN_S
from ws4py.client.threadedclient import WebSocketClient

from shared.types.player_info import PlayerInfo

def get_ws_protocol() -> str:
    if HOST_IS_SECURE:
        return "wss"
    return "ws"

class MatchWS(WebSocketClient):
    def __init__(self, match_id, player_id, player_name, recv_callback,protocols=None, extensions=None, heartbeat_freq=None, ssl_options=None, headers=None, exclude_headers=None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Sending {player_name}")
        self.url = f"{get_ws_protocol()}://{HOST}/match/{match_id}/{player_id}/{player_name}"
        super().__init__(self.url, protocols, extensions, heartbeat_freq, ssl_options, headers, exclude_headers)
        self.recv_cb = recv_callback
        self.connected = False
        self.connect()
        self.last_packet: PlayerInfo = PlayerInfo()
        self.last_packet_time = time()

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
        if self.last_packet.__hash__() == data.__hash__() and time() - self.last_packet_time > (TIME_BETWEEN_PACKAGES_IN_S * 4):
            return

        self.send(data.to_bytes(), binary=True)
        self.last_packet = data
        self.last_packet_time = time()

    def received_message(self, message):
        if message.is_text:
            recvStr = message.data.decode("utf-8")
            self.recv_cb(recvStr)
        else:
            self.recv_cb(message.data)
