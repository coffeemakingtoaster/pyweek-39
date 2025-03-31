from game.const.events import ENTER_QUEUE_EVENT, GUI_SETTINGS_EVENT, START_GAME_EVENT
from game.helpers.config import save_config
from panda3d.core import TransparencyAttrib
from game.const.colors import TEXT_PRIMARY_COLOR

from direct.gui.DirectGui import DirectButton, DirectFrame, DGG

import sys

from game.gui.gui_base import GuiBase
from game.helpers.helpers import getFontPath, getTexturePath

class MainMenu(GuiBase):
    def __init__(self):
        super().__init__("MainMenu")

        self.ui_elements = []
        self.menu_elements = []

        buttonImages = loader.loadTexture(getTexturePath("button_bg"))

        menu_box = DirectFrame( 
            frameSize=(-2, 2, -0.2, 0.2),
            pos=(0, 0, -0.85), 
            frameColor = (1,1,1,1),
            frameTexture = getTexturePath("main_menu_board"),
        )
        menu_box.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(menu_box)
        
        start_button = DirectButton(text=("Solo"),
                    parent = menu_box,
                    pos=(-1.25,0,0), 
                    scale=0.12, 
                    command=self.start_game, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_PRIMARY_COLOR),
                    #pad = (1, 0.1),
                    frameTexture = buttonImages,
                    frameSize = (-3, 3, -1, 1),
                    text_scale = 1,
                    text_pos = (0, -0.3),
                    text_font=self.font,
                    frameColor = (1,1,1,1))
        start_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(start_button)

        queue_button = DirectButton(text=("Online"),
                    parent = menu_box,
                    pos=(-(1.25-0.83333),0,0), 
                    scale=0.12, 
                    command=self.queue_up, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_PRIMARY_COLOR),
                    frameTexture = buttonImages,
                    #pad = (1, 0.1),
                    frameSize = (-3, 3, -1, 1),
                    text_scale = 1,
                    text_pos = (0, -0.3),
                    text_font=self.font,
                    frameColor = (1,1,1,1))
        queue_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(queue_button)

        settings_button = DirectButton(text=("Settings"),
                    parent = menu_box,
                    pos=(1.25-0.83333,0,0), 
                    scale=0.12, 
                    command=self.open_settings, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_PRIMARY_COLOR),
                    frameTexture = buttonImages,
                    #text_align = TextNode.ACenter, 
                    #pad = (1, 0.1),
                    frameSize = (-3, 3, -1, 1),
                    text_scale = 1,
                    text_font=self.font,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        settings_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(settings_button)

        quit_button = DirectButton(text=("Quit"),
                    parent = menu_box,
                    pos=(1.25,0,0), 
                    scale=0.12, 
                    command=self.quit_game, 
                    relief=DGG.FLAT, 
                    text_fg=(1,0,0,1),
                    frameTexture = buttonImages,
                    #text_align = TextNode.ACenter, 
                    #pad = (1, 0.1),
                    frameSize = (-3, 3, -1, 1),
                    text_font=self.font,
                    text_scale = 1,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        quit_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(quit_button)

        self.ui_elements += self.menu_elements
        
    def start_game(self):
        self.logger.info("Start button pressed")
        # Use global event messenger to start the game
        messenger.send(START_GAME_EVENT)

    def open_settings(self):
        messenger.send(GUI_SETTINGS_EVENT)

    def queue_up(self):
        messenger.send(ENTER_QUEUE_EVENT)
        
    def quit_game(self):
        save_config('./user_settings.json')
        sys.exit()
