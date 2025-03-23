import json
from typing import Dict
import websockets
from websockets.client import ClientConnection
from game.const.networking import HOST

def get_ws_conn(match_id: str, player_id: str):
    return websockets.connect(f"ws://{HOST}/match/{match_id}/{player_id}")

async def save_send(ws: websockets.ClientConnection, state: Dict):
    await ws.send(json.dumps(state))

async def ws_producer(ws: ClientConnection, callback):
    async for message in ws:
        await callback(message)
