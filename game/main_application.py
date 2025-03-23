import logging
from time import sleep, time
from direct.task.Task import Task
from panda3d.core import *

from direct.showbase.ShowBase import ShowBase

from game.const.events import CANCEL_QUEUE, ENTER_QUEUE, GUI_MAIN_MENU_EVENT, GUI_PLAY_EVENT, GUI_QUEUE_EVENT, GUI_RETURN_EVENT, GUI_SETTINGS_EVENT, START_GAME_EVENT
from game.gui.gui_manager import GuiManager, StateTransitionEvents
import uuid

from game.networking.queue import check_queue_status, join_queue, leave_queue
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
        self.logger.debug("Window setup done...")

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
        self.accept(ENTER_QUEUE, self.__enter_queue)
        self.accept(CANCEL_QUEUE, self.__cancel_queue)

        self.player_id = str(uuid.uuid4())

    def __enter_queue(self):
        messenger.send(GUI_QUEUE_EVENT)
        join_queue(self.player_id)
        self.queue_task = base.taskMgr.add(self.__check_queue_status, "queue_check")

    def __cancel_queue(self):
        self.logger.info("Exiting queue and stopping background check.")
        leave_queue(self.player_id)
        self.queue_task.remove()
        self.queue_task = None

    def __check_queue_status(self, task):
        sleep(1)
        success, status, match_id = check_queue_status(self.player_id)
        if not success:
            return Task.again
        if status != QueueStatus.MATCHED:
            self.logger.debug("Not matched yet...")
            return Task.again
        if len(match_id) > 0:
            self.logger.info("Game found! Joining game...")
            self.__start_game()
            return Task.done

    def __start_game(self):
        messenger.send(GUI_PLAY_EVENT)
        pass

    def __main_loop(self, task):
        dt = self.clock.dt
