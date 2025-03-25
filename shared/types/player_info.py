from dataclasses import dataclass

@dataclass
class Vector:
    x: float 
    y: float
    z: float
    length : float

@dataclass
class PlayerInfo:
    position: Vector | None = None
    health: float = 1.0 # this cannot default to 0 as 0 means defeat :)
    lookDirection: Vector | None = None
    bodyRotation: Vector | None = None
    movement: Vector | None = None
    is_attacking: bool = False
    attack_offset_from_start: float = 0.0
    def __post_init__(self):
        if isinstance(self.position, dict):
            self.position = Vector(**self.position)
        if isinstance(self.movement, dict):
            self.movement = Vector(**self.movement)
        if isinstance(self.lookDirection, dict):
            self.lookDirection = Vector(**self.lookDirection)
        if isinstance(self.bodyRotation, dict):
            self.bodyRotation = Vector(**self.bodyRotation)
