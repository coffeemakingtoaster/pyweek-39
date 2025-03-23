from game.const.events import ENTER_QUEUE_EVENT, GUI_SETTINGS_EVENT, START_GAME_EVENT
from game.helpers.config import save_config
from panda3d.core import TextNode, TransparencyAttrib

from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DGG

import sys

from game.gui.gui_base import GuiBase

class MainMenu(GuiBase):
    def __init__(self):
        super().__init__("MainMenu")

        TEXT_COLOR = (0.82, 0.34, 0.14, 1) #  NEW: rgb(208, 86, 36) (0.82f, 0.34f, 0.14f, 1f)
        TEXT_ALTERNATE_COLOR = (1.0, 0.84, 0.62, 1) # rgb(255, 214, 159) (1f, 0.84f, 0.62f, 1f)
        
        #buttonImages = (
        #    loader.loadTexture("assets/textures/button_bg.png"),
        #    loader.loadTexture("assets/textures/button_bg.png"),
        #    loader.loadTexture("assets/textures/button_bg.png"),
        #    loader.loadTexture("assets/textures/button_bg.png")
        #)

        self.ui_elements = []
        self.menu_elements = []

        self.load_background_image()

        menu_box = DirectFrame( 
            frameSize=(-0.60, 0.60, -1.00, 0.30),
            pos=(-0.85, 0, 0), 
            frameColor = (1,1,1,1),
        )
        menu_box.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(menu_box)
        
        start_button = DirectButton(text=("Start offline"),
                    parent = menu_box,
                    pos=(0,0,0.05), 
                    scale=0.12, 
                    command=self.start_game, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        start_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(start_button)

        queue_button = DirectButton(text=("Queue online..."),
                    parent = menu_box,
                    pos=(0,0,-0.25), 
                    scale=0.12, 
                    command=self.queue_up, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        queue_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(queue_button)

        settings_button = DirectButton(text=("Settings"),
                    parent = menu_box,
                    pos=(0,0,-0.55), 
                    scale=0.12, 
                    command=self.open_settings, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #text_align = TextNode.ACenter, 
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        settings_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(settings_button)

        quit_button = DirectButton(text=("Quit"),
                    parent = menu_box,
                    pos=(0,0,-0.85), 
                    scale=0.12, 
                    command=self.quit_game, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #text_align = TextNode.ACenter, 
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
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
