import json
import logging
from typing import Dict
from websockets.sync.client import ClientConnection, connect
from game.const.networking import HOST

LOGGER = logging.getLogger(__name__)

def get_ws_conn(match_id: str, player_id: str):
    LOGGER.info("Setting up ws connection")
    return connect(f"ws://{HOST}/match/{match_id}/{player_id}")

async def save_send(ws: ClientConnection, state: Dict):
    await ws.send(json.dumps(state))

def ws_producer(ws: ClientConnection, callback):
    for message in ws:
        callback(message)
