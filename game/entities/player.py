from direct.stdpy.threading import current_thread
from game.const.events import NETWORK_SEND_PRIORITY_EVENT, SET_PLAYER_NO_EVENT, UPDATE_PLAYER_LOOK_SENSITIVITY
from game.const.player import BASE_HEALTH, DASH_SPEED, GRAVITY, JUMP_VELOCITY, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from game.helpers.config import get_look_sensitivity
from game.helpers.helpers import *
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere,Vec2,CollisionCapsule,ColorAttrib,CollisionHandlerEvent,CollisionHandlerQueue
from shared.types.player_info import PlayerAction, PlayerInfo, Vector
import random


class Player(EntityBase):
    def __init__(self, camera, window, online) -> None:
        super().__init__(window, "player", online, "Player")
        self.mouse_sens = get_look_sensitivity()
        self.movement_status = {"forward": 0, "backward": 0, "left": 0, "right": 0}
        self.camera = camera
                
        self.accept("a", self.set_movement_status, ["left"])
        self.accept("a-up", self.unset_movement_status, ["left"])
        self.accept("d", self.set_movement_status, ["right"])
        self.accept("d-up", self.unset_movement_status, ["right"])
        self.accept("w", self.set_movement_status, ["forward"])
        self.accept("w-up", self.unset_movement_status, ["forward"])
        self.accept("s", self.set_movement_status, ["backward"])
        self.accept("s-up", self.unset_movement_status, ["backward"])
        self.accept("space", self.jump)
        self.accept("lshift", self.stab)
        self.accept("mouse1",self.sweep)
        self.accept("mouse3", self.block)

        self.accept(UPDATE_PLAYER_LOOK_SENSITIVITY, self.__update_player_sens)

    def __update_player_sens(self):
        self.mouse_sens = get_look_sensitivity()

    def set_movement_status(self, direction):
        self.movement_status[direction] = 1

    def unset_movement_status(self, direction):
        self.movement_status[direction] = 0

    def jump(self):
        if self.is_block_stunned:
            return

        if self.vertical_velocity == 0:
            self.vertical_velocity = JUMP_VELOCITY
            messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(actions=[PlayerAction.JUMP], action_offsets=[self.match_timer], health=self.health)])
            
    def stab(self):
        if self.is_block_stunned:
            return

        if not self.is_in_attack and not self.is_in_block:
            self.is_in_attack = True
            self.is_in_block = False
            self.sword.play("stab")
            self.schedule_stab_tasks()
            messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(actions=[PlayerAction.ATTACK_1], action_offsets=[self.match_timer], health=self.health)])
    
    def sweep(self):
        if self.is_block_stunned :
            return

        if not self.is_in_attack and not self.is_in_block:
            self.is_in_attack = True
            if self.sweepCount == 4:
                self.sweepCount = 1
            self.sword.play(f"sweep{self.sweepCount}")
            self.schedule_sweep_tasks()
            messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(actions=[PlayerAction(3 + self.sweepCount)], action_offsets=[self.match_timer], health=self.health)])
            self.sweepCount += 1
            
    def block(self):
        if self.is_block_stunned:
            return

        if not self.is_in_block:
            
            self.is_in_block = True
            self.start_block_animation()
            self.end_attack(None)
            self.schedule_block_tasks()
            messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(actions=[PlayerAction.BLOCK], action_offsets=[self.match_timer], health=self.health)])

    def update_state(self, player_info: PlayerInfo):
        if PlayerAction.DEAL_DAMAGE in player_info.actions:
            self.show_sword_hit(self.body.getPos(render), render.getRelativeVector(self.body, Vec3.forward() + Vec3.up()))
            if player_info.enemy_health != self.health:
                self.logger.warning(f"Health desync. Updating with network value local: {self.health} remote: {player_info.enemy_health}")
                self.take_damage(self.health - player_info.enemy_health, force=True)
    
    def update_camera(self, dt):
        # Check if mouse is enabled
        # https://docs.panda3d.org/1.10/python/_modules/direct/showbase/ShowBase#ShowBase.disableMouse
        if base.mouse2cam.has_parent():
            return
        md = self.window.getPointer(0)
        x = md.getX() - self.window.getXSize() / 2
        y = md.getY() - self.window.getYSize() / 2
        if abs(y) <= 0.5: #Potenziell Fixable
            y = 0
        self.body.setH(self.body.getH() - x * self.mouse_sens)
        self.head.setP(min(max(self.head.getP() - y * self.mouse_sens, -90 + 5), 90 - 5))
        self.window.movePointer(0, self.window.getXSize() // 2, self.window.getYSize() // 2)
    
    def __get_movement_vector(self) -> Vec3:
        flat_moveVec = Vec2(0,0)
        if self.movement_status["forward"]:
            flat_moveVec += Vec2(0, 1)
        if self.movement_status["backward"]:
            flat_moveVec += Vec2(0, -1)
        if self.movement_status["left"]:
            flat_moveVec += Vec2(-1, 0)
        if self.movement_status["right"]:
            flat_moveVec += Vec2(1, 0)
        flat_moveVec.normalize() if flat_moveVec.length() > 0 else None
        flat_moveVec *= self.move_speed
        move_vec = Vec3(flat_moveVec.x, flat_moveVec.y, self.vertical_velocity)
        if self.is_dashing:
            direction = self.body.getRelativeVector(self.head, Vec3.forward())
            self.vertical_velocity = direction.z * DASH_SPEED
            direction.z = 0
            move_vec += direction * DASH_SPEED
        return move_vec

    def update(self, dt):
        # player has been destroyed
        if self.body.isEmpty():
            return
        super().update(dt)
        self.match_timer += dt
        self.update_camera(dt)
        self.apply_gravity(dt)
        moveVec = self.__get_movement_vector()
        stepped_move_vec = Vec3(moveVec.x, moveVec.y, 0)
        stepped_move_vec *= dt
        stepped_move_vec = self.apply_world_border_correction(stepped_move_vec)
        self.body.setPos(self.body, Vec3(stepped_move_vec.x, stepped_move_vec.y, moveVec.z  * dt))

    def get_current_state(self) -> PlayerInfo:
        """Current state to send via network"""
        movement_vec = self.__get_movement_vector()
        return PlayerInfo(
            health=self.health,
            position=Vector(self.body.getX(),self.body.getY(),self.body.getZ(),1),
            lookRotation=self.head.getP(),
            bodyRotation=self.body.getH(),
            movement=Vector(movement_vec.x, movement_vec.y, movement_vec.z, movement_vec.length()),
        )
