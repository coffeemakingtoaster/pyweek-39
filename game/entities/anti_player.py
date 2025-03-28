from typing import List
from game.const.events import GUI_UPDATE_LATENCY, NETWORK_SEND_PRIORITY_EVENT
from game.const.networking import POSITION_DIFF_THRESHOLD
from game.const.player import DASH_SPEED, GRAVITY, JUMP_VELOCITY
from game.entities.base_entity import EntityBase
from game.helpers.helpers import *
from panda3d.core import Vec3, Vec2, TextNode
from shared.types.player_info import PlayerAction, PlayerInfo
from game.utils.name_generator import generate_name

class AntiPlayer(EntityBase):
    def __init__(self, window, is_puppet=False) -> None:
        self.name = generate_name()
        super().__init__(window, "enemy", is_puppet, f"Enemy {'(online)' if is_puppet else '(local)'}")

        self.name_tag = None
        self.name_tag_node = None

        self.is_puppet = is_puppet

        self.movement_vector = Vec3(0,0,0)
        self.correction_vector = Vec3(0,0,0)

        self.accept("q", self.debug_stab)
        self.accept("e", self.debug_block)
        self.accept("f", self.debug_sweep)

        self.__add_name_tag()

        if self.is_puppet:
            self.logger.info(f"Created enemy for opponent")
        else:
            self.logger.info(f"Created bot enemy")
 
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
        self.__update_name()

    def __update_name(self):
        if self.name_tag is not None and self.name_tag_node is not None:
            self.name_tag.setText(self.name)
            self.logger.info(f"Enemy now named {self.name}")
            self.name_tag_node.setPos(0,0,1)

    def set_name(self, name: str):
        self.name = name
        self.__update_name()

    def jump(self, start_time: float = 0.0):
        if start_time == 0.0 and not self.is_puppet:
            self.vertical_velocity = JUMP_VELOCITY
            return
        offset = self.match_timer - start_time
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        # calc current jump pos based on time offset
        # base velocity - gravity * offset
        self.vertical_velocity = JUMP_VELOCITY - (GRAVITY * offset)
        self.body.setZ(self.body.getZ() + (self.vertical_velocity * offset))

    def __sweep_safe(self, is_alternate_sweep=False, frame_offset=0):
        # sweep and sweep2 have the same duration
        total_frames = self.sword.getAnimControl("sweep").getNumFrames()
        if frame_offset > total_frames:
            self.logger.warning(f"Skipped sweep animation because latency exceeded frame count {frame_offset}")
            return
        self.sword.play("sweep2" if is_alternate_sweep else "sweep")
        self.inAttack = True
        self.inBlock = False
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=14, fn=self.playSoundLater, name=f"{self.id}-playSoundSweep", extraArgs=["sweep"])
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=14, fn=self.turnSwordLethal, name=f"{self.id}-makeSwordLethalTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=21, fn=self.turnSwordHarmless, name=f"{self.id}-makeSwordHarmlessTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.endAttack, name=f"{self.id}-endAttackTask")

    def sweep(self, is_alternate_sweep=False, start_time=0.0):
        if not self.is_puppet or start_time == 0.0:
            self.__sweep_safe(is_alternate_sweep=is_alternate_sweep)
            return
        offset = self.match_timer - start_time
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        start_frame = int(offset * 24)
        self.logger.debug(f"Block started at frame {start_frame}")
        self.__sweep_safe(is_alternate_sweep=is_alternate_sweep, frame_offset=start_frame)

    def __block_safe(self, frame_offset=0):
        total_frames = self.sword.getAnimControl("block").getNumFrames()
        if frame_offset > total_frames:
            self.logger.warning(f"Skipped block animation because latency exceeded frame count {frame_offset}")
            return
        self.sword.play("block")
        self.inAttack = True
        self.inBlock = True
        taskMgr.remove(f"{self.id}-endAttackTask")
        taskMgr.remove(f"{self.id}-makeSwordLethalTask")
        taskMgr.remove(f"{self.id}-makeSwordHarmlessTask")
        frames = self.sword.getAnimControl("block").getNumFrames()
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=5, fn=self.turnSwordBlock, name=f"{self.id}-makeSwordBlockTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=15, fn=self.turnSwordSword, name=f"{self.id}-makeSwordSwordTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=15, fn=self.turnSwordSword, name=f"{self.id}-makeSwordSwordTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.endBlock, name=f"{self.id}-endBlockTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.endBlock, name=f"{self.id}-endAttackTask")

    def block(self, start_time=0.0):
        if not self.is_puppet or start_time == 0.0:
            self.__block_safe()
            return
        offset = self.match_timer - start_time
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        start_frame = int(offset * 24)
        self.logger.debug(f"Block started at frame {start_frame}")
        self.__block_safe(start_frame)

    def __stab_safe(self, frame_offset=0):
        total_frames = self.sword.getAnimControl("stab").getNumFrames()
        if frame_offset > total_frames:
            self.logger.warning(f"Skipped attack animation because latency exceeded frame count {frame_offset}")
            return
        self.sword.play("stab", fromFrame=frame_offset)
        self.logger.debug(f"Frame offset is {frame_offset}")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=5, fn=self.playSoundLater, name=f"{self.id}-playSoundStab", extraArgs=["stab"])
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=25, fn=self.turnSwordLethal, name=f"{self.id}-makeSwordLethalTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=25, fn=self.start_dash, name=f"{self.id}-startDashingTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=32, fn=self.turnSwordHarmless, name=f"{self.id}-makeSwordHarmlessTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=32, fn=self.end_dash, name=f"{self.id}-endDashingTask")
        self.__schedule_or_run(offset_frame=frame_offset, wanted_frame=total_frames, fn=self.endAttack, name=f"{self.id}-endAttackTask")

    def __schedule_or_run(self, offset_frame: int, wanted_frame: int, fn, name: str, extraArgs=[None]):
        # Already happended -> do now
        if offset_frame >= wanted_frame:
            # Pass none as tasks expect 
            fn(*extraArgs)
            return
        if len(extraArgs) > 0:
            base.taskMgr.doMethodLater((wanted_frame - offset_frame)/24, fn, name,extraArgs=extraArgs)
            return
        base.taskMgr.doMethodLater((wanted_frame - offset_frame)/24, fn, name)
    
    def handleSwordCollisionEnd(self,entry):
        self.logger.debug(f"no longer colliding with {entry}")

    def debug_stab(self):
        self.stab()

    def debug_block(self):
        self.block()

    def debug_sweep(self):
        self.sweep()

    def stab(self, start_time: float = 0.0):
        # AI controlled
        if not self.is_puppet or start_time == 0.0:
            self.__stab_safe()
            return
        offset = self.match_timer - start_time
        messenger.send(GUI_UPDATE_LATENCY, [offset * 1000])
        start_frame = int(offset * 24)
        self.logger.debug(f"Stab started at frame {start_frame}")
        self.__stab_safe(start_frame)

    def __handle_actions(self, actions: List[PlayerAction], offsets: List[float]):
        assert len(actions) == len(offsets)
        self.logger.debug(f"Handling {len(actions)} remote actions")
        for action in actions:
            offset = offsets.pop(0)
            match action:
                case PlayerAction.JUMP:
                    self.jump(offset)
                case PlayerAction.ATTACK_1:
                    self.stab(offset)
                case PlayerAction.BLOCK:
                    self.block(offset)
                case PlayerAction.SWEEP_1:
                    self.sweep(start_time=offset)
                case PlayerAction.SWEEP_2:
                    self.sweep(is_alternate_sweep=True, start_time=offset)
                case _:
                    self.logger.debug(f"Code {action} not implemented")

    def set_state(self, update: PlayerInfo):
        if not self.is_puppet:
            self.logger.error("Tried to update enemy that is not controlled by other player")
            return
        # an attack package does not! contain any other info
        if len(update.actions) > 0:
            self.__handle_actions(update.actions, update.action_offsets)
        if self.health != update.health:
            self.logger.error("Desync between received and perceived health")
            self.take_damage(self.health - update.health)
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
