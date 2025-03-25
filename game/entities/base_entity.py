import logging
from direct.actor.Actor import Actor
from direct.showbase import DirectObject
from abc import abstractmethod

from direct.task.Task import messenger

from game.const.bit_masks import ANTI_PLAYER_BIT_MASK, NO_BIT_MASK, PLAYER_BIT_MASK
from game.const.events import DEFEAT_EVENT, GUI_UPDATE_ANTI_HP, GUI_UPDATE_PLAYER_HP, WIN_EVENT
from game.const.player import BASE_HEALTH, GRAVITY, MOVEMENT_SPEED, POST_HIT_INV_DURATION
from game.helpers.helpers import getModelPath
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere,Vec2,CollisionCapsule,ColorAttrib,CollisionHandlerEvent,CollisionHandlerQueue, BitMask32

class EntityBase(DirectObject.DirectObject):
    def __init__(self, window, id: str, online: bool, name="BaseEntity"):
        super().__init__()
        self.logger = logging.getLogger(name)
        self.id = id
        self.online = online
        self.is_puppet = False
        self.own_collision_mask = PLAYER_BIT_MASK if self.id == "player" else ANTI_PLAYER_BIT_MASK
        self.opposing_collision_mask = ANTI_PLAYER_BIT_MASK if self.id == "player" else PLAYER_BIT_MASK 
        self.move_speed = MOVEMENT_SPEED
        self.health = BASE_HEALTH
        self.inAttack = False
        self.swordLethality = False
        self.window = window

        self.vertical_velocity = 0
        self.match_timer = 0.0

        self.__construct()

        self.collisionHandler = CollisionHandlerEvent()
        self.collisionHandler.addInPattern("%fn-collision-into-%in")

        base.cTrav.addCollider(self.swordHitBoxNodePath, self.collisionHandler)

        head_damage_event = f"{'enemy' if self.id == 'player' else 'player'}-sHbnp-collision-into-{self.id}-hHbnp"
        body_damage_event = f"{'enemy' if self.id == 'player' else 'player'}-sHbnp-collision-into-{self.id}-bHbnp"
        self.accept(head_damage_event, self.handle_head_hit) 
        self.accept(body_damage_event, self.handle_body_hit)
        self.logger.debug(f"Listening to {head_damage_event} and {body_damage_event}")

        self.inv_phase = 0.0
        self.current_hit_has_critted = False

    def __construct(self):
        self.body = Actor(getModelPath("body"))
        self.body.reparentTo(render)
        
        bodyHitBox = CollisionCapsule(0,0,0.4,0,0,0.3,0.3)
        self.bodyHitBoxNodePath = self.body.attachNewNode(CollisionNode(f"{self.id}-bHbnp"))
        self.bodyHitBoxNodePath.node().addSolid(bodyHitBox)
        self.bodyHitBoxNodePath.setCollideMask(self.own_collision_mask)
        self.bodyHitBoxNodePath.show()
        
        self.head = Actor(getModelPath("head"))
        self.head.reparentTo(self.body)
        self.head.setPos(0,0,0.52)
        head_joint = self.head.exposeJoint(None, "modelRoot", "Bone")
        headHitBox = CollisionSphere(0,0.2,0,0.1)
        
        self.headHitBoxNodePath = self.head.attachNewNode(CollisionNode(f"{self.id}-hHbnp"))
        self.headHitBoxNodePath.node().addSolid(headHitBox)
        self.headHitBoxNodePath.setCollideMask(self.own_collision_mask)
        self.headHitBoxNodePath.show()
        self.headHitBoxNodePath.reparentTo(head_joint)
        
        self.sword = Actor(getModelPath("sword"),{"stab":getModelPath("sword-Stab")})
        self.sword.reparentTo(self.head)
       
        sword_joint = self.sword.exposeJoint(None, "modelRoot", "Bone")
        swordHitBox = CollisionCapsule(0, 4, 0, 0, 1, 0, 1)
        self.swordHitBoxNodePath = self.sword.attachNewNode(CollisionNode(f"{self.id}-sHbnp"))
        self.swordHitBoxNodePath.node().addSolid(swordHitBox)
        self.swordHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        self.swordHitBoxNodePath.show()
        self.swordHitBoxNodePath.reparentTo(sword_joint)
    
        self.shoes = Actor(getModelPath("shoes"))
        self.shoes.reparentTo(self.body)
        self.body.setPos(0, 0, 0.5)

    def endAttack(self,task):
        self.inAttack = False
        
    def turnSwordLethal(self,task):
        self.swordLethality = True
        self.swordHitBoxNodePath.node().setCollideMask(self.opposing_collision_mask)
        
    def turnSwordHarmless(self,task):
        self.swordLethality = False
        self.swordHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)

    def take_damage(self, damage_value: int):
        self.health -= damage_value
        self.logger.debug(f"Now at {self.health} HP")
        messenger.send(GUI_UPDATE_PLAYER_HP if self.id == "player" else GUI_UPDATE_ANTI_HP, [self.health])
        # Server handles online win states
        if self.online:
            return
        if self.health == 0:
            if self.id == "player":
                messenger.send(DEFEAT_EVENT)
            else:
                if not self.is_puppet:
                    messenger.send(WIN_EVENT)

    def handle_body_hit(self, entry):
        self.logger.info(f"Ouch! My body! ({self.inv_phase})")
        if self.is_puppet:
            return
        if self.inv_phase <= 0.0:
            self.current_hit_has_critted = False
            self.take_damage(1)
            self.inv_phase = POST_HIT_INV_DURATION

    def handle_head_hit(self, entry):
        self.logger.info("Ouch! My head!")
        # Do not calculate damage for enemy
        if self.is_puppet:
            return
        # Direct head hit
        if self.inv_phase <= 0:
            self.current_hit_has_critted = True
            self.take_damage(2)
            self.inv_phase = POST_HIT_INV_DURATION
        # Hit that hit body first, then head
        elif not self.current_hit_has_critted and self.inv_phase >= 0:
            self.current_hit_has_critted = True
            self.take_damage(1)
        
    def start_match_timer(self):
        self.match_timer = 0.0

    def apply_gravity(self, dt):
        if self.vertical_velocity == 0:
            return
        self.vertical_velocity -= (GRAVITY * dt)

        if self.body.getZ() <= 0.5 and self.vertical_velocity < 0:
            self.vertical_velocity = 0 
            # This is the base height -> magic number
            self.body.setZ(0.5)

    def destroy(self):
        self.ignoreAll()
        if self.body is not None:
            self.body.cleanup()
            self.body.removeNode()

    def update(self, dt):
        if self.inv_phase > 0.0:
            self.inv_phase -= dt
        else:
            self.current_hit_has_critted = False
