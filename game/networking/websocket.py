import logging
from time import time
from game.const.events import DEFEAT_EVENT, GUI_UPDATE_ANTI_PLAYER_NAME, SET_PLAYER_NO_EVENT, START_MATCH_TIMER_EVENT, WIN_EVENT
from game.const.networking import HOST, HOST_IS_SECURE, TIME_BETWEEN_PACKAGES_IN_S
from ws4py.client.threadedclient import WebSocketClient

from shared.types.player_info import PlayerInfo
from shared.types.status_message import StatusMessages
from shared.utils.validation import parse_game_status, parse_player_info

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

    def __handle_control_message(self, raw: str):
        game_status = parse_game_status(raw)
        assert game_status is not None
        match game_status.message:
            case StatusMessages.DEFEAT.value:
                messenger.send(DEFEAT_EVENT)
            case StatusMessages.VICTORY.value:
                messenger.send(WIN_EVENT)
            case StatusMessages.PLAYER_NAME.value:
                messenger.send(GUI_UPDATE_ANTI_PLAYER_NAME, [game_status.detail])
            case StatusMessages.PLAYER_1.value:
                messenger.send(SET_PLAYER_NO_EVENT, [StatusMessages.PLAYER_1])
            case StatusMessages.PLAYER_2.value:
                messenger.send(SET_PLAYER_NO_EVENT, [StatusMessages.PLAYER_2])
            case StatusMessages.LOBBY_STARTING.value:
                messenger.send(START_MATCH_TIMER_EVENT)
            case _:
                self.logger.warning(f"Status message contained status {game_status.message} which is not implemented")


    def received_message(self, message):
        if message.is_text:
            recvStr = message.data.decode("utf-8")
            self.__handle_control_message(recvStr)
        else:
            player_info = parse_player_info(message.data)
            assert player_info is not None
            self.recv_cb(player_info)
