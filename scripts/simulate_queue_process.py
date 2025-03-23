import asyncio
import requests
import uuid
import time
from websockets.asyncio.client import connect
from websockets.exceptions import ConnectionClosedOK

def join_queue():
    id = str(uuid.uuid4())
    url = 'http://localhost:3000/queue'
    body = {'player_id': id}
    res = requests.post(url, json = body)
    assert res.status_code == 201
    return id

def get_queue_status(id):
    res = requests.get(f"http://localhost:3000/queue/{id}")
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
    async with connect(f"ws://localhost:3000/match/{match_id}/{player_id}") as websocket:
        while True:
            try:
                message = await websocket.recv()
                print(message)
                if ready:
                    await websocket.send(message)
                if "Starting" in message:
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



