import asyncio
import logging
from direct.task.Task import Task, messenger
from panda3d.core import *

from direct.showbase.ShowBase import ShowBase

from game.const.events import CANCEL_QUEUE_EVENT, DEFEAT_EVENT, ENTER_QUEUE_EVENT, GUI_MAIN_MENU_EVENT, GUI_PLAY_EVENT, GUI_QUEUE_EVENT, GUI_RETURN_EVENT, GUI_SETTINGS_EVENT, START_GAME_EVENT, WIN_EVENT
from game.const.networking import TIME_BETWEEN_PACKAGES_IN_S
from game.entities.player import Player
from game.gui.gui_manager import GuiManager, GuiStates, StateTransitionEvents
import uuid

from game.networking.queue import check_queue_status, join_queue, leave_queue
from game.networking.websocket import MatchWS
from shared.const.queue_status import QueueStatus

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

        self.player: None | Player = None

        # Setup gui handling
        self.gui_manager = GuiManager()
        self.accept("escape", self.gui_manager.handle_custom, [StateTransitionEvents.ESC])
        self.accept(GUI_RETURN_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.RETURN])
        self.accept(GUI_SETTINGS_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.SETTINGS])
        self.accept(GUI_PLAY_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.PLAY])
        self.accept(GUI_MAIN_MENU_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.MAIN_MENU])
        self.accept(GUI_QUEUE_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.QUEUE])
        self.logger.debug("Gui handling and state machine initialized...")

        # General event handling
        self.accept(START_GAME_EVENT, self.__start_game)
        self.accept(ENTER_QUEUE_EVENT, self.__enter_queue)
        self.accept(CANCEL_QUEUE_EVENT, self.__cancel_queue)
        self.accept(WIN_EVENT, self.__finish_game, [True])
        self.accept(DEFEAT_EVENT, self.__finish_game, [False])

        self.player_id: str = str(uuid.uuid4())
        self.match_id: None | str = None

        self.is_online: bool = False
        self.ws: None | MatchWS = None

        self.time_since_last_package: int = 1_000_000

    def __finish_game(self, is_victory):
        self.logger.info(f"Received game finish where victory: {is_victory}")
        if self.ws is not None:
            self.ws.close(reason="Finished")
        if self.ws_handle_task is not None:
            self.ws_handle_task.cancel()
            self.ws_handle_task = None
        self.is_online = False
        self.match_id = None
        if self.player is not None:
            self.player.destroy()
        if is_victory:
            self.gui_manager.handle_custom(StateTransitionEvents.WIN)
        else:
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

    def __start_game(self, match_id="",is_offline=True):
        self.player = Player()
        self.is_online = not is_offline
        if is_offline:
            self.logger.info("Starting game in offline mode...")
            self.match_id = None
        else:
            self.logger.info("Starting online game...")
            if self.queue_task is not None:
                self.queue_task.remove()
            self.queue_task = None
            self.ws = MatchWS(
                match_id=match_id, 
                player_id=self.player_id, 
                recv_callback=self.__process_ws_message)
        messenger.send(GUI_PLAY_EVENT)
           
    def __process_ws_message(self, msg):
        self.logger.info(msg)

    def __main_loop_online(self, dt):
        self.time_since_last_package += dt
        if self.time_since_last_package > TIME_BETWEEN_PACKAGES_IN_S:
            self.ws.send_game_data(
                self.player.get_current_state()
            )
            self.time_since_last_package = 0

    def __main_loop(self, task):
        dt = self.clock.dt

        if self.gui_manager.gui_state_machine.getCurrentOrNextState() != GuiStates.RUNNING.value:
            return Task.cont

        self.player.update(dt)

        if self.is_online:
            self.__main_loop_online(dt)
            return Task.cont
        else:
            return Task.cont
