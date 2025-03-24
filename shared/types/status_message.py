from dataclasses import dataclass
from enum import Enum

class StatusMessages(Enum):
    PLAYER_1 = "player1"
    PLAYER_2 = "player2"
    VICTORY = "victory"
    DEFEAT = "defeat"
    PLAYER_NAME = "player_name"
    LOBBY_WAITING = "lobby_waiting"
    TERMINATED = "terminated"
    LOBBY_STARTING = "lobby_starting"

@dataclass
class GameStatus:
    message: StatusMessages 
    """Contain name when player_name"""
    detail: str = ""

def game_status_factory(data):
    def convert_value(obj):
        # Resolve instance value to actual literal value
        if isinstance(obj, Enum):
            return obj.value
        return obj

    return dict((k, convert_value(v)) for k, v in data)
