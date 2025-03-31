import logging
from direct.actor.Actor import Actor
from direct.showbase import DirectObject

from direct.task.Task import messenger

from game.const.bit_masks import ANTI_PLAYER_BIT_MASK, NO_BIT_MASK, PLAYER_BIT_MASK
from game.const.events import DEFEAT_EVENT, GUI_UPDATE_ANTI_HP, GUI_UPDATE_PLAYER_HP, NETWORK_SEND_PRIORITY_EVENT, SET_PLAYER_NO_EVENT, START_MATCH_TIMER_EVENT, WIN_EVENT
from game.const.player import ALLOWED_WORD_CENTER_DISTANCE, BASE_HEALTH, BLOCK_RANGE_DEG, GRAVITY, MOVEMENT_SPEED, PLAYER_1_SPAWN, PLAYER_2_SPAWN, POST_HIT_INV_DURATION, WORLD_CENTER_POINT
from game.helpers.helpers import getModelPath
from panda3d.core import Vec3, CollisionNode, CollisionSphere, CollisionCapsule, CollisionHandlerEvent, NodePath

from game.utils.scene_graph import traverse_parents_until_name_is_matched
from direct.particles.ParticleEffect import ParticleEffect
from game.helpers.helpers import *
import random

from game.utils.sound import add_3d_sound_to_node
from shared.types.player_info import PlayerAction, PlayerInfo
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
        self.sweepCount = 1
        self.is_dashing = False
        self.hit_handled = False
        self.is_block_stunned = False
        self.dashParticles = []

        self.block_animations = ["block1", "block2"]
        
        self.setup_sounds()

        self.vertical_velocity = 0
        self.match_timer = 0.0

        self.__construct()

        self.collisionHandler = CollisionHandlerEvent()
        self.collisionHandler.addInPattern("%fn-collision-into-%in")

        base.cTrav.addCollider(self.swordHitBoxNodePath, self.collisionHandler)
        
        # Receive damage event -> being hit
        head_damage_event = f"{'enemy' if self.id == 'player' else 'player'}-sHbnp-collision-into-{self.id}-hHbnp"
        body_damage_event = f"{'enemy' if self.id == 'player' else 'player'}-sHbnp-collision-into-{self.id}-bHbnp"
        self.accept(head_damage_event, self.handle_being_hit) 
        self.accept(body_damage_event, self.handle_being_hit)
        self.accept(f"{head_damage_event}-blocked", self.handle_being_hit) 
        self.accept(f"{body_damage_event}-blocked", self.handle_being_hit)

        # Deal damage event -> hitting someone and being blocked
        blocked_head_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-hHbnp-blocked"
        blocked_body_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-bHbnp-blocked"
        self.accept(blocked_head_hit_event, self.handle_attack_being_blocked)
        self.accept(blocked_body_hit_event, self.handle_attack_being_blocked)
        
        # Deal damage event -> hitting someone and being blocked
        head_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-hHbnp"
        body_hit_event = f"{self.id}-sHbnp-collision-into-{'enemy' if self.id == 'player' else 'player'}-bHbnp"
        self.accept(head_hit_event, self.handle_hitting_enemy)
        self.accept(body_hit_event, self.handle_hitting_enemy)

        self.hitBlocked = False
        self.inv_phase = 0.0
        
        self.particle_owner = render.attachNewNode("particle_owner")
        self.particle_owner.setShaderOff()

        self.accept(SET_PLAYER_NO_EVENT, self.set_player)
        self.accept(START_MATCH_TIMER_EVENT, self.start_match_timer)

    def setup_sounds(self):
        self.sweeping_sounds = [base.loader.loadSfx(getSoundPath("swipe"+str(i+1))) for i in range(7)]
        self.hit_sounds = [base.loader.loadSfx(getSoundPath("hit"+str(i+1))) for i in range(4)]

    def set_player(self, playerId: StatusMessages):
        assert playerId in [StatusMessages.PLAYER_1, StatusMessages.PLAYER_2]
        spawn = PLAYER_1_SPAWN if playerId == StatusMessages.PLAYER_1 else PLAYER_2_SPAWN
        if self.id != "player":
            spawn = PLAYER_2_SPAWN if playerId == StatusMessages.PLAYER_1 else PLAYER_1_SPAWN
        self.body.setX(spawn[0])
        self.body.setY(spawn[1])
        if spawn == PLAYER_2_SPAWN:
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
                                                  "block1":getModelPath("sword-Block"),
                                                  "block2":getModelPath("sword-Block2"),
                                                  "being-blocked":getModelPath("sword-being-blocked"),
                                                  "sweep1":getModelPath("sword-Sweep"),
                                                  "sweep2":getModelPath("sword-Sweep2"),
                                                  "sweep3":getModelPath("sword-Sweep3")})
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
        
    def end_attack(self,task):
        self.is_in_attack = False
    
    def end_block(self,task):
        self.is_in_block = False
    
    def play_sound(self,name, is_3d=False):
        if name == "sweep":
            sound = random.choice(self.sweeping_sounds)
        elif name == "hit":
            sound = random.choice(self.hit_sounds)
        else:
            sound = base.loader.loadSfx(getSoundPath(name))
        if not is_3d:
            sound.play()
            return 
        add_3d_sound_to_node(sound.getName(), self.body, loops=False)
        
    def turn_sword_lethal(self,task):
        self.has_lethal_sword = True
        self.swordHitBoxNodePath.node().setCollideMask(self.opposing_collision_mask)
        
    def turn_sword_harmless(self,task):
        self.has_lethal_sword = False
        self.swordHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        
    def turn_sword_block(self,task):
        self.has_blocking_sword = True
        # Enable block body
        self.bodyHitBoxBlockedNodePath.node().setCollideMask(self.own_collision_mask)
        self.headHitBoxBlockedNodePath.node().setCollideMask(self.own_collision_mask)
        # Disable normal body
        self.bodyHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        self.headHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
        
    def turn_sword_sword(self,task):
        self.has_blocking_sword = False
        self.hitBlocked = False
        # Disable block body
        self.bodyHitBoxBlockedNodePath.node().setCollideMask(NO_BIT_MASK)
        self.headHitBoxBlockedNodePath.node().setCollideMask(NO_BIT_MASK)
        # Enable normal body
        self.bodyHitBoxNodePath.node().setCollideMask(self.own_collision_mask)
        self.headHitBoxNodePath.node().setCollideMask(self.own_collision_mask)

    def show_sword_hit(self, start, direction):
        self.play_sound("hit")
        p = ParticleEffect()
        p.setShaderOff()
        p.loadConfig(getParticlePath("blood2"))
        p.setPos(start)
        
        p0 = p.getParticlesList()[0]  # Get the first particle system
        emitter = p0.getEmitter()
        
        emitter.setExplicitLaunchVector(direction)
        
        p.setScale(1)
        p.start(parent = self.particle_owner, renderParent = self.particle_owner)

        taskMgr.doMethodLater(1, self.hit_over,"hitOver", extraArgs=[p], appendTask=True)

    def handle_hitting_enemy(self, event):
        if not self.hit_handled and self.sword.getCurrentAnim() is not None:
            if self.is_puppet:
                self.swordHitBoxNodePath.node().setCollideMask(NO_BIT_MASK)
                return

            self.hit_handled = True
            animName = self.sword.getCurrentAnim()
            
            anim = self.sword.getAnimControl(animName)
            frame = anim.getFrame()
            anim.pose(frame)

            self.show_sword_hit(event.getSurfacePoint(render), event.getSurfaceNormal(render))
            
            taskMgr.doMethodLater(2/24,self.continue_strike,"continueStrike",extraArgs=[animName,frame],appendTask=True)
              
    def continue_strike(self,animName,frame,task):
        self.sword.play(animName,fromFrame=frame)
        
    def hit_over(self,blood,task):
        self.hit_handled = False
        if blood is not None:
            blood.cleanup()
            blood.removeNode()

    def take_damage(self, damage_value: int, force = False):
        self.health -= damage_value
        messenger.send(GUI_UPDATE_PLAYER_HP if self.id == "player" else GUI_UPDATE_ANTI_HP, [self.health])
        # Server handles online win states
        if self.online:
            if self.is_puppet:
                messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(actions=[PlayerAction.DEAL_DAMAGE], action_offsets=[self.match_timer])])

        if self.health <= 0:
            if self.id == "player":
                messenger.send(DEFEAT_EVENT)
            else:
                if not self.is_puppet:
                    messenger.send(WIN_EVENT)

    def handle_being_hit(self, entry):
        assert entry.getFromNodePath().getName().endswith("-sHbnp")

        if not self.__collision_into_was_from_behind(entry.getFromNodePath()):
            if self.hitBlocked:
                return
            if self.has_blocking_sword:
                self.hitBlocked = True
                self.handle_blocking_an_attack()
                return

        if self.inv_phase <= 0.0:
            self.take_damage(1)
            self.inv_phase = POST_HIT_INV_DURATION

    def handle_blocking_an_attack(self):
        #self.logger.debug("I blocked an attack")
        self.inv_phase = 0.1
        self.is_in_block = False
        self.is_in_attack = False
        base.taskMgr.doMethodLater(0, self.turn_sword_sword,f"{self.id}-makeSwordSword")
                
    def handle_attack_being_blocked(self, entry, force=False, frame_offset=0):
        if (self.is_puppet or self.hit_handled) and not force:
            return

        self.hit_handled = True
        # force is over network...no need to verify that
        if not force:
            if self.__collision_into_was_from_behind(entry.getIntoNodePath()):
                    return
        self.turn_sword_sword(None)
        self.end_dash(None)
        self.end_attack(None)
        taskMgr.remove(f"{self.id}-endBlockTask")
        self.end_block(None) 
        self.play_blocked_animation(frame_offset)
        taskMgr.doMethodLater(0.5, self.hit_over,"hitOver", extraArgs=[None], appendTask=True)

        if self.id == "player" and self.online:
            messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(actions=[PlayerAction.GOT_BLOCKED], action_offsets=[self.match_timer])])
           
    def play_blocked_animation(self, frame_offset=0):
        #self.logger.debug(f"My attack was blocked {frame_offset}")
        self.play_sound("blocked_hit")
        self.sword.play("being-blocked", fromFrame=frame_offset)
        self.is_block_stunned = True
        total_frames = self.sword.getAnimControl("being-blocked").getNumFrames()
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.cleanse_block_stun,  name=f"{self.id}-cleanseBlockStun")

    def cleanse_block_stun(self, task):
        self.is_block_stunned = False
        self.is_dashing = False
        self.is_in_attack = False
        
    def start_dash(self,task):
        self.is_dashing = True
    
    def end_dash(self,task):
        self.is_dashing = False
        self.vertical_velocity = -0.01
        taskMgr.doMethodLater(1, self.cleanup_particles, "cleanUpSplashTask")

    def schedule_stab_tasks(self, frame_offset=0):
        total_frames = self.sword.getAnimControl("stab").getNumFrames()
        if frame_offset > total_frames:
            self.logger.warning(f"Skipped attack animation because latency exceeded frame count {frame_offset}")
            return
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=5, fn=self.play_sound, name=f"{self.id}-playSoundStab", extraArgs=["stab", True])
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=25, fn=self.turn_sword_lethal, name=f"{self.id}-makeSwordLethalTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=25, fn=self.start_dash, name=f"{self.id}-startDashingTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=32, fn=self.turn_sword_harmless, name=f"{self.id}-makeSwordHarmlessTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=32, fn=self.end_dash, name=f"{self.id}-endDashingTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.end_attack, name=f"{self.id}-endAttackTask")

    def schedule_block_tasks(self, frame_offset=0):
        taskMgr.remove(f"{self.id}-endAttackTask")
        taskMgr.remove(f"{self.id}-makeSwordLethalTask")
        taskMgr.remove(f"{self.id}-makeSwordHarmlessTask")
        taskMgr.remove(f"{self.id}-startDashingTask")

        total_frames = self.sword.getAnimControl("block1").getNumFrames()
        if frame_offset > total_frames:
            self.logger.warning(f"Skipped attack animation because latency exceeded frame count {frame_offset}")
            return
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=5, fn=self.turn_sword_block, name=f"{self.id}-makeSwordBlockTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=15, fn=self.turn_sword_sword, name=f"{self.id}-makeSwordSwordTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=15, fn=self.turn_sword_sword, name=f"{self.id}-makeSwordSwordTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.end_block, name=f"{self.id}-endBlockTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.end_attack, name=f"{self.id}-endAttackTask")

    def schedule_sweep_tasks(self, frame_offset=0):
        total_frames = self.sword.getAnimControl("sweep1").getNumFrames()
        if frame_offset > total_frames:
            self.logger.warning(f"Skipped attack animation because latency exceeded frame count {frame_offset}")
            return
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=14, fn=self.play_sound, name=f"{self.id}-playSoundSweep", extraArgs=["sweep", True])
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=14, fn=self.turn_sword_lethal, name=f"{self.id}-makeSwordLethalTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=28, fn=self.turn_sword_harmless, name=f"{self.id}-makeSwordHarmlessTask")
        self.schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.end_attack, name=f"{self.id}-endAttackTask")

    def start_sweep_animation(self, frame_offset=0):
        current_block = self.block_animations.pop(0)
        self.sword.play(current_block, fromFrame=frame_offset)
        self.block_animations.append(current_block)

    def start_block_animation(self, frame_offset=0):
        current_block = self.block_animations.pop(0)
        self.sword.play(current_block, fromFrame=frame_offset)
        self.block_animations.append(current_block)
    
    def cleanup_particles(self,task):
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
        return deg_delta > (BLOCK_RANGE_DEG/2)

    def getPos(self, ref: NodePath):
        """ Stupid wrapper to avoid having to write .body """
        if self.body.is_empty():
            return Vec3(0,0,0)
        return self.body.getPos(ref)

    def schedule_or_run(self, offset_frame: int, wanted_frame: int, fn, name: str, extraArgs=[None]):
        # Already happended -> do now
        if offset_frame >= wanted_frame:
            # Pass none as tasks expect 
            fn(*extraArgs)
            return
        if len(extraArgs) > 0:
            base.taskMgr.doMethodLater((wanted_frame - offset_frame)/24, fn, name,extraArgs=extraArgs)
            return
        base.taskMgr.doMethodLater((wanted_frame - offset_frame)/24, fn, name)

    def update(self, dt):
        if self.is_dashing and self.body.getZ() < 0.8 and self.body.getX() > -5.5 and self.body.getX() < 6 and self.body.getY() < 16 and self.body.getY() > -8:
            p = ParticleEffect()
            p.setShaderOff()
            p.loadConfig(getParticlePath("water_dash2"))

            # Ensure the renderer is set before initialization
            p0 = p.getParticlesList()[0]  # Get the first particle system
            p.start(parent=self.particle_owner, renderParent=self.particle_owner)
            p.setDepthWrite(False)
            p.setBin("fixed", 0)
            p.setPos(self.body.getPos()) 

            self.dashParticles.append(p)
            
        if self.inv_phase > 0.0:
            self.inv_phase -= dt
        else:
            self.current_hit_has_critted = False
