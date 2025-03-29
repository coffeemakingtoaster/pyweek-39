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
        
        backdrop = DirectFrame(
            frameSize=(-1, 1, -0.6, 0.6),
            pos=(0, 0, 0.3), 
            frameColor = (1,1,1,1),
            frameTexture = "assets/textures/end_game_backdrop.png",
        )
        backdrop.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(backdrop)


        state_image = loader.loadTexture("assets/textures/victory.png")
        text = "victory"

        if not self.is_victory:
            state_image = loader.loadTexture("assets/textures/defeat.png")
            text = "defeat"

        state_indicator = DirectFrame(
            frameSize=(-0.8, 0.8, -0.8, 0.8),
            pos=(0, 0, 0.3), 
            frameColor = (1,1,1,1),
            frameTexture = state_image,
        )
        state_indicator.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(state_indicator)
        
        state_text = DirectLabel(
            scale=0.07,
            pos=(0,0,-0.3),
            text_fg=(TEXT_PRIMARY_COLOR) if self.is_victory else (1,0,0,1),
            text_font=font,
            text=text,
            frameColor = (1,1,1,0)
        )
        state_text.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(state_text)

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

