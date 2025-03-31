from typing import List
from game.const.events import GUI_UPDATE_ANTI_PLAYER_NAME, GUI_UPDATE_LATENCY
from game.const.networking import POSITION_DIFF_THRESHOLD
from game.const.player import DASH_SPEED, GRAVITY, JUMP_VELOCITY
from game.entities.base_entity import EntityBase
from game.helpers.helpers import *
from panda3d.core import Vec3, Vec2, TextNode
from shared.types.player_info import PlayerAction, PlayerInfo
from game.utils.name_generator import generate_name

class AntiPlayer(EntityBase):
    def __init__(self, window) -> None:
        self.name = generate_name()
        super().__init__(window, "enemy", True, "Enemy (online)")

        self.name_tag = None
        self.name_tag_node = None

        self.is_puppet = True

        self.movement_vector = Vec3(0,0,0)
        self.correction_vector = Vec3(0,0,0)

        self.__add_name_tag()

        self.accept(GUI_UPDATE_ANTI_PLAYER_NAME, self.__update_name)
        self.logger.info("Created representation for network opponent")
 
    def __add_name_tag(self):
        self.name_tag = TextNode(f"{self.id}-name")
        self.name_tag.setAlign(TextNode.ACenter) 
        self.name_tag.set_card_color(1,1,1,0.5)
        self.name_tag.set_text_color(1,1,1,1)
        self.name_tag.setCardDecal(True)
        self.name_tag.setCardAsMargin(0, 0, 0, 0)
        self.name_tag_node = self.body.attachNewNode(self.name_tag)
        self.name_tag_node.setScale(0.3)
        self.name_tag_node.setBillboardPointEye()
        self.__update_name_tag()

    def __update_name_tag(self):
        if self.name_tag is not None and self.name_tag_node is not None:
            self.name_tag.setText(self.name)
            self.logger.info(f"Enemy now named {self.name}")
            self.name_tag_node.setPos(0,0,1)

    def __update_name(self, name: str):
        self.name = name
        self.__update_name_tag()

    def jump(self, offset: float):
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        # calc current jump pos based on time offset
        # base velocity - gravity * offset
        self.vertical_velocity = JUMP_VELOCITY - (GRAVITY * offset)
        self.body.setZ(self.body.getZ() + (self.vertical_velocity * offset))

    def sweep(self, sweep_animation_no: int, offset: float):
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        start_frame = int(offset * 24)
        self.logger.debug(f"Block started at frame {start_frame}")
        total_frames = self.sword.getAnimControl("sweep1").getNumFrames()
        if start_frame > total_frames:
            return
        self.sword.play(f"sweep{sweep_animation_no}")
        self.inAttack = True
        self.inBlock = False
        self.schedule_sweep_tasks(start_frame)

    def block(self, offset: float):
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        start_frame = int(offset * 24)
        self.logger.debug(f"Block started at frame {start_frame}")
        total_frames = self.sword.getAnimControl("block1").getNumFrames()
        if start_frame > total_frames:
            return
        self.start_block_animation(start_frame)
        self.inAttack = True
        self.inBlock = True
        self.schedule_block_tasks(start_frame)

    def stab(self, offset: float):
        start_frame = int(offset * 24)
        total_frames = self.sword.getAnimControl("stab").getNumFrames()
        if start_frame > total_frames:
            return
        self.logger.debug(f"Stab started at frame {start_frame}")
        self.sword.play("stab", fromFrame=start_frame)
        self.schedule_stab_tasks(start_frame)

    def __handle_actions(self, actions: List[PlayerAction], offsets: List[float]):
        assert len(actions) == len(offsets)
        self.logger.debug(f"Handling {len(actions)} remote actions")
        for action in actions:
            start_time = offsets.pop(0)
            offset = self.match_timer - start_time
            messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
            match action:
                case PlayerAction.JUMP:
                    self.jump(offset)
                case PlayerAction.ATTACK_1:
                    self.stab(offset)
                case PlayerAction.BLOCK:
                    self.block(offset)
                case PlayerAction.SWEEP_1:
                    self.sweep(sweep_animation_no=1, offset=offset)
                case PlayerAction.SWEEP_2:
                    self.sweep(sweep_animation_no=2, offset=offset)
                case PlayerAction.SWEEP_3:
                    self.sweep(sweep_animation_no=3, offset=offset)
                case PlayerAction.GOT_BLOCKED:
                    self.__remote_block(offset)
                case _:
                    self.logger.debug(f"Code {action} not implemented")

    def __remote_block(self, start_time):
        self.logger.debug("Network block")
        self.handle_attack_being_blocked(None, force=True, frame_offset=int(self.match_timer - start_time) * 24)

    def set_state(self, update: PlayerInfo):
        if not self.is_puppet:
            self.logger.error("Tried to update enemy that is not controlled by other player")
            return
        # an attack package does not! contain any other info
        if len(update.actions) > 0:
            self.__handle_actions(update.actions, update.action_offsets)

        if update.position is not None:
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
        if update.movement is not None:
            # The vector is normalized when sending it
            self.movement_vector = Vec3(update.movement.x , update.movement.y, 0)
            # This is not the correct labelling...I am aware but idc
        if update.lookRotation is not None:
            self.head.setP(update.lookRotation)
        if update.bodyRotation is not None:
            self.body.setH(update.bodyRotation)

    def update(self, dt, player_pos=None):
        super().update(dt)
        if self.body.is_empty():
            return
        self.match_timer += dt
        self.apply_gravity(dt)
        flat_move = Vec2(self.movement_vector.x, self.movement_vector.y)
        if self.is_dashing:
            direction = self.body.getRelativeVector(self.head, Vec3.forward())
            self.vertical_velocity = direction.z * DASH_SPEED
            flat_move.x += direction.x * DASH_SPEED
            flat_move.y += direction.y * DASH_SPEED
        flat_move = flat_move * dt

        # network desync soft correction
        flat_move.x += self.correction_vector.x * dt
        flat_move.y += self.correction_vector.y * dt
         
        self.body.setFluidPos(self.body, Vec3(flat_move.x, flat_move.y, self.vertical_velocity * dt))
