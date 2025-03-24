from game.const.player import BASE_HEALTH, MOVEMENT_SPEED
from game.entities.base_entity import EntityBase
from direct.actor.Actor import Actor
from game.helpers.helpers import *
from panda3d.core import Vec3, Point3, CollisionNode, CollisionSphere,Vec2
from shared.types.player_info import PlayerInfo, Vector

class Player(EntityBase):
    def __init__(self,camera,window) -> None:
        super().__init__("Player")
        self.id = "player"
        self.move_speed = 10   #MOVEMENT_SPEED
        self.mouse_sens = 0.1 #MOUSE_SENS
        self.movement_status = {"forward": 0, "backward": 0, "left": 0, "right": 0}
        self.camera = camera
        self.window = window
        self.jump_status = "none"
        self.health = BASE_HEALTH
        self.build_player()
        self.initial_jump_velocity = 100
        
        
        

        # Keybinds for movement
        self.accept("a", self.set_movement_status, ["left"])
        self.accept("a-up", self.unset_movement_status, ["left"])
        self.accept("d", self.set_movement_status, ["right"])
        self.accept("d-up", self.unset_movement_status, ["right"])
        self.accept("w", self.set_movement_status, ["forward"])
        self.accept("w-up", self.unset_movement_status, ["forward"])
        self.accept("s", self.set_movement_status, ["backward"])
        self.accept("s-up", self.unset_movement_status, ["backward"])
        self.accept("space",self.set_jump_status)
        self.accept("mouse1",self.stab)
        
        

        '''
        self.model = Actor("assets/models/MapObjects/Player/Player.bam",
                           {"Turn": "assets/models/MapObjects/Player/Player-Turn.bam",
                            "TurnBack": "assets/models/MapObjects/Player/Player-TurnBack.bam"})
        self.model.setPos(0, 0, MOVEMENT.PLAYER_FIXED_HEIGHT)
        self.model.reparentTo(render)
        '''

        #self.__add_player_collider()
        #self.holding.model.setPos(0, -0.4, 0.76)
        #self.holding.model.reparentTo(self.model)
        #self.actor.loop("stab")

    def set_movement_status(self, direction):
        self.movement_status[direction] = 1

    def unset_movement_status(self, direction):
        self.movement_status[direction] = 0

    def set_jump_status(self):
        if self.jump_status == "none":
            
            self.jump_status = "start"
            
    def stab(self):
        self.sword.play("stab")
    
    def build_player(self):
        
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

    def update_camera(self,dt):
        md = self.window.getPointer(0)
        x = md.getX() - self.window.getXSize() / 2
        y = md.getY() - self.window.getYSize() / 2
        if abs(y) <= 0.5: #Potenziell Fixable
            y = 0
        self.body.setH(self.body.getH() - x * self.mouse_sens)
        self.head.setP(self.head.getP() - y * self.mouse_sens)
        self.window.movePointer(0, self.window.getXSize() // 2, self.window.getYSize() // 2)

    def __get_movement_vector(self,dt) -> Vec3:
        
        flat_moveVec = Vec2(0,0)
        moveVec = Vec3(0, 0, 0)
        
        if self.body.getZ() <= 0.5 and self.jump_status == "start":
            self.jump_status = "fly"
            self.vertical_velocity = self.initial_jump_velocity  

        if self.jump_status == "fly" or self.jump_status == "fall":
            
            self.vertical_velocity -= 9.81*20 * dt  

            moveVec += Vec3(0, 0, self.vertical_velocity) * dt  

            if self.vertical_velocity < 0:
                self.jump_status = "fall"
        if self.body.getZ() <= 0.5 and self.jump_status == "fall":
            self.jump_status = "none"
            self.vertical_velocity = 0 
             
        if self.movement_status["forward"]:
            flat_moveVec += Vec2(0, 1)
        if self.movement_status["backward"]:
            flat_moveVec += Vec2(0, -1)
        if self.movement_status["left"]:
            flat_moveVec += Vec2(-1, 0)
        if self.movement_status["right"]:
            flat_moveVec += Vec2(1, 0)
        flat_moveVec.normalize() if flat_moveVec.length() > 0 else None
        moveVec = Vec3(flat_moveVec.x,flat_moveVec.y,moveVec.z)
        return moveVec

    
    def update(self, dt):
        self.update_camera(dt)
        moveVec = self.__get_movement_vector(dt)
        moveVec *= self.move_speed * dt
        self.body.setPos(self.body, moveVec)

    def get_current_state(self) -> PlayerInfo:
        """Current state to send via network"""
        movement_vec = self.__get_movement_vector()
        return PlayerInfo(
            health=self.health,
            position=Vector(self.body.getX(),self.body.getY(),self.body.getZ(),1),
            lookDirection=Vector(self.head.getH(),self.head.getP(),self.head.getR(),1),
            movement=Vector(movement_vec.x,movement_vec.y,movement_vec.z,movement_vec.length()),
        )
