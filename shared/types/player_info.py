from dataclasses import dataclass

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
    lookDirection: Vector | None = None
    bodyRotation: Vector | None = None
    movement: Vector | None = None
    is_attacking: bool = False
    is_jumping: bool = False
    action_offset: float = 0.0
    def __post_init__(self):
        if isinstance(self.position, dict):
            self.position = Vector(**self.position)
        if isinstance(self.movement, dict):
            self.movement = Vector(**self.movement)
        if isinstance(self.lookDirection, dict):
            self.lookDirection = Vector(**self.lookDirection)
        if isinstance(self.bodyRotation, dict):
            self.bodyRotation = Vector(**self.bodyRotation)

    def __safe_hash__(self, val: Vector | None) -> int:
        if val is None:
            return 0
        return val.__hash__()

    def __hash__(self) -> int:
        hash = int(self.health + self.is_attacking + self.is_jumping + self.action_offset)
        hash += self.__safe_hash__(self.position)
        hash += self.__safe_hash__(self.lookDirection)
        hash += self.__safe_hash__(self.bodyRotation)
        hash += self.__safe_hash__(self.movement)
        return hash
