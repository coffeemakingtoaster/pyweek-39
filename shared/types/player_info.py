from dataclasses import dataclass

@dataclass
class Vector:
    x: float 
    y: float
    z: float
    length : float

@dataclass
class PlayerInfo:
    position: Vector
    health: float
    lookDirection: Vector
    bodyRotation: Vector
    movement: Vector
    is_attacking: bool
    attack_offset_from_start: float
    def __post_init__(self):
        if isinstance(self.position, dict):
            self.position = Vector(**self.position)
        if isinstance(self.movement, dict):
            self.movement = Vector(**self.movement)
        if isinstance(self.lookDirection, dict):
            self.lookDirection = Vector(**self.lookDirection)
        if isinstance(self.bodyRotation, dict):
            self.bodyRotation = Vector(**self.bodyRotation)
