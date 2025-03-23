import logging
from panda3d.core import *

from direct.showbase.ShowBase import ShowBase

from game.const.events import GUI_MAIN_MENU_EVENT, GUI_PLAY_EVENT, GUI_RETURN_EVENT, GUI_SETTINGS_EVENT, START_GAME_EVENT
from game.gui.gui_manager import GuiManager, StateTransitionEvents

class MainGame(ShowBase):
    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        properties = WindowProperties()
        properties.setSize(1280, 720)
        self.win.requestProperties(properties)
        self.gameTask = base.taskMgr.add(self.__main_loop, "gameLoop")
        self.logger.debug("Window setup done...")

        # Setup gui handling
        self.gui_manager = GuiManager()
        self.accept("escape", self.gui_manager.handle_custom, [StateTransitionEvents.ESC])
        self.accept(GUI_RETURN_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.RETURN])
        self.accept(GUI_SETTINGS_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.SETTINGS])
        self.accept(GUI_PLAY_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.PLAY])
        self.accept(GUI_MAIN_MENU_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.MAIN_MENU])
        self.logger.debug("Gui handling and state machine initialized...")

        # General event handling
        self.accept(START_GAME_EVENT, self.__start_game)

    def __start_game(self):
        messenger.send(GUI_PLAY_EVENT)
        pass

    def __main_loop(self, task):
        dt = self.clock.dt
