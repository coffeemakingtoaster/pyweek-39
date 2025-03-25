from game.const.player import BASE_HEALTH, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from direct.actor.Actor import Actor
from game.helpers.helpers import *
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere, Vec2
from shared.types.player_info import PlayerInfo

class AntiPlayer(EntityBase):
    def __init__(self, window, is_puppet=False) -> None:
        super().__init__(f"Enemy {'(online)' if is_puppet else '(local)'}")
        self.id = "enemy"
        self.move_speed = MOVEMENT_SPEED
        self.mouse_sens = 0.1 #MOUSE_SENS
        self.movement_status = {"forward": 0, "backward": 0, "left": 0, "right": 0}
        self.window = window
        self.jump_status = "none"
        self.health = BASE_HEALTH
        self.__build()
        self.initial_jump_velocity = 100
        self.is_puppet = is_puppet
        self.match_timer = 0.0

        self.__build()

        self.movement_vector = Vec3(0,0,0)
        self.health = BASE_HEALTH
        self.name = "placeholder"

        if self.is_puppet:
            self.logger.info(f"Created enemy for opponent")
        else:
            self.logger.info(f"Created bot enemy")
 
    def __build(self):
        self.body = Actor(getModelPath("body"))
        self.body.reparentTo(render)
        self.head = Actor(getModelPath("head"))
        self.head.reparentTo(self.body)
        self.head.setPos(0,0,0.52)
        self.sword = Actor(getModelPath("sword"),{"stab":getModelPath("sword-Stab")})
        self.sword.reparentTo(self.head)
    
        self.shoes = Actor(getModelPath("shoes"))
        self.shoes.reparentTo(self.body)
        self.body.setPos(0, 0, 0.5)

    def set_name(self, name: str):
        self.name = name
        self.logger.info(f"Enemy now named {name}")

    def stab(self, start_time: float = 0.0):
        self.logger.debug("Starting enemy stab")
        # AI controlled
        if start_time == 0.0 and not self.is_puppet:
            self.sword.play("stab")
            return
        offset = self.match_timer - start_time
        start_frame = int(offset * 24)
        self.logger.debug(f"Stab started at frame {start_frame}")
        # Animation has 50 frames at 24fps
        # and takes ca. 2sec
        self.sword.play("stab", fromFrame=start_frame)

    def set_state(self, update: PlayerInfo):
        if not self.is_puppet:
            self.logger.error("Tried to update enemy that is not controlled by other player")
            return
        # an attack package does not! contain any other info
        if update.is_attacking:
            self.stab(update.attack_offset_from_start)
            return
        self.body.setPos(update.position.x, update.position.y, update.position.z)
        # The vector is normalized when sending it
        self.movement_vector = Vec3(update.movement.x , update.movement.y, update.movement.z)
        # This is not the correct labelling...I am aware but idc
        self.head.setHpr(update.lookDirection.x, update.lookDirection.y, update.lookDirection.z)
        self.body.setHpr(update.bodyRotation.x, update.bodyRotation.y, update.bodyRotation.z)

    def start_match_timer(self):
        self.match_timer = 0.0
            
    def update(self, dt):
        self.match_timer += dt
        flat_move = Vec2(self.movement_vector.x, self.movement_vector.y).normalized() * dt
        self.body.setPos(self.body, Vec3(flat_move.x, flat_move.y, self.movement_vector.z * dt))
