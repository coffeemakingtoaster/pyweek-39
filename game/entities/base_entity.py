import logging
from typing import ForwardRef
from direct.actor.Actor import Actor
from direct.showbase import DirectObject
from abc import abstractmethod
import math

from direct.stdpy.threading import current_thread
from direct.task.Task import messenger

from game.const import player
from game.const.bit_masks import ANTI_PLAYER_BIT_MASK, NO_BIT_MASK, PLAYER_BIT_MASK
from game.const.events import DEFEAT_EVENT, GUI_UPDATE_ANTI_HP, GUI_UPDATE_PLAYER_HP, WIN_EVENT
from game.const.player import ALLOWED_WORD_CENTER_DISTANCE, BASE_HEALTH, BLOCK_RANGE_DEG, GRAVITY, MOVEMENT_SPEED, PLAYER_1_SPAWN, PLAYER_2_SPAWN, POST_HIT_INV_DURATION, WORLD_CENTER_POINT
from game.helpers.helpers import getModelPath
from panda3d.core import Vec3, CollisionNode, CollisionSphere, CollisionCapsule, CollisionHandlerEvent, LineSegs, NodePath, Mat3,Quat

from game.utils.scene_graph import traverse_parents_until_name_is_matched
from direct.particles.ParticleEffect import ParticleEffect
from game.helpers.helpers import *
import random

from shared.types.status_message import StatusMessages

