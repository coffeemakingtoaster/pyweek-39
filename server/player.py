import json
import logging
from fastapi import WebSocket
from fastapi.websockets import WebSocketState
from dataclasses import asdict

from shared.types.player_info import PlayerInfo
from shared.types.status_message import GameStatus, StatusMessages 
from shared.utils.validation import parse_player_info, enum_friendly_factory

class Player:
    def __init__(self,player_id: str, player_name: str, websocket: WebSocket) -> None:
        self.ws: WebSocket = websocket
        self.id = player_id
        self.name = player_name
        self.logger = logging.getLogger(f"{__name__}-{self.id}")
        self.last_message: PlayerInfo | None = None

    async def send_player_info(self, player_info: PlayerInfo):
        await self.ws.send_bytes(player_info.to_bytes())

    async def send_control_message(self, message: GameStatus):
        await self.ws.send_text(json.dumps(asdict(message, dict_factory=enum_friendly_factory)))

    async def receive_data(self):
        msg = await self.ws.receive()
        if "bytes" not in msg:
            self.logger.warning(f"Invalid payload received {msg}")
            return None
        parsed_msg = parse_player_info(msg["bytes"]) 
        if parsed_msg is None:
            self.logger.warning("Unparseable payload received")
            return
        if self.last_message is None:
            self.last_message = parsed_msg
            return
        # Priority packages are in action!
        if len(self.last_message.actions) > 0:
            # Prepend already saved actions
            parsed_msg.actions = self.last_message.actions + parsed_msg.actions
            parsed_msg.action_offsets = self.last_message.action_offsets + parsed_msg.action_offsets
        self.last_message = parsed_msg

    def flush_last_message(self) -> PlayerInfo | None:
        msg = self.last_message
        self.last_message = None
        return msg
        
    def is_still_in_match(self) -> bool:
        return self.ws.client_state != WebSocketState.DISCONNECTED

    async def declare_victor(self):
        await self.send_control_message(GameStatus(StatusMessages.VICTORY))

    async def declare_loser(self):
        await self.send_control_message(GameStatus(StatusMessages.DEFEAT))

    async def disconnect(self):
        await self.ws.close()
