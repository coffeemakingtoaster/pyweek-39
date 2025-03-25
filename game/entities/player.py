from game.const.events import NETWORK_SEND_PRIORITY_EVENT
from game.const.player import BASE_HEALTH, GRAVITY, JUMP_VELOCITY, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from direct.actor.Actor import Actor
from game.helpers.helpers import *
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere,Vec2,CollisionCapsule,ColorAttrib,CollisionHandlerEvent,CollisionHandlerQueue
from shared.types.player_info import PlayerInfo, Vector

class Player(EntityBase):
    def __init__(self,camera,window) -> None:
        super().__init__(window, "player", "Player")
        self.mouse_sens = 0.1 #MOUSE_SENS
        self.movement_status = {"forward": 0, "backward": 0, "left": 0, "right": 0}
        self.camera = camera
        
        #self.accept("sHbnp-collision-out", self.handleSwordCollisionEnd)

        # Keybinds for movement
        self.accept("a", self.set_movement_status, ["left"])
        self.accept("a-up", self.unset_movement_status, ["left"])
        self.accept("d", self.set_movement_status, ["right"])
        self.accept("d-up", self.unset_movement_status, ["right"])
        self.accept("w", self.set_movement_status, ["forward"])
        self.accept("w-up", self.unset_movement_status, ["forward"])
        self.accept("s", self.set_movement_status, ["backward"])
        self.accept("s-up", self.unset_movement_status, ["backward"])
        self.accept("space",self.jump)
        self.accept("mouse1",self.stab)

    def set_movement_status(self, direction):
        self.movement_status[direction] = 1

    def unset_movement_status(self, direction):
        self.movement_status[direction] = 0

    def jump(self):
        if self.vertical_velocity == 0:
            self.vertical_velocity = JUMP_VELOCITY
            messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(is_jumping=True, action_offset=self.match_timer)])
            
    def stab(self):
        if not self.inAttack:
            self.inAttack = True
            self.sword.play("stab")
            frames = self.sword.getAnimControl("stab").getNumFrames()
            base.taskMgr.doMethodLater(25/24,self.turnSwordLethal,"makeSwordLethalTask")
            base.taskMgr.doMethodLater(32/24,self.turnSwordHarmless,"makeSwordLethalTask")
            base.taskMgr.doMethodLater(frames/24,self.endAttack,"endAttackTask")
            messenger.send(NETWORK_SEND_PRIORITY_EVENT, [PlayerInfo(is_attacking=True, action_offset=self.match_timer)])
      
    def update_camera(self, dt):
        md = self.window.getPointer(0)
        x = md.getX() - self.window.getXSize() / 2
        y = md.getY() - self.window.getYSize() / 2
        if abs(y) <= 0.5: #Potenziell Fixable
            y = 0
        self.body.setH(self.body.getH() - x * self.mouse_sens)
        self.head.setP(self.head.getP() - y * self.mouse_sens)
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
        return Vec3(flat_moveVec.x, flat_moveVec.y, self.vertical_velocity)
    
    def update(self, dt):
        super().update(dt)
        self.match_timer += dt
        self.update_camera(dt)
        self.apply_gravity(dt)
        moveVec = self.__get_movement_vector()
        stepped_move_vec = Vec3(moveVec.x, moveVec.y, 0)
        stepped_move_vec *= dt
        self.body.setPos(self.body, Vec3(stepped_move_vec.x, stepped_move_vec.y, moveVec.z  * dt))

    def get_current_state(self) -> PlayerInfo:
        """Current state to send via network"""
        movement_vec = self.__get_movement_vector()
        return PlayerInfo(
            health=self.health,
            position=Vector(self.body.getX(),self.body.getY(),self.body.getZ(),1),
            lookDirection=Vector(self.head.getH(),self.head.getP(),self.head.getR(),1),
            bodyRotation=Vector(self.body.getH(),self.body.getP(),self.body.getR(),1),
            movement=Vector(movement_vec.x, movement_vec.y, movement_vec.z, movement_vec.length()),
        )