class EntityBase(DirectObject.DirectObject):
    def __init__(self, window, id: str, online: bool, name="BaseEntity"):
        super().__init__()
        self.logger = logging.getLogger(name)
        self.id = id
        self.online = online
        self.window = window
        self.is_puppet = False
        self.own_collision_mask = PLAYER_BIT_MASK if self.id == "player" else ANTI_PLAYER_BIT_MASK
        self.opposing_collision_mask = ANTI_PLAYER_BIT_MASK if self.id == "player" else PLAYER_BIT_MASK 
        self.move_speed = MOVEMENT_SPEED
        self.health = BASE_HEALTH
        self.is_in_attack = False
        self.is_in_block = False
        self.has_lethal_sword = False
        self.has_blocking_sword = False
        self.sweep2 = False
        self.is_dashing = False
        self.hit_handled = False
        self.is_block_stunned = False
        self.dashParticles = []
        
        self.setupSounds()

        self.vertical_velocity = 0
        self.match_timer = 0.0

        self.__construct()

        self.collisionHandler = CollisionHandlerEvent()
        self.collisionHandler.addInPattern("%fn-collision-into-%in")

        base.cTrav.addCollider(self.swordHitBoxNodePath, self.collisionHandler)
        
        # Receive damage event -> being hit
        head_damage_event = f"{'enemy' if self.id == 'player' else 'player'}-sHbnp-collision-into-{self.id}-hHbnp"
        body_damage_event = f"{'enemy' if self.id == 'player' else 'player'}-sHbnp-collision-into-{self.id}-bHbnp"
        self.accept(head_damage_event, self.handle_head_damage) 
        self.accept(body_damage_event, self.handle_body_damage)
        self.accept(f"{head_damage_event}-blocked", self.handle_head_damage) 
        self.accept(f"{body_damage_event}-blocked", self.handle_body_damage)

        # Deal damage event -> hitting someone and being blocked
        blocked_head_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-hHbnp-blocked"
        blocked_body_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-bHbnp-blocked"
        self.accept(blocked_head_hit_event, self.handle_blocked_hit)
        self.accept(blocked_body_hit_event, self.handle_blocked_hit)
        
        # Deal damage event -> hitting someone and being blocked
        head_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-hHbnp"
        body_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-bHbnp"
        self.accept(head_hit_event, self.handle_hit)
        self.accept(body_hit_event, self.handle_hit)

        self.hitBlocked = False
        self.inv_phase = 0.0
        self.current_hit_has_critted = False

    def setupSounds(self):
        self.sweepingSounds = []
        self.hitSounds = []
        for i in range(7):
            self.sweepingSounds.append(base.loader.loadSfx(getSoundPath("swipe"+str(i+1))))
        for i in range(4):
            self.hitSounds.append(base.loader.loadSfx(getSoundPath("hit"+str(i+1))))

    def set_player(self, playerId: StatusMessages):
        assert playerId in [StatusMessages.PLAYER_1, StatusMessages.PLAYER_2]
        if playerId == StatusMessages.PLAYER_1:
            self.body.setX(PLAYER_1_SPAWN[0])
            self.body.setY(PLAYER_1_SPAWN[1])
            return
        self.body.setX(PLAYER_2_SPAWN[0])
        self.body.setY(PLAYER_2_SPAWN[1])
        self.body.setH(180)
    
    def __construct(self):
        self.body = Actor(getModelPath("body"))
        self.body.setName("body")
        self.body.reparentTo(render)
        
        bodyHitBox = CollisionCapsule(0,0,0.4,0,0,0.3,0.3)
        self.bodyHitBoxNodePath = self.body.attachNewNode(CollisionNode(f"{self.id}-bHbnp"))
        self.bodyHitBoxNodePath.node().addSolid(bodyHitBox)
        self.bodyHitBoxNodePath.setCollideMask(self.own_collision_mask)
        
        self.head = Actor(getModelPath("head"))
        self.head.reparentTo(self.body)
        self.head.setPos(0,0,0.52)
        head_joint = self.head.exposeJoint(None, "modelRoot", "Bone")
        headHitBox = CollisionSphere(0,0.2,0,0.1)
        
        self.headHitBoxNodePath = self.head.attachNewNode(CollisionNode(f"{self.id}-hHbnp"))
        self.headHitBoxNodePath.node().addSolid(headHitBox)
        self.headHitBoxNodePath.setCollideMask(self.own_collision_mask)
        self.headHitBoxNodePath.reparentTo(head_joint)

        # Blocked hitbox
        bodyBlockedHitBox = CollisionCapsule(0,0,0.4,0,0,0.3,0.3)
        self.bodyHitBoxBlockedNodePath = self.body.attachNewNode(CollisionNode(f"{self.id}-bHbnp-blocked"))
        self.bodyHitBoxBlockedNodePath.node().addSolid(bodyBlockedHitBox)
        self.bodyHitBoxBlockedNodePath.setCollideMask(NO_BIT_MASK)
        
        self.headHitBoxBlockedNodePath = self.head.attachNewNode(CollisionNode(f"{self.id}-hHbnp-blocked"))
        self.headHitBoxBlockedNodePath.node().addSolid(headHitBox)
        self.headHitBoxBlockedNodePath.setCollideMask(NO_BIT_MASK)
        self.headHitBoxBlockedNodePath.reparentTo(head_joint)
        
        self.sword = Actor(getModelPath("sword"),{"stab":getModelPath("sword-Stab"),
                                                  "block":getModelPath("sword-Block"),
                                                  "being-blocked":getModelPath("sword-being-blocked"),
                                                  "sweep":getModelPath("sword-Sweep"),
                                                  "sweep2":getModelPath("sword-Sweep2")})
        self.sword.reparentTo(self.head)
        
        sword_joint = self.sword.exposeJoint(None, "modelRoot", "Bone")
        swordHitBox = CollisionCapsule(0, 5, 0, 0, 1, 0, 0.3)
        self.swordHitBoxNodePath = self.sword.attachNewNode(CollisionNode(f"{self.id}-sHbnp"))
        self.swordHitBoxNodePath.node().addSolid(swordHitBox)
        self.swordHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        self.swordHitBoxNodePath.reparentTo(sword_joint)
        
        self.sword.setShaderOff()
               
        self.sword.setPos(0, 0.2, 0)
    
        self.shoes = Actor(getModelPath("shoes"))
        self.shoes.reparentTo(self.body)
        self.body.setPos(0, 0, 0.5)
        
    def endAttack(self,task):
        self.is_in_attack = False
    
    def endBlock(self,task):
        self.is_in_block = False
    
    def playSound(self,name):
        if name == "sweep":
            random.choice(self.sweepingSounds).play()
        elif name == "hit":
            random.choice(self.hitSounds).play()
        else:
            base.loader.loadSfx(getSoundPath(name)).play()
    
    def playSoundLater(self, name):
        self.playSound(name)
        
    def turnSwordLethal(self,task):
        self.has_lethal_sword = True
        self.swordHitBoxNodePath.node().setCollideMask(self.opposing_collision_mask)
        
    def turnSwordHarmless(self,task):
        self.has_lethal_sword = False
        self.swordHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        
    def turnSwordBlock(self,task):
        self.logger.debug("block")
        self.has_blocking_sword = True
        # Enable block body
        self.bodyHitBoxBlockedNodePath.node().setCollideMask(self.own_collision_mask)
        self.headHitBoxBlockedNodePath.node().setCollideMask(self.own_collision_mask)
        # Disable normal body
        self.bodyHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        self.headHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        
    def turnSwordSword(self,task):
        self.logger.debug("unblock")
        self.has_blocking_sword = False
        self.hitBlocked = False
        # Disable block body
        self.bodyHitBoxBlockedNodePath.node().setCollideMask(NO_BIT_MASK)
        self.headHitBoxBlockedNodePath.node().setCollideMask(NO_BIT_MASK)
        # Enable normal body
        self.bodyHitBoxNodePath.node().setCollideMask(self.own_collision_mask)
        self.headHitBoxNodePath.node().setCollideMask(self.own_collision_mask)

        #TODO: interrupt block when hit anyway -> this still applicable? @Heuserus
        
    def handle_hit(self,event):
        if not self.hit_handled and self.sword.getCurrentAnim() is not None:
            self.hit_handled = True
            animName = self.sword.getCurrentAnim()
            
            anim = self.sword.getAnimControl(animName)
            frame = anim.getFrame()
            anim.pose(frame)
            p = ParticleEffect()
            p.setShaderOff()
            p.loadConfig(getParticlePath("blood2"))
            p.setPos(event.getSurfacePoint(render))
            normal = event.getSurfaceNormal(render)
            
            p0 = p.getParticlesList()[0]  # Get the first particle system
            emitter = p0.getEmitter()
            
            emitter.setExplicitLaunchVector(normal)
            
            p.setScale(1)
            p.start(parent = render, renderParent = render)
            taskMgr.doMethodLater(2/24,self.continueStrike,"continueStrike",extraArgs=[animName,frame],appendTask=True)
            taskMgr.doMethodLater(1,self.hitOver,"hitOver",extraArgs=[p],appendTask=True)

    def continueStrike(self,animName,frame,task):
        self.sword.play(animName,fromFrame=frame)
        
    def hitOver(self,blood,task):
        self.hit_handled = False
        blood.cleanup()
        blood.removeNode()

    def take_damage(self, damage_value: int):
        self.playSound("hit")
        self.health -= damage_value
        self.logger.debug(f"Now at {self.health} HP")
        messenger.send(GUI_UPDATE_PLAYER_HP if self.id == "player" else GUI_UPDATE_ANTI_HP, [self.health])
        # Server handles online win states
        if self.online:
            return
        if self.health <= 0:
            if self.id == "player":
                messenger.send(DEFEAT_EVENT)
            else:
                if not self.is_puppet:
                    messenger.send(WIN_EVENT)

    def handle_body_damage(self, entry):
        if self.is_puppet:
            return

        # ensure that this is the sword in case any topology is changed at some point
        assert entry.getFromNodePath().getName().endswith("-sHbnp")

        if not self.__collision_into_was_from_behind(entry.getFromNodePath()):
            if self.hitBlocked:
                return
            if self.has_blocking_sword:
                self.hitBlocked = True
                self.handle_block()
                return
        
        if self.inv_phase <= 0.0:
            self.current_hit_has_critted = False
            self.take_damage(1)
            self.inv_phase = POST_HIT_INV_DURATION

    def handle_head_damage(self, entry):
         # Do not calculate damage for enemy
        if self.is_puppet:
            return

        # ensure that this is the sword in case any topology is changed at some point
        assert entry.getFromNodePath().getName().endswith("-sHbnp")

        if not self.__collision_into_was_from_behind(entry.getFromNodePath()):
            if self.hitBlocked:
                return
        
            if self.has_blocking_sword:
                self.hitBlocked = True
                self.handle_block()
                return
       
        # Direct head hit
        if self.inv_phase <= 0:
            self.current_hit_has_critted = True
            self.take_damage(1)
            self.inv_phase = POST_HIT_INV_DURATION
        # Hit that hit body first, then head
        elif not self.current_hit_has_critted and self.inv_phase >= 0:
            self.current_hit_has_critted = True
            #self.take_damage(1)
    
    def handle_block(self):
        self.logger.debug("I blocked an attack")
        self.is_in_block = False
        self.is_in_attack = False
        self.playSound("blocked_hit")
        base.taskMgr.doMethodLater(0, self.turnSwordSword,f"{self.id}-makeSwordSword")
        
    def handle_blocked_hit(self,entry):
        if not self.hit_handled:
            if self.__collision_into_was_from_behind(entry.getIntoNodePath()):
                self.logger.debug("Was from behind, no block occured")
                return
            self.end_dash(None)
            self.endAttack(None)
            taskMgr.remove(f"{self.id}-endAttackTask")
            self.play_blocked_animation()
           
    def play_blocked_animation(self):
        self.logger.debug("My attack was blocked")
        self.sword.play("being-blocked")
        self.is_block_stunned = True
        total_frames = self.sword.getAnimControl("being-blocked").getNumFrames()
        taskMgr.doMethodLater(total_frames/24, self.cleanse_block_stun, f"{self.id}-cleanseBlockStun")

    def cleanse_block_stun(self, task):
        self.is_block_stunned = False
        self.is_dashing = False
        self.is_in_attack = False
        
    def start_dash(self,task):
        self.is_dashing = True
    
    def end_dash(self,task):
        self.is_dashing = False
        self.vertical_velocity = -0.01
        taskMgr.doMethodLater(1, self.cleanUpParticles, "cleanUpSplashTask")
    
    def cleanUpParticles(self,task):
        for p in self.dashParticles:
            p.cleanup()
        self.dashParticles = []
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

    def apply_world_border_correction(self, wanted_movement_vector: Vec3) -> Vec3:
        """ Transform vector to stop at world border. Ignores z coord """
        current_pos = self.body.getPos()
        current_pos.setZ(0)
        current_delta_to_center = (current_pos - Vec3(WORLD_CENTER_POINT[0], WORLD_CENTER_POINT[1], 0))
        if current_delta_to_center.length() > (ALLOWED_WORD_CENTER_DISTANCE):
            closest_valid_position = Vec3(WORLD_CENTER_POINT[0], WORLD_CENTER_POINT[1],0) + (current_delta_to_center.normalized() * (ALLOWED_WORD_CENTER_DISTANCE * 0.95))
            self.body.setFluidPos(closest_valid_position.getX(), closest_valid_position.getY(), self.body.getZ())
            return Vec3(0,0,0)
        return wanted_movement_vector

    def __collision_into_was_from_behind(self, into_node_path: NodePath) -> bool:
        """ 2D calculation if own sword is coming from behind the stabbed/attacked entity"""
        into_body_node_path = traverse_parents_until_name_is_matched(into_node_path, "body")
        if into_body_node_path is None:
            return False
        enemy_body_orientation_hor = render.getRelativeVector(into_body_node_path, Vec3.forward())
        enemy_body_orientation_hor.setZ(0)
        own_back_hor = render.getRelativeVector(self.body, Vec3.back())
        own_back_hor.setZ(0)
        deg_delta = abs(enemy_body_orientation_hor.normalized().angleDeg(own_back_hor.normalized()))
        self.draw_debug_ray(self.body.getPos(), self.body.getPos() + own_back_hor)
        self.draw_debug_ray(self.body.getPos(), self.body.getPos() + enemy_body_orientation_hor, color=(0,1,0,1))
        return deg_delta > (BLOCK_RANGE_DEG/2)

    def draw_debug_ray(self, start, end, color=(1, 0, 0, 1)):
        """Draws a debug ray from start to end with the given color."""
        lines = LineSegs()
        lines.setColor(*color)  # Set color (RGBA)
        lines.setThickness(2.0)  # Set line thickness
        lines.moveTo(start)
        lines.drawTo(end)

        # Convert to a NodePath and attach it to the render tree
        line_node = NodePath(lines.create())
        line_node.reparentTo(render)

    def getPos(self, ref: NodePath):
        """ Stupid wrapper to avoid having to write .body in bot """
        return self.body.getPos(ref)

    def update(self, dt):
        if self.is_dashing and self.body.getZ() < 0.8 and self.body.getX() > -5.5 and self.body.getX() < 6 and self.body.getY() < 16 and self.body.getY() > -8:
            # -5,5 16
            # 6 16
            # 6 -8
            # -5,5 -8
            p = ParticleEffect()
            p.setShaderOff()
            p.loadConfig(getParticlePath("water_dash2"))

            # Ensure the renderer is set before initialization
            p0 = p.getParticlesList()[0]  # Get the first particle system
            

            p.start(parent=render, renderParent=render)
            p.setDepthWrite(False)
            p.setBin("fixed", 0)
            p.setPos(self.body.getPos())

            self.dashParticles.append(p)
            
        if self.inv_phase > 0.0:
            self.inv_phase -= dt
        else:
            self.current_hit_has_critted = False
