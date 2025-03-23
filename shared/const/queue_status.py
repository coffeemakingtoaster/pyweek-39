from enum import Enum

class QueueStatus(Enum):
    IN_QUEUE = "in_queue"
    MATCHED = "matched"
    IN_GAME = "in_game"
    UNKNOWN = "unknown"

