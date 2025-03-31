import logging
import math
from direct.task.Task import Task, messenger

from direct.showbase.ShowBase import ShowBase

from game.entities.map import Map
from game.gui.const import GuiStates, StateTransitionEvents

from panda3d.core import WindowProperties, CollisionTraverser, loadPrcFileData


from game.const.events import CANCEL_QUEUE_EVENT, DEFEAT_EVENT, ENTER_QUEUE_EVENT, GUI_FORCE_MAIN_MENU_EVENT, GUI_MAIN_MENU_EVENT, GUI_PLAY_EVENT, GUI_QUEUE_EVENT, GUI_RETURN_EVENT, GUI_SETTINGS_EVENT, GUI_UPDATE_ANTI_PLAYER_NAME, NETWORK_SEND_PRIORITY_EVENT, RESET_PLAYER_CAMERA, SET_PLAYER_NO_EVENT, START_GAME_EVENT, WIN_EVENT
from game.const.networking import TIME_BETWEEN_PACKAGES_IN_S
from game.const.player import MAIN_MENU_CAMERA_HEIGHT, MAIN_MENU_CAMERA_ROTATION_RADIUS, MAIN_MENU_CAMERA_ROTATION_SPEED, MAIN_MENU_PLAYER_POSITION
from game.entities.anti_player import AntiPlayer
from game.entities.bot import Bot
from game.entities.player import Player
from game.helpers.config import get_player_name, load_config
from game.helpers.helpers import *
from game.gui.gui_manager import GuiManager
import uuid

from game.helpers.sound import SoundHelper
from game.networking.queue import check_queue_status, join_queue, leave_queue
from game.networking.websocket import MatchWS
from game.utils.input import disable_mouse, enable_mouse
from game.utils.name_generator import generate_name
from shared.const.queue_status import QueueStatus

from shared.types.player_info import PlayerInfo
from shared.types.status_message import StatusMessages

from direct.actor.Actor import Actor

