from game.const.events import GUI_UPDATE_LATENCY
from game.const.networking import POSITION_DIFF_THRESHOLD
from game.const.player import BASE_HEALTH, GRAVITY, JUMP_VELOCITY, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from direct.actor.Actor import Actor
from game.helpers.helpers import *
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere, Vec2, TextNode
from shared.types.player_info import PlayerInfo
from game.utils.name_generator import generate_name

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
        self.initial_jump_velocity = 100
        self.is_puppet = is_puppet
        self.match_timer = 0.0
        self.vertical_velocity = 0.0

        self.name = generate_name()
        self.name_tag = None
        self.name_tag_node = None

        self.__build()

        self.movement_vector = Vec3(0,0,0)
        self.correction_vector = Vec3(0,0,0)
        self.health = BASE_HEALTH

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

        self.__add_name_tag()

    def __add_name_tag(self):
        self.name_tag = TextNode(f"{self.id}-name")
        self.name_tag_node = self.body.attachNewNode(self.name_tag)
        self.name_tag_node.setScale(1.0)
        self.__update_name()

    def __update_name(self):
        if self.name_tag is not None and self.name_tag_node is not None:
            self.name_tag.setText(self.name)
            self.logger.info(f"Enemy now named {self.name} ({self.name_tag.getWidth()})")
            self.name_tag_node.setPos(-(self.name_tag.getWidth()/2),0,1)

    def set_name(self, name: str):
        self.name = name
        self.__update_name()

    def jump(self, start_time: float = 0.0):
        if start_time == 0.0 and not self.is_puppet:
            self.vertical_velocity = JUMP_VELOCITY
            return
        offset = self.match_timer - start_time
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        # calc current jump pos based on time offset
        # base velocity - gravity * offset
        self.vertical_velocity = JUMP_VELOCITY - (GRAVITY * offset)
        self.body.setZ(self.body.getZ() + (self.vertical_velocity * offset))

    def stab(self, start_time: float = 0.0):
        self.logger.debug("Starting enemy stab")
        # AI controlled
        if start_time == 0.0 and not self.is_puppet:
            self.sword.play("stab")
            return
        offset = self.match_timer - start_time
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
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
            self.logger.debug("Received stab packet")
            self.stab(update.action_offset)
        if update.is_jumping:
            self.logger.debug("Received jump packet")
            self.jump(update.action_offset)
        if update.is_jumping or update.is_attacking:
            return
        # Use the locally calculated z coord to stop slight jittering midair
        networkPos = Vec3(update.position.x, update.position.y, self.body.getZ())
        network_to_local_delta = (networkPos - self.body.getPos())
        # Hard correction
        if  network_to_local_delta.length() > (POSITION_DIFF_THRESHOLD * 2):
            self.body.setFluidPos(networkPos)
            self.correction_vector.set(0,0,0)
        # Soft correction
        elif  network_to_local_delta.length() > POSITION_DIFF_THRESHOLD:
            #self.logger.debug(f"Adjusted position because delta was {network_to_local_delta.length()} (>{POSITION_DIFF_THRESHOLD})")
            self.correction_vector = network_to_local_delta
        else:
            self.correction_vector.set(0,0,0)
        # The vector is normalized when sending it
        self.movement_vector = Vec3(update.movement.x , update.movement.y, 0)
        assert (Vec2(update.movement.x , update.movement.y).length() == self.move_speed 
                or Vec2(update.movement.x , update.movement.y).length() == 0)
        # This is not the correct labelling...I am aware but idc
        self.head.setHpr(update.lookDirection.x, update.lookDirection.y, update.lookDirection.z)
        self.body.setHpr(update.bodyRotation.x, update.bodyRotation.y, update.bodyRotation.z)

    def start_match_timer(self):
        self.match_timer = 0.0

    def __apply_gravity(self, dt):
        if self.vertical_velocity == 0:
            return
        self.vertical_velocity -= (GRAVITY * dt)

        if self.body.getZ() <= 0.5 and self.vertical_velocity < 0:
            self.vertical_velocity = 0 
            # This is the base height -> magic number
            self.body.setZ(0.5)
            
    def update(self, dt):
        self.match_timer += dt
        self.__apply_gravity(dt)
        flat_move = Vec2(self.movement_vector.x, self.movement_vector.y) * dt
        flat_move.x += self.correction_vector.x * dt
        flat_move.y += self.correction_vector.y * dt
        self.body.setFluidPos(self.body, Vec3(flat_move.x, flat_move.y, self.vertical_velocity * dt))
