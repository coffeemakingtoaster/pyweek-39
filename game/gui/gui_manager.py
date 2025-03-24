from enum import Enum
from direct.fsm.FSM import FSM
import logging

from game.gui.game_end import GameEnd
from game.gui.gui_base import GuiBase
from game.gui.hud import Hud
from game.gui.main_menu import MainMenu
from game.gui.queue_menu import QueueMenu
from game.gui.settings_menu import SettingsMenu

class GuiStates(Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    SETTINGS = "SETTINGS"
    MAIN_MENU = "MAIN_MENU"
    GAME_END_SCREEN_WIN = "GAME_END_SCREEN_WIN"
    GAME_END_SCREEN_DEFEAT = "GAME_END_SCREEN_DEFEAT"
    QUEUE = "QUEUE"
    LIMBO = "LIMBO"

class StateTransitionEvents(Enum):
    ESC = "ESC"
    RETURN = "RETURN"
    SETTINGS = "GOTO_SETTINGS"
    MAIN_MENU = "GOTO_MAIN_MENU"
    QUEUE = "QUEUE"
    PLAY = "PLAY"
    FORCE_MAIN_MENU = "FORCE_GOTO_MAIN_MENU"
    WIN = "WIN"
    DEFEAT = "DEFEAT"

# State machine to implement gui state change interactions
class GuiStateMachine(FSM):
    def __init__(self, initial_state=GuiStates.MAIN_MENU):
        FSM.__init__(self, "GuiStateMachine")
        # Initial state
        self.state = initial_state.value
        self.logger = logging.getLogger(__name__)

    nextState = {
        (GuiStates.RUNNING.value, StateTransitionEvents.ESC.value) : GuiStates.PAUSED.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.PLAY.value) : GuiStates.RUNNING.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.WIN.value) : GuiStates.GAME_END_SCREEN_WIN.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.DEFEAT.value) : GuiStates.GAME_END_SCREEN_DEFEAT.value,
        (GuiStates.PAUSED.value, StateTransitionEvents.ESC.value) : GuiStates.RUNNING.value,
        (GuiStates.PAUSED.value, StateTransitionEvents.RETURN.value) : GuiStates.RUNNING.value,
        (GuiStates.SETTINGS.value, StateTransitionEvents.ESC.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.SETTINGS.value, StateTransitionEvents.RETURN.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN_WIN.value, StateTransitionEvents.ESC.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN_WIN.value, StateTransitionEvents.RETURN.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN_DEFEAT.value, StateTransitionEvents.ESC.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN_DEFEAT.value, StateTransitionEvents.RETURN.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.MAIN_MENU.value, StateTransitionEvents.PLAY.value) : GuiStates.RUNNING.value,
        (GuiStates.MAIN_MENU.value, StateTransitionEvents.QUEUE.value) : GuiStates.QUEUE.value,
        (GuiStates.MAIN_MENU.value, StateTransitionEvents.SETTINGS.value) : GuiStates.SETTINGS.value,
        (GuiStates.QUEUE.value, StateTransitionEvents.RETURN.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.QUEUE.value, StateTransitionEvents.PLAY.value) : GuiStates.RUNNING.value,
        (GuiStates.QUEUE.value, StateTransitionEvents.ESC.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.PAUSED.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.SETTINGS.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN_WIN.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN_DEFEAT.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.MAIN_MENU.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.QUEUE.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
    }

    def defaultFilter(self, request: str, args):
        key = (self.state, request)
        self.logger.debug(f"State machine change input {key}")
        return self.nextState.get(key)

class GuiManager():
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.gui_state_machine = GuiStateMachine()
        self.currently_displayed_gui_state: GuiStates = GuiStates.LIMBO
        self.current_ui: None | GuiBase = None
        self.__update_displayed_gui()

    def handle_custom(self, request_input: StateTransitionEvents):
        self.logger.debug(f"Requesting gui state change with event {request_input.value}")
        self.gui_state_machine.request(request_input.value)
        self.__update_displayed_gui()

    def __update_displayed_gui(self):
        # Current GUI == Wanted GUI
        if self.currently_displayed_gui_state == self.gui_state_machine.getCurrentOrNextState():
            return

        if self.current_ui is None:
            self.logger.warning("Current ui is None! This should only happen once")
        else:
            self.current_ui.destroy()

        target_state = self.gui_state_machine.getCurrentOrNextState()
        self.logger.info(f"Now rendering gui for state {target_state}")
        match target_state:
            case GuiStates.MAIN_MENU.value:
                self.current_ui = MainMenu()
                self.currently_displayed_gui_state = GuiStates.MAIN_MENU
            case GuiStates.QUEUE.value:
                self.current_ui = QueueMenu()
                self.currently_displayed_gui_state = GuiStates.QUEUE
            case GuiStates.GAME_END_SCREEN_WIN.value:
                self.current_ui = GameEnd(True)
                self.currently_displayed_gui_state = GuiStates.GAME_END_SCREEN_WIN
            case GuiStates.GAME_END_SCREEN_DEFEAT.value:
                self.current_ui = GameEnd(False)
                self.currently_displayed_gui_state = GuiStates.GAME_END_SCREEN_DEFEAT
            case GuiStates.RUNNING.value:
                self.current_ui = Hud()
                self.currently_displayed_gui_state = GuiStates.RUNNING
            case GuiStates.SETTINGS.value:
                self.current_ui = SettingsMenu()
                self.currently_displayed_gui_state = GuiStates.SETTINGS
            case _:
                self.logger.warning(f"State {target_state} not yet implemented by gui manager. Returning to main menu")
                self.gui_state_machine.state  = GuiStates.MAIN_MENU.value
                self.currently_displayed_gui_state = GuiStates.LIMBO
                self.__update_displayed_gui()
