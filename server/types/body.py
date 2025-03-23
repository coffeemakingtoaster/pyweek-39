from pydantic import BaseModel


class JoinQueueBody(BaseModel):
    player_id: str
