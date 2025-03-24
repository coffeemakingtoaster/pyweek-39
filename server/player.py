import json
import logging
from typing import List
from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from dataclasses import asdict

from shared.types.player_info import PlayerInfo
from shared.types.status_message import GameStatus, StatusMessages, game_status_factory
from shared.utils.validation import parse_player_info

class Player:
    def __init__(self,player_id: str, player_name: str, websocket: WebSocket) -> None:
        self.ws: WebSocket = websocket
        self.id = player_id
        self.name = player_name
        self.logger = logging.getLogger(f"{__name__}-{self.id}")
        self.messages: List[PlayerInfo] = []
        # TODO: add properties

    async def send_player_info(self, player_info):
        await self.ws.send_text(json.dumps(asdict(player_info)))

    async def send_control_message(self, message: GameStatus):
        self.logger.debug(asdict(message))
        await self.ws.send_text(json.dumps(asdict(message, dict_factory=game_status_factory)))

    async def receive_data(self):
        msg = await self.ws.receive()
        if "text" not in msg:
            self.logger.warning("Invalid payload received")
            return None
        parsed_msg = parse_player_info(msg["text"]) 
        if parsed_msg is None:
            self.logger.warning("Invalid payload received")
            return
        self.messages.append(parsed_msg)

    def __has_message(self) -> bool:
        return len(self.messages) > 0

    def get_last_message(self) -> PlayerInfo | None:
        if self.__has_message():
            msg = self.messages.pop(-1)
            self.messages.clear()
            return msg
        return None

    def is_still_in_match(self) -> bool:
        return self.ws.client_state != WebSocketState.DISCONNECTED

    async def declare_victor(self):
        await self.send_control_message(GameStatus(StatusMessages.VICTORY))

    async def declare_loser(self):
        await self.send_control_message(GameStatus(StatusMessages.DEFEAT))

    async def disconnect(self):
        await self.ws.close()
