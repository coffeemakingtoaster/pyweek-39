from game.const.player import MOVEMENT_SPEED
from game.entities.base_entity import EntityBase

class Player(EntityBase):
    def __init__(self) -> None:
        super().__init__("Player")

        self.id = "player"
        self.move_speed = MOVEMENT_SPEED
        self.movement_status = {"forward": 0, "backward": 0, "left": 0, "right": 0}

        # Keybinds for movement
        self.accept("a", self.set_movement_status, ["left"])
        self.accept("a-up", self.unset_movement_status, ["left"])
        self.accept("d", self.set_movement_status, ["right"])
        self.accept("d-up", self.unset_movement_status, ["right"])
        self.accept("w", self.set_movement_status, ["forward"])
        self.accept("w-up", self.unset_movement_status, ["forward"])
        self.accept("s", self.set_movement_status, ["backward"])
        self.accept("s-up", self.unset_movement_status, ["backward"])

        '''
        self.model = Actor("assets/models/MapObjects/Player/Player.bam",
                           {"Turn": "assets/models/MapObjects/Player/Player-Turn.bam",
                            "TurnBack": "assets/models/MapObjects/Player/Player-TurnBack.bam"})
        self.model.setPos(0, 0, MOVEMENT.PLAYER_FIXED_HEIGHT)
        self.model.reparentTo(render)
        '''

        #self.__add_player_collider()
        #self.holding.model.setPos(0, -0.4, 0.76)
        #self.holding.model.reparentTo(self.model)

    def set_movement_status(self, direction):
        self.movement_status[direction] = 1

    def unset_movement_status(self, direction):
        self.movement_status[direction] = 0

    def update(self, dt):
        self.logger.debug(f"tick {dt}")

    def get_current_state(self):
        """Current state to send via network"""
        return {"health": "yes"}
