from enum import Enum
from direct.fsm.FSM import FSM
import logging

from src.gui.gui_base import GuiBase
from src.gui.main_menu import MainMenu

class GuiStates(Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    SETTINGS = "SETTINGS"
    MAIN_MENU = "MAIN_MENU"
    GAME_END_SCREEN = "GAME_END_SCREEN"
    LIMBO = "LIMBO"

class StateTransitionEvents(Enum):
    ESC = "ESC"
    RETURN = "RETURN"
    SETTINGS = "GOTO_SETTINGS"
    MAIN_MENU = "GOTO_MAIN_MENU"
    PLAY = "PLAY"
    FORCE_MAIN_MENU = "GOTO_MAIN_MENU"

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
        (GuiStates.PAUSED.value, StateTransitionEvents.ESC.value) : GuiStates.RUNNING.value,
        (GuiStates.PAUSED.value, StateTransitionEvents.RETURN.value) : GuiStates.RUNNING.value,
        (GuiStates.SETTINGS.value, StateTransitionEvents.ESC.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.SETTINGS.value, StateTransitionEvents.RETURN.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN.value, StateTransitionEvents.ESC.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN.value, StateTransitionEvents.RETURN.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.MAIN_MENU.value, StateTransitionEvents.PLAY.value) : GuiStates.RUNNING.value,
        (GuiStates.MAIN_MENU.value, StateTransitionEvents.SETTINGS.value) : GuiStates.SETTINGS.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.PAUSED.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.SETTINGS.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.GAME_END_SCREEN.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.MAIN_MENU.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
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
            case _:
                self.logger.warning(f"State {target_state} not yet implemented by gui manager. Returning to main menu")
                self.gui_state_machine.state  = GuiStates.MAIN_MENU.value
                self.currently_displayed_gui_state = GuiStates.LIMBO
                self.__update_displayed_gui()
