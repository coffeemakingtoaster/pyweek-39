from direct.fsm.FSM import FSM
import logging

from game.const.events import RESET_PLAYER_CAMERA
from game.gui.const import GuiStates, StateTransitionEvents
from game.gui.game_end import GameEnd
from game.gui.gui_base import GuiBase
from game.gui.hud import Hud
from game.gui.main_menu import MainMenu
from game.gui.queue_menu import QueueMenu
from game.gui.settings_menu import SettingsMenu
from game.utils.input import disable_mouse, enable_mouse

# State machine to implement gui state change interactions
class GuiStateMachine(FSM):
    def __init__(self, initial_state=GuiStates.MAIN_MENU):
        FSM.__init__(self, "GuiStateMachine")
        # Initial state
        self.state = initial_state.value
        self.logger = logging.getLogger(__name__)

    nextState = {
        (GuiStates.RUNNING.value, StateTransitionEvents.ESC.value) : GuiStates.SETTINGS_OVERLAY.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.PLAY.value) : GuiStates.RUNNING.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.WIN.value) : GuiStates.GAME_END_SCREEN_WIN.value,
        (GuiStates.RUNNING.value, StateTransitionEvents.DEFEAT.value) : GuiStates.GAME_END_SCREEN_DEFEAT.value,
        (GuiStates.SETTINGS_OVERLAY.value, StateTransitionEvents.DEFEAT.value) : GuiStates.GAME_END_SCREEN_DEFEAT.value,
        (GuiStates.SETTINGS_OVERLAY.value, StateTransitionEvents.WIN.value) : GuiStates.GAME_END_SCREEN_WIN.value,
        (GuiStates.SETTINGS_OVERLAY.value, StateTransitionEvents.ESC.value) : GuiStates.RUNNING.value,
        (GuiStates.SETTINGS_OVERLAY.value, StateTransitionEvents.RETURN.value) : GuiStates.RUNNING.value,
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
        (GuiStates.SETTINGS.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
        (GuiStates.SETTINGS_OVERLAY.value, StateTransitionEvents.FORCE_MAIN_MENU.value) : GuiStates.MAIN_MENU.value,
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
        self.cached_ui: None | GuiBase = None
        self.__update_displayed_gui()

    def handle_custom(self, request_input: StateTransitionEvents):
        self.logger.debug(f"Requesting gui state change with event {request_input.value}")
        self.gui_state_machine.request(request_input.value)
        self.__update_displayed_gui()

    def is_ingame(self):
        return self.gui_state_machine.getCurrentOrNextState() in [GuiStates.RUNNING.value, GuiStates.SETTINGS_OVERLAY.value]

    def __update_displayed_gui(self):
        # Current GUI == Wanted GUI
        if self.currently_displayed_gui_state == self.gui_state_machine.getCurrentOrNextState():
            return

        if self.current_ui is None:
            self.logger.warning("Current ui is None! This should only happen once")
        else:
            if self.gui_state_machine.getCurrentOrNextState() != GuiStates.SETTINGS_OVERLAY.value:
                self.current_ui.destroy()
            else:
                self.logger.debug("Skipping gui destroy because of overlay")
                self.cached_ui = self.current_ui

        if self.currently_displayed_gui_state == GuiStates.SETTINGS_OVERLAY:
            assert self.cached_ui is not None
            if self.gui_state_machine.getCurrentOrNextState() == GuiStates.RUNNING.value:
                disable_mouse()
                self.current_ui = self.cached_ui
                self.currently_displayed_gui_state = GuiStates.RUNNING
                messenger.send(RESET_PLAYER_CAMERA)
                return
            else:
                self.cached_ui.destroy()

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
                enable_mouse()
                self.current_ui = GameEnd(True)
                self.currently_displayed_gui_state = GuiStates.GAME_END_SCREEN_WIN
            case GuiStates.GAME_END_SCREEN_DEFEAT.value:
                enable_mouse()
                self.current_ui = GameEnd(False)
                self.currently_displayed_gui_state = GuiStates.GAME_END_SCREEN_DEFEAT
            case GuiStates.RUNNING.value:
                disable_mouse()
                self.current_ui = Hud()
                self.currently_displayed_gui_state = GuiStates.RUNNING
            case GuiStates.SETTINGS.value:
                self.current_ui = SettingsMenu()
                self.currently_displayed_gui_state = GuiStates.SETTINGS
            case GuiStates.SETTINGS_OVERLAY.value:
                enable_mouse()
                self.current_ui = SettingsMenu(True)
                self.currently_displayed_gui_state = GuiStates.SETTINGS_OVERLAY
            case _:
                self.logger.warning(f"State {target_state} not yet implemented by gui manager. Returning to main menu")
                self.gui_state_machine.state  = GuiStates.MAIN_MENU.value
                self.currently_displayed_gui_state = GuiStates.LIMBO
                self.__update_displayed_gui()
