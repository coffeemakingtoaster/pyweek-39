import json
import uuid

from shared.types.player_info import PlayerInfo
from shared.types.status_message import GameStatus

def is_valid_uuid(uuid_to_test, version=4) -> bool:
    try:
        # check for validity of Uuid
        uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True

def parse_player_info(raw: str) -> PlayerInfo | None:
    try:
        res = PlayerInfo(**json.loads(raw))
        return res
    except Exception:
        return None

def parse_game_status(raw: str) -> GameStatus | None:
    try:
        res = GameStatus(**json.loads(raw))
        return res
    except Exception:
        return None

