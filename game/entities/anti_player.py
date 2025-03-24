from abc import update_abstractmethods
from game.const.player import BASE_HEALTH, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from direct.actor.Actor import Actor
from game.helpers.helpers import *
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere
from shared.types.player_info import PlayerInfo, Vector

class AntiPlayer(EntityBase):
    def __init__(self, window, is_puppet=False) -> None:
        super().__init__("Enemy")
        self.id = "enemy"
        self.move_speed = MOVEMENT_SPEED
        self.mouse_sens = 0.2 #MOUSE_SENS
        self.movement_status = {"forward": 0, "backward": 0, "left": 0, "right": 0}
        self.camera = camera
        self.window = window
        self.is_puppet = is_puppet
        
        self.actor = Actor(getModelPath("player"))
        self.actor.reparentTo(render)
        self.actor.setPos(0, 0, 1)
        self.movement_vector = Vec3(0,0,0)
        self.health = BASE_HEALTH
        self.name = "placeholder"

        if self.is_puppet:
            self.logger.info(f"Created enemy for opponent")
        else:
            self.logger.info(f"Created bot enemy")

    def set_name(self, name: str):
        self.name = name
        self.logger.info(f"Enemy now named {name}")

    def set_state(self, update: PlayerInfo):
        if not self.is_puppet:
            self.logger.error("Tried to update enemy that is not controlled by other player")
            return
        self.logger.debug(update)
        # Testing offset
        #update.position.z += 5
        self.actor.setPos(update.position.x, update.position.y, update.position.z)
        # The vector is normalized when sending it
        self.movement_vector = Vec3(update.movement.x , update.movement.y, update.movement.z)
        # This is not the correct labelling...I am aware but idc
        self.actor.setHpr(update.lookDirection.x, update.lookDirection.y, update.lookDirection.z)
    
    def update(self, dt):
        self.actor.setPos(self.actor, self.movement_vector * dt)
