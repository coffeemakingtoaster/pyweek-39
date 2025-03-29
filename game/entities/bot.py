import random
from game.const.player import BOT_WAIT_TIME_BETWEEN_ACTION_CHECKS, DASH_SPEED, JUMP_VELOCITY, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from game.entities.player import Player
from game.helpers.helpers import *
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere,Vec2,CollisionCapsule,ColorAttrib,CollisionHandlerEvent,CollisionHandlerQueue
from shared.types.player_info import PlayerAction, PlayerInfo, Vector
from math import atan2, degrees, sqrt
from panda3d.core import Vec3

class Bot(EntityBase):
    def __init__(self,window) -> None:
        super().__init__(window, "enemy", False, "Player")

        self.action_check_cooldown = 1

    def jump(self):
        if self.is_block_stunned:
            return

        if self.vertical_velocity == 0:
            self.vertical_velocity = JUMP_VELOCITY
            
    def stab(self,player):
        if self.is_block_stunned:
            return

        if not self.is_in_attack:
            self.is_in_attack = True
            self.is_in_block = False
            base.taskMgr.doMethodLater(5/24,self.playSoundLater,f"{self.id}-playSoundStab", extraArgs=["stab"])
            self.sword.play("stab")
            frames = self.sword.getAnimControl("stab").getNumFrames()
            base.taskMgr.doMethodLater(25/24,self.turnSwordLethal,f"{self.id}-makeSwordLethalTask")
            base.taskMgr.doMethodLater(32/24,self.turnSwordHarmless,f"{self.id}-makeSwordHarmlessTask")
            base.taskMgr.doMethodLater(25/24,self.start_dash,f"{self.id}-startDashingTask",extraArgs=[player],appendTask = True)
            base.taskMgr.doMethodLater(32/24,self.end_dash,f"{self.id}-endDashingTask")
            base.taskMgr.doMethodLater(frames/24,self.endAttack,f"{self.id}-endAttackTask")
    
    def start_dash(self,player,task):
        if self.body.is_empty():
            return
        self.is_dashing = True
        # Get positions
        player_position = player.getPos(render)
        body_position = self.body.getPos(render)

        # Calculate direction vector
        direction_x = player_position.x - body_position.x
        direction_y = player_position.y - body_position.y

        # Calculate angle in degrees
        angle = degrees(atan2(direction_y, direction_x))-80

        # Set the heading (H) to face the player
        self.body.setH(angle)
        
     
    def sweep(self):
        if self.is_block_stunned :
            return

        if not self.is_in_attack and not self.is_in_block:
            
            self.is_in_attack = True
            base.taskMgr.doMethodLater(14/24, self.playSoundLater, f"{self.id}-playSoundSweep", extraArgs=["sweep"])
            if self.sweepCount == 3:
                self.sword.play("sweep"+str(self.sweepCount))
                self.sweepCount = 0
            else:
                self.sword.play("sweep"+str(self.sweepCount))
                self.sweepCount += 1
            frames = self.sword.getAnimControl("sweep1").getNumFrames()
            base.taskMgr.doMethodLater(20/24,self.turnSwordLethal,f"{self.id}-makeSwordLethalTask")
            base.taskMgr.doMethodLater(28/24,self.turnSwordHarmless,f"{self.id}-makeSwordHarmlessTask")
            base.taskMgr.doMethodLater((35)/24, self.endAttack,f"{self.id}-endAttackTask")
    
    def block(self):
        if self.is_block_stunned:
            return

        if not self.is_in_block:
            self.is_in_attack = True
            self.is_in_block = True
            self.sword.play("block1")
            
            taskMgr.remove(f"{self.id}-endAttackTask")
            taskMgr.remove(f"{self.id}-makeSwordLethalTask")
            taskMgr.remove(f"{self.id}-makeSwordHarmlessTask")
            taskMgr.remove(f"{self.id}-startDashingTask")
            
            frames = self.sword.getAnimControl("block1").getNumFrames()
            base.taskMgr.doMethodLater(1/24, self.turnSwordBlock,f"{self.id}-makeSwordBlockTask")
            base.taskMgr.doMethodLater(15/24, self.turnSwordSword,f"{self.id}-makeSwordSword")
            base.taskMgr.doMethodLater(frames/24, self.endBlock,f"{self.id}-endBlockTask")
            base.taskMgr.doMethodLater(frames/24, self.endAttack,f"{self.id}-endAttackTask")
    
    def jump(self):
        if self.is_block_stunned:
            return

        if self.vertical_velocity == 0:
            self.vertical_velocity = JUMP_VELOCITY
            
    
    def update_viewing_direction(self, dt, player_position: Vec3):
        # Dont turn during dash to make it a bit more fair
        if self.is_dashing:
            return
       
       
        body_position = self.body.getPos(render)

        # Calculate direction vector
        direction_x = player_position.x - body_position.x
        direction_y = player_position.y - body_position.y
        direction_z = player_position.z - body_position.z

        # Calculate heading (H) - rotate horizontally
        angle_h = degrees(atan2(direction_y, direction_x)) - 90

        # Calculate pitch (P) - tilt up/down
        distance_xy = sqrt(direction_x**2 + direction_y**2)  # Horizontal distance
        angle_p = degrees(atan2(direction_z, distance_xy))  # Negative because Panda3D pitch increases downward

        # Apply rotation
        self.body.setH(angle_h)
        if not self.is_in_attack:
            self.head.setP(angle_p)

    def attack_if_possible(self, player: Player):
        # We wait a bit longer until we try again
        if self.action_check_cooldown > 0:
            return
        # Sword is occupied with something else
        if self.is_in_block or self.is_in_attack:
            return
        dist_to_player = (self.body.getPos(render) - player.getPos(render)).length()
        # Player is too far away?
        if dist_to_player > 7:
            return
        self.action_check_cooldown = BOT_WAIT_TIME_BETWEEN_ACTION_CHECKS
        if player.is_in_attack:
            # 1 in 100 chance to block -> this is per tick :)
            self.block() if random.randint(1,100) else None
        if 7 > dist_to_player > 3:
            # 1 in 100 chance to block -> this is per tick :)
            
            self.stab(player) if random.randint(1,100) else None
            
        else:
            #self.stab(player) if random.randint(1,500) else None
            #self.jump() if random.randint(1,200) else None
            # 1 in 100 chance to block -> this is per tick :)
            self.sweep() if random.randint(1,100) else None
            
            
            

    def get_desired_movement_direction(self, player_position: Vec3) -> Vec3:
        if self.is_dashing:
            direction = self.body.getRelativeVector(self.head, Vec3.forward())
            self.vertical_velocity = direction.z * DASH_SPEED
            direction.z = 0
            return direction.normalized() * DASH_SPEED
        delta = (self.body.getPos(render) - player_position).length()
        if delta < 1:
            return self.body.getRelativeVector(self.head, Vec3.forward()).normalized() * MOVEMENT_SPEED * -1 
        if delta < 3:
            return Vec3(0,0,self.vertical_velocity)
        return self.body.getRelativeVector(self.head, Vec3.forward()) * MOVEMENT_SPEED
            
    def update(self, dt, player=None):
        
        self.action_check_cooldown -= dt
        if player is None:
            self.logger.error("Bot did not receive valid player")
            return
        # bot has been destroyed
        if self.body.isEmpty():
            return
        super().update(dt)
        self.match_timer += dt
        self.update_viewing_direction(dt, player.getPos(render))
        self.apply_gravity(dt)
        self.attack_if_possible(player)
        moveVec = self.get_desired_movement_direction(player.getPos(render))
        moveVec *= dt
        moveVec = self.apply_world_border_correction(moveVec)
        self.body.setFluidPos(self.body, Vec3(moveVec.x, moveVec.y, moveVec.z  * dt))