class MainGame(ShowBase):
    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        properties = WindowProperties()
        properties.setSize(1280, 720)
        self.win.requestProperties(properties)
        self.game_task = base.taskMgr.add(self.__main_loop, "gameLoop")
        self.queue_task = None
        self.ws_handle_task = None
        self.logger.debug("Window setup done...")
        base.camLens.setNear(0.01)
        base.camLens.setFov(120)
        
        base.cTrav = CollisionTraverser()
        #base.cTrav.showCollisions(render)
        base.enableParticles()
        
        loadPrcFileData("", "interpolate-frames 1")
        load_config()
        
        self.waterfallCount = 0
        self.mouse_locked = False

        self.player: None | Player = None
        self.anti_player: None | AntiPlayer | Bot = None

        # Setup gui handling
        self.gui_manager = GuiManager()
        self.accept("escape", self.gui_manager.handle_custom, [StateTransitionEvents.ESC])
        self.accept(GUI_RETURN_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.RETURN])
        self.accept(GUI_SETTINGS_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.SETTINGS])
        self.accept(GUI_PLAY_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.PLAY])
        self.accept(GUI_MAIN_MENU_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.MAIN_MENU])
        self.accept(GUI_QUEUE_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.QUEUE])
        self.accept(GUI_FORCE_MAIN_MENU_EVENT, self.__force_main_menu)
        self.logger.debug("Gui handling and state machine initialized...")

        # General event handling
        self.accept(START_GAME_EVENT, self.__start_game)
        self.accept(ENTER_QUEUE_EVENT, self.__enter_queue)
        self.accept(CANCEL_QUEUE_EVENT, self.__cancel_queue)
        self.accept(WIN_EVENT, self.__finish_game, [True])
        self.accept(DEFEAT_EVENT, self.__finish_game, [False])
        self.accept(RESET_PLAYER_CAMERA, self.__position_player_camera)

        self.accept(NETWORK_SEND_PRIORITY_EVENT, self.__priority_ws_send)

        self.player_id: str = str(uuid.uuid4())
        self.match_id: None | str = None

        self.is_online: bool = False
        self.ws: None | MatchWS = None

        self.time_since_last_package: int = 1_000_000
        self.camera_angle = 0

        self.map = Map()
        self.map.build_map()
        self.sound_handler = SoundHelper()
        self.sound_handler.start_main_menu_music()

        self.__add_and_focus_main_menu_player()

    def __force_main_menu(self):
        if self.gui_manager.is_ingame():
            self.__finish_game(False, fast_exit=True)
            self.sound_handler.start_main_menu_music()
        self.gui_manager.handle_custom(StateTransitionEvents.FORCE_MAIN_MENU)

    def __add_and_focus_main_menu_player(self):
        self.logger.info("Place camera and player")
        if self.player is not None:
            self.player.destroy()
        self.player = Actor(getModelPath("idle_actor"),{"idle": getModelPath("idle_actor-Idle")})
        self.player.setPos(MAIN_MENU_PLAYER_POSITION)
        self.player.loop("idle")
        
        self.player.reparentTo(render)
        self.camera.reparentTo(render)
        self.camera_angle = 0
    
    def __finish_game(self, is_victory, fast_exit=None):
        enable_mouse()
        self.logger.info(f"Received game finish where victory: {is_victory}")
        self.gui_manager.set_online(False)
       
        if self.ws is not None:
            self.ws.close(reason="Finished")
        if self.ws_handle_task is not None:
            self.ws_handle_task.cancel()
            self.ws_handle_task = None
        self.is_online = False
        self.match_id = None
        if self.player is not None:
            self.player.destroy()
        self.__add_and_focus_main_menu_player()
        if self.anti_player is not None:
            self.anti_player.destroy()
        if fast_exit:
            return
        
        if is_victory:
            self.sound_handler.play_victory_sound()
            self.sound_handler.start_main_menu_music()
            self.gui_manager.handle_custom(StateTransitionEvents.WIN)
        else:
            self.sound_handler.start_main_menu_music()
            self.gui_manager.handle_custom(StateTransitionEvents.DEFEAT)

    def __enter_queue(self):
        messenger.send(GUI_QUEUE_EVENT)
        self.queue_task = base.taskMgr.doMethodLater(1, self.__check_queue_status, "queue_check")
        base.taskMgr.add(join_queue, 'join_queue_task', extraArgs=[self.player_id])

    def __cancel_queue(self):
        if self.match_id is None:
            self.logger.info("Exiting queue and stopping background check.")
            leave_queue(self.player_id)
        if self.queue_task is not None:
            self.queue_task.remove()
        self.queue_task = None

    def __check_queue_status(self, task):
        success, status, match_id = check_queue_status(self.player_id)
        if not success:
            return Task.again
        if status != QueueStatus.MATCHED.value:
            return Task.again
        if len(match_id) > 0:
            self.match_id = match_id
            self.logger.info("Game found! Joining game...")
            self.__start_game(match_id, False)
            return Task.done

    def __start_game(self, match_id="", is_offline=True):
        self.sound_handler.start_combat_music()
                
        self.is_online = not is_offline
        self.gui_manager.set_online(self.is_online)

        disable_mouse()
        if self.player is not None:
            self.player.removeNode()

        self.player = Player(self.camera,self.win, self.is_online)
        self.__position_player_camera()
               
        if is_offline:
            self.logger.info("Starting game in offline mode...")
            self.match_id = None
            self.anti_player = Bot(self.win)
            messenger.send(SET_PLAYER_NO_EVENT, [StatusMessages.PLAYER_1])
            self.player.start_match_timer()
            self.anti_player.start_match_timer()
        else:
            self.logger.info("Starting online game...")
            self.anti_player = AntiPlayer(self.win)
            if self.queue_task is not None:
                self.queue_task.remove()
            self.queue_task = None
            self.ws = MatchWS(
                match_id=match_id, 
                player_id=self.player_id, 
                player_name=get_player_name(),
                recv_callback=self.__process_ws_message)
        messenger.send(GUI_PLAY_EVENT)
        if is_offline:
            messenger.send(GUI_UPDATE_ANTI_PLAYER_NAME, [generate_name()])

    def __position_player_camera(self, update_pointer=True):
        if type(self.player) is Player and self.player is not None:
            self.camera.setHpr(0,0,0)
            self.camera.reparentTo(self.player.head)
            self.camera.setPos(0,0.09,0.4)
            self.player.head.setP(0)
            if update_pointer:
                self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)
                  
    def __process_ws_message(self, player_info: PlayerInfo):
        self.player.update_state(player_info)
        self.anti_player.set_state(player_info)

    def __priority_ws_send(self, packet: PlayerInfo):
        if not self.is_online:
            return
        if self.ws is not None:
            packet.health = self.player.health
            packet.enemy_health = self.anti_player.health
            self.ws.send_game_data(packet)

    def __main_loop_online(self, dt):
        self.time_since_last_package += dt
        if self.time_since_last_package > TIME_BETWEEN_PACKAGES_IN_S:
            packet = self.player.get_current_state()
            packet.enemy_health = self.anti_player.health
            self.ws.send_game_data(packet)
            self.time_since_last_package = 0

    def rotate_camera(self, dt):
        self.camera_angle += MAIN_MENU_CAMERA_ROTATION_SPEED * dt

        # Compute new position
        x = MAIN_MENU_PLAYER_POSITION.x +  MAIN_MENU_CAMERA_ROTATION_RADIUS * math.cos(self.camera_angle)
        y = MAIN_MENU_PLAYER_POSITION.y + MAIN_MENU_CAMERA_ROTATION_RADIUS * math.sin(self.camera_angle)

        # Set camera position and look at the center
        self.camera.setPos(x, y, MAIN_MENU_CAMERA_HEIGHT)
        self.camera.lookAt(MAIN_MENU_PLAYER_POSITION)

    def __main_loop(self, task):
        dt = self.clock.dt

        if not self.gui_manager.is_ingame():
            self.rotate_camera(dt)
            return Task.cont

        # Fix issue within settings overlay and camera pos
        if self.gui_manager.gui_state_machine.getCurrentOrNextState() == GuiStates.SETTINGS_OVERLAY.value:
            self.__position_player_camera(update_pointer=False)

        if type(self.player) is not Actor:
            self.player.update(dt)

        if self.is_online:
            self.anti_player.update(dt)
            self.__main_loop_online(dt)
            return Task.cont
        else:
            self.anti_player.update(dt, self.player)
        return Task.cont

