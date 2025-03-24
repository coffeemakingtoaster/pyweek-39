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
    movement: Vector
    def __post_init__(self):
        if isinstance(self.position, dict):
            self.position = Vector(**self.position)
        if isinstance(self.movement, dict):
            self.movement = Vector(**self.movement)
        if isinstance(self.lookDirection, dict):
            self.lookDirection = Vector(**self.lookDirection)
