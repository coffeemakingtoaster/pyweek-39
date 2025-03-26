from enum import Enum
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

def parse_player_info(raw: bytes) -> PlayerInfo | None:
    try:
        res = PlayerInfo.from_bytes(raw)
        return res
    except Exception:
        return None

def parse_game_status(raw: str) -> GameStatus | None:
    try:
        res = GameStatus(**json.loads(raw))
        return res
    except Exception:
        return None

def enum_friendly_factory(data):
    def convert_value(obj):
        # Resolve instance value to actual literal value
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, list):
            return [convert_value(val) for val in obj]
        return obj

    return dict((key, convert_value(val)) for key, val in data)
