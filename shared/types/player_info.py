from dataclasses import dataclass, field
from enum import Enum
import struct
from typing import List


class PlayerAction(Enum):
    JUMP = 1
    ATTACK_1 = 2
    BLOCK = 3
    SWEEP_1 = 4
    SWEEP_2 = 5

@dataclass
class Vector:
    x: float 
    y: float
    z: float
    length : float

    def to_bytes(self) -> bytes:
        return struct.pack("ffff", self.x, self.y, self.z, self.length)

    @staticmethod
    def from_bytes(data: bytes):
        x, y, z, length = struct.unpack("ffff", data)
        return Vector(x, y, z, length)

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

    def to_bytes(self) -> bytes:
        parts = []
        
        # Pack fixed fields
        fmt = "B i B f B f B"  # Presence flags, health, and rotation values
        parts.append(struct.pack(fmt, 
            1 if self.position else 0,
            self.health,
            1 if self.lookRotation is not None else 0,
            self.lookRotation if self.lookRotation is not None else 0.0,
            1 if self.bodyRotation is not None else 0,
            self.bodyRotation if self.bodyRotation is not None else 0.0,
            1 if self.movement else 0
        ))

        # Serialize optional vectors
        if self.position:
            parts.append(self.position.to_bytes())
        if self.movement:
            parts.append(self.movement.to_bytes())

        # Serialize actions as integers with length prefix
        parts.append(struct.pack("I", len(self.actions)))  # 4-byte length prefix
        for action in self.actions:
            parts.append(struct.pack("B", action.value))  # Each action as 1 byte

        # Serialize action_offsets as floats with length prefix
        parts.append(struct.pack("I", len(self.action_offsets)))  # 4-byte length prefix
        if self.action_offsets:
            parts.append(struct.pack(f"{len(self.action_offsets)}f", *self.action_offsets))

        return b"".join(parts)

    @staticmethod
    def from_bytes(data: bytes):
        offset = 0
        fmt = "B i B f B f B"
        fixed_size = struct.calcsize(fmt)
        values = struct.unpack(fmt, data[:fixed_size])
        offset += fixed_size

        pos_flag, health, look_flag, look_rotation, body_flag, body_rotation, move_flag = values
        pos = Vector.from_bytes(data[offset:offset+16]) if pos_flag else None
        offset += 16 if pos_flag else 0

        move = Vector.from_bytes(data[offset:offset+16]) if move_flag else None
        offset += 16 if move_flag else 0

        actions_len = struct.unpack("I", data[offset:offset+4])[0]
        offset += 4
        actions = [
            PlayerAction(struct.unpack("B", data[offset+i:offset+i+1])[0]) 
            for i in range(actions_len)
        ]
        offset += actions_len

        offsets_len = struct.unpack("I", data[offset:offset+4])[0]
        offset += 4
        action_offsets = list(struct.unpack(f"{offsets_len}f", data[offset:offset + 4 * offsets_len]))
        offset += 4 * offsets_len

        return PlayerInfo(
            position=pos,
            health=health,
            lookRotation=look_rotation if look_flag else None,
            bodyRotation=body_rotation if body_flag else None,
            movement=move,
            actions=actions,
            action_offsets=action_offsets
        )

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

if __name__ == "__main__":
    import json
    from dataclasses import asdict

    def enum_friendly_factory(data):
        def convert_value(obj):
            # Resolve instance value to actual literal value
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, list):
                return [convert_value(val) for val in obj]
            return obj

        return dict((key, convert_value(val)) for key, val in data)

    expected_player = PlayerInfo(
        position=Vector(1.0, 2.0, 3.0, 4.0),
        health=100,
        lookRotation=90.0,
        bodyRotation=45.0,
        movement=Vector(0.1, 0.2, 0.3, 0.4),
        actions=[PlayerAction.JUMP, PlayerAction.ATTACK_1],
        action_offsets=[0.5, 1.2]
    )

    # Serialize and Deserialize
    bytes_data = expected_player.to_bytes()
    actual_player = PlayerInfo.from_bytes(bytes_data)

    assert actual_player.__hash__() == expected_player.__hash__()

    print(f"Old size: {len(json.dumps(asdict(expected_player, dict_factory=enum_friendly_factory)).encode('utf-8'))}")
    print(f"New size: {len(bytes_data)}")
