from dataclasses import dataclass, field
from enum import Enum
from typing import List

class PlayerAction(Enum):
    JUMP = 1
    ATTACK_1 = 2
    BLOCK = 3

@dataclass
class Vector:
    x: float 
    y: float
    z: float
    length : float

    def __hash__(self) -> int:
        return int(self.x + self.y + self.z + self.length)

@dataclass
class PlayerInfo:
    position: Vector | None = None
    health: int = 1 # this cannot default to 0 as 0 means defeat :)
    lookRotation: float | None = None
    bodyRotation: float | None = None
    movement: Vector | None = None
    actions: List[PlayerAction] = field(default_factory=lambda: [])
    action_offsets: List[float] = field(default_factory=lambda: [])

    def __post_init__(self):
        if isinstance(self.position, dict):
            self.position = Vector(**self.position)
        if isinstance(self.movement, dict):
            self.movement = Vector(**self.movement)
        assert len(self.actions) == len(self.action_offsets)

    def __safe_hash__(self, val: Vector | None) -> int:
        if val is None:
            return 0
        return val.__hash__()

    def __hash__(self) -> int:
        hash = 0
        hash += int(self.lookRotation) if self.lookRotation is not None else 0
        hash += int(self.bodyRotation) if self.bodyRotation is not None else 0
        hash += self.__safe_hash__(self.position)
        hash += self.__safe_hash__(self.movement)
        hash += sum([val.value for val in self.actions])
        hash += int(sum(self.action_offsets))
        hash += int(self.health)
        return hash
