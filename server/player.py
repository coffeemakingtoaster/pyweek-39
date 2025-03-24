import json
import logging
from typing import Dict
from fastapi import WebSocket
from fastapi.websockets import WebSocketState

from shared.types.player_info import PlayerInfo

class Player:
    def __init__(self,player_id: str, websocket: WebSocket) -> None:
        self.ws: WebSocket = websocket
        self.id = player_id
        self.logger = logging.getLogger(f"{__name__}-{self.id}")
        self.messages = []
        # TODO: add properties

    async def send_data(self, data):
        await self.ws.send(data)

    async def send_text(self, data):
        await self.ws.send_text(data)

    async def send_message(self, message: str):
        await self.ws.send_text(json.dumps({"message": message}))

    def __validate_payload_format(self, msg: str):
        try:
            PlayerInfo(**json.loads(msg))
            return True
        except Exception as e:
            return False

    async def receive_data(self):
        msg = await self.ws.receive()
        if "text" not in msg:
            self.logger.warning("Invalid payload received")
            return None
        if not self.__validate_payload_format(msg["text"]):
            self.logger.warning("Invalid payload received")
            return None
        self.messages.append(msg["text"])

    def __has_message(self) -> bool:
        return len(self.messages) > 0

    def get_last_message(self) -> Dict | None:
        if self.__has_message():
            msg = self.messages.pop(-1)
            self.messages.clear()
            return msg
        return None

    def is_still_in_match(self) -> bool:
        return self.ws.client_state != WebSocketState.DISCONNECTED

    async def declare_victor(self, caused_by_victory=True):
        if caused_by_victory:
            await self.send_message("You won!")
        else:
            await self.send_message("Enemy left or disconnected...you are now the winner :)")

    async def disconnect(self):
        await self.ws.close()
