import asyncio
from dataclasses import asdict, dataclass
import json
import requests
import uuid
import time
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK

#HOST = "pyweek-39.ssh-coffee.dev"
HOST = "localhost:3000"

@dataclass
class Vector:
    x: float 
    y: float
    z: float
    length : float

@dataclass
class PlayerInfo:
    position: Vector
    health: float
    lookDirection: Vector
    bodyRotation: Vector
    movement: Vector
    is_attacking: bool
    attack_offset_from_start: float
    def __post_init__(self):
        if isinstance(self.position, dict):
            self.position = Vector(**self.position)
        if isinstance(self.movement, dict):
            self.movement = Vector(**self.movement)
        if isinstance(self.lookDirection, dict):
            self.lookDirection = Vector(**self.lookDirection)
        if isinstance(self.bodyRotation, dict):
            self.bodyRotation = Vector(**self.bodyRotation)

def parse_player_info(raw: str) -> PlayerInfo | None:
    try:
        res = PlayerInfo(**json.loads(raw))
        return res
    except Exception:
        return None

def join_queue():
    id = str(uuid.uuid4())
    url = f'http://{HOST}/queue'
    body = {'player_id': id}
    res = requests.post(url, json = body)
    assert res.status_code == 201
    return id

def get_queue_status(id):
    res = requests.get(f"http://{HOST}/queue/{id}")
    assert res.status_code == 200
    print(f"Player {id} is {res.json()["status"]}")
    return res.json().get("match_id")

def observe_queue_status(id: str):
    res = None
    while res is None:
        res = get_queue_status(id)
        time.sleep(1)
    return res

async def match_ws(player_id, match_id):
    print(f"Connecting for {player_id}")
    ready = False
    proacctive = False
    async with connect(f"ws://{HOST}/match/{match_id}/{player_id}/Peter") as websocket:
        while True:
            try:
                if proacctive and ready:
                    print("sending...")
                    await websocket.send(
                        json.dumps(
                            asdict(
                                PlayerInfo(
                                    health=1.0,
                                    position=Vector(1,1,1,1),
                                    lookDirection=Vector(1,1,1,1),
                                    movement=Vector(1,1,1,1),
                                    bodyRotation=Vector(1,1,1,1),
                                    is_attacking=False,
                                    attack_offset_from_start=0.0
                                )
                            )
                        )
                    )
                    proacctive = False
                message = await websocket.recv()
                print(message)
                if (parsed := parse_player_info(message)) is not None:
                    # Mutation
                    parsed.position.x += 5
                    parsed.position.y += 5
                    message = json.dumps(asdict(parsed))
                if "player1" in message:
                    proacctive = True
                if ready:
                    await websocket.send(message)
                if "lobby_starting" in message:
                    ready = True
                    print("go!")
            except ConnectionClosedOK:
                break

async def main():
    player = join_queue()
    match_id = observe_queue_status(player)

    await match_ws(player, match_id)

if __name__ == "__main__":
    asyncio.run(main())



