import random
from game.const.player import BOT_WAIT_TIME_BETWEEN_ACTION_CHECKS, DASH_SPEED, JUMP_VELOCITY, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from game.entities.player import Player
from game.helpers.helpers import *
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
            
    def stab(self):
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
            base.taskMgr.doMethodLater(25/24,self.start_dash,f"{self.id}-startDashingTask")
            base.taskMgr.doMethodLater(32/24,self.end_dash,f"{self.id}-endDashingTask")
            base.taskMgr.doMethodLater(frames/24,self.endAttack,f"{self.id}-endAttackTask")
    
    def sweep(self):
        if self.is_block_stunned:
            return

        if not self.is_in_attack:
            self.is_in_attack = True
            self.is_in_block = False
            base.taskMgr.doMethodLater(14/24, self.playSoundLater, f"{self.id}-playSoundSweep", extraArgs=["sweep"])
            if self.sweep2:
                self.sword.play("sweep2")
                self.sweep2 = False
            else:
                self.sword.play("sweep")
                self.sweep2 = True
            frames = self.sword.getAnimControl("sweep").getNumFrames()
            base.taskMgr.doMethodLater(10/24,self.turnSwordLethal,f"{self.id}-makeSwordLethalTask")
            base.taskMgr.doMethodLater(30/24,self.turnSwordHarmless,f"{self.id}-makeSwordHarmlessTask")
            base.taskMgr.doMethodLater(frames/24,self.endAttack,f"{self.id}-endAttackTask")
    
    def block(self):
        if self.is_block_stunned:
            return

        if not self.is_in_block:
            self.is_in_attack = True
            self.is_in_block = True
            self.sword.play("block")
            
            taskMgr.remove(f"{self.id}-endAttackTask")
            taskMgr.remove(f"{self.id}-makeSwordLethalTask")
            taskMgr.remove(f"{self.id}-makeSwordHarmlessTask")
            taskMgr.remove(f"{self.id}-startDashingTask")
            
            frames = self.sword.getAnimControl("block").getNumFrames()
            base.taskMgr.doMethodLater(1/24, self.turnSwordBlock,f"{self.id}-makeSwordBlockTask")
            base.taskMgr.doMethodLater(15/24, self.turnSwordSword,f"{self.id}-makeSwordSword")
            base.taskMgr.doMethodLater(frames/24, self.endBlock,f"{self.id}-endBlockTask")
            base.taskMgr.doMethodLater(frames/24, self.endAttack,f"{self.id}-endAttackTask")
    
    def update_viewing_direction(self, dt, player_position: Vec3):
        # Dont turn during dash to make it a bit more fair
        if self.is_dashing:
            return
        # Only turn to player if player gets closer
        self.body.lookAt(Vec3(player_position.x, player_position.y,0.5))
        self.head.lookAt(player_position)

    def attack_if_possible(self, player: Player):
        # We wait a bit longer until we try again
        if self.action_check_cooldown > 0:
            return
        # Sword is occupied with something else
        if self.is_in_block or self.is_in_attack:
            return
        dist_to_player = (self.body.getPos(render) - player.getPos(render)).length()
        # Player is too far away?
        if dist_to_player > 5:
            return
        self.action_check_cooldown = BOT_WAIT_TIME_BETWEEN_ACTION_CHECKS
        if player.is_in_attack:
            # 1 in 100 chance to block -> this is per tick :)
            self.block() if random.randint(1,100) else None
        if 5 > dist_to_player > 3:
            # 1 in 100 chance to block -> this is per tick :)
            self.stab() if random.randint(1,100) else None
        else:
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
        return self.body.getRelativeVector(self.head, Vec3.forward()).normalized() * MOVEMENT_SPEED
            
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
        #moveVec = self.apply_world_border_correction(moveVec)
        self.body.setFluidPos(self.body, Vec3(moveVec.x, moveVec.y, moveVec.z  * dt))
