import logging
from direct.actor.Actor import Actor
from direct.showbase import DirectObject
from abc import abstractmethod

from game.const.player import BASE_HEALTH, GRAVITY, MOVEMENT_SPEED
from game.helpers.helpers import getModelPath
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere,Vec2,CollisionCapsule,ColorAttrib,CollisionHandlerEvent,CollisionHandlerQueue

class EntityBase(DirectObject.DirectObject):
    def __init__(self, window, name="BaseEntity"):
        super().__init__()
        print(name)
        self.logger = logging.getLogger(name)
        self.move_speed = MOVEMENT_SPEED
        self.health = BASE_HEALTH
        self.inAttack = False
        self.swordLethality = False
        self.window = window

        self.vertical_velocity = 0
        self.match_timer = 0.0

        self.__construct()

        self.collisionHandler = CollisionHandlerEvent()
        self.collisionHandler.addInPattern("sHbnp-collision-into")
        self.collisionHandler.addOutPattern("sHbnp-collision-out")

        base.cTrav.addCollider(self.swordHitBoxNodePath, self.collisionHandler)

        self.accept("sHbnp-collision-into", self.handleSwordCollision) 

    def __construct(self):
        self.body = Actor(getModelPath("body"))
        self.body.reparentTo(render)
        
        bodyHitBox = CollisionCapsule(0,0,0.4,0,0,0.3,0.3)
        self.bodyHitBoxNodePath = self.body.attachNewNode(CollisionNode('bHbnp'))
        self.bodyHitBoxNodePath.node().addSolid(bodyHitBox)
        self.bodyHitBoxNodePath.show()
        
        self.head = Actor(getModelPath("head"))
        self.head.reparentTo(self.body)
        self.head.setPos(0,0,0.52)
        head_joint = self.head.exposeJoint(None, "modelRoot", "Bone")
        headHitBox = CollisionSphere(0,0.2,0,0.1)
        
        self.headHitBoxNodePath = self.head.attachNewNode(CollisionNode("hHbnp"))
        self.headHitBoxNodePath.node().addSolid(headHitBox)
        self.headHitBoxNodePath.show()
        self.headHitBoxNodePath.reparentTo(head_joint)
        
        self.sword = Actor(getModelPath("sword"),{"stab":getModelPath("sword-Stab")})
        self.sword.reparentTo(self.head)
       
        sword_joint = self.sword.exposeJoint(None, "modelRoot", "Bone")
        swordHitBox = CollisionCapsule(0, 4, 0, 0, 1, 0, 1)
        self.swordHitBoxNodePath = self.sword.attachNewNode(CollisionNode('sHbnp'))
        self.swordHitBoxNodePath.node().addSolid(swordHitBox)
        self.swordHitBoxNodePath.show()
        self.swordHitBoxNodePath.reparentTo(sword_joint)
    
        self.shoes = Actor(getModelPath("shoes"))
        self.shoes.reparentTo(self.body)
        self.body.setPos(0, 0, 0.5)

    def endAttack(self,task):
        self.inAttack = False
        
    def turnSwordLethal(self,task):
        self.swordLethality = True
        
    def turnSwordHarmless(self,task):
        self.swordLethality = False
        
    def handleSwordCollision(self, entry):
        if self.swordLethality:
            self.logger.debug("dmg")
    
    def handleSwordCollisionEnd(self, entry):
        self.logger.debug(f"no longer colliding with {entry}")

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

    @abstractmethod
    def update(self, dt):
        pass
