from game.const.events import GUI_RETURN_EVENT
from game.gui.gui_base import GuiBase

from game.const.colors import TEXT_PRIMARY_COLOR, TEXT_SECONDARY_COLOR

from panda3d.core import TransparencyAttrib

from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DGG

class GameEnd(GuiBase):
    def __init__(self, is_victory):
        super().__init__("GameEnd")
        self.is_victory = is_victory

        buttonImages = loader.loadTexture("assets/textures/button_bg.png"),
        font = loader.loadFont("assets/fonts/the_last_shuriken.ttf")

        state_label = "Victory!"

        if not self.is_victory:
            state_label = "Defeat"
        
        state_indicator = DirectLabel(text=(state_label),
                    pos=(0,0,0.05), 
                    scale=0.12, 
                    relief=DGG.FLAT, 
                    text_fg=(1,1,1,1),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.5,
                    text_font=font,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,0))
        state_indicator.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(state_indicator)

        main_menu_button = DirectButton(text=("Main Menu"),
                    pos=(0,0,-0.85), 
                    scale=0.12, 
                    command=self.__return_to_main_menu, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_PRIMARY_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    frameTexture = buttonImages,
                    text_font=font,
                    text_scale = 1,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        main_menu_button.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(main_menu_button)

    def __return_to_main_menu(self):
        messenger.send(GUI_RETURN_EVENT)
