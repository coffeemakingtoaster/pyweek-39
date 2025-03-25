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

    async def send_player_info(self, player_info):
        await self.ws.send_text(json.dumps(asdict(player_info)))

    async def send_control_message(self, message: GameStatus):
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
        if len(self.messages) > 0:
            # Do not overwrite attack package
            if self.messages[-1].is_attacking or self.messages[-1].is_jumping:
                if parsed_msg.is_attacking or parsed_msg.is_jumping:
                    # This obscured the actual timings of the second priority package
                    # However this is fine for now as this case is very rare and timing changes should be marginal
                    self.messages[-1].is_attacking = parsed_msg.is_attacking or self.messages[-1].is_attacking
                    self.messages[-1].is_jumping = parsed_msg.is_jumping or self.messages[-1].is_jumping
                else:
                    self.logger.debug("Threw package out for priority package")
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
