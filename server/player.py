import json
from fastapi import WebSocket
from fastapi.websockets import WebSocketState

class Player:
    def __init__(self,player_id: str, websocket: WebSocket) -> None:
        self.ws: WebSocket = websocket
        self.id = player_id
        # TODO: add properties

    async def send_data(self, data):
        await self.ws.send(data)

    async def send_message(self, message: str):
        await self.ws.send_text(json.dumps({"message": message}))

    async def receive_data(self):
        return await self.ws.receive()

    def is_still_in_match(self) -> bool:
        return self.ws.client_state != WebSocketState.DISCONNECTED

    async def declare_victor(self, caused_by_victory=True):
        if caused_by_victory:
            await self.send_message("You won!")
        else:
            await self.send_message("Enemy left or disconnected...you are now the winner :)")

    async def disconnect(self):
        await self.ws.close()
