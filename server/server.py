import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from server.matchmaking import MatchMaker
from server.types.body import JoinQueueBody
from shared.const.queue_status import QueueStatus
from shared.utils.validation import is_valid_uuid

LOGGER = logging.getLogger(__name__)

matchMaker = MatchMaker()

app = FastAPI()

@app.post("/queue", status_code=201)
async def new_queue(new_player: JoinQueueBody):
    if not is_valid_uuid(new_player.player_id): 
        raise HTTPException(
            status_code=400,
            detail=f"Provided player id was invalid (Gave: {new_player.player_id} Wants: valid uuid)"
        )
    matchMaker.add_player(new_player.player_id)

@app.delete("/queue/{player_id}")
async def remove_player_from_queue(player_id: str):
    if not is_valid_uuid(player_id): 
        raise HTTPException(
            status_code=400,
            detail="Provided player id was invalid"
        )
    matchMaker.remove_player(player_id)

@app.get("/queue/{player_id}")
async def get_queue_status(player_id: str):
    if not is_valid_uuid(player_id): 
        raise HTTPException(
            status_code=400,
            detail="Provided player id was invalid"
        )
    status, match_id = matchMaker.get_player_status(player_id)
    if status in [QueueStatus.MATCHED, QueueStatus.IN_GAME]:
        return JSONResponse(content={"status": status.value, "match_id": match_id}, status_code=200)
    return JSONResponse(content={"status": status.value}, status_code=200)

@app.websocket("/match/{match_id}/{player_id}/{player_name}")
async def websocket_endpoint(websocket: WebSocket, match_id: str, player_id: str, player_name: str):
    if not matchMaker.is_valid_match_id(match_id):
        LOGGER.info(f"Client connected with invalid match id {match_id}")
        await websocket.close()
        return
    if not is_valid_uuid(player_id):
        LOGGER.info(f"Client connected with invalid player id {player_id}")
        await websocket.close()
        return
    await websocket.accept()
    LOGGER.info("New client connected")
    try:
        match = matchMaker.get_match(match_id)
        await match.accept_player(player_id, player_name, websocket)
        await websocket.close()
    except WebSocketDisconnect:
        LOGGER.info("Client disconnected")
