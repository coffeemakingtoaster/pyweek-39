from game.const.events import GUI_RETURN_EVENT
from game.gui.gui_base import GuiBase

from panda3d.core import TransparencyAttrib

from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DGG

class GameEnd(GuiBase):
    def __init__(self, is_victory):
        super().__init__("GameEnd")
        self.is_victory = is_victory

        self.load_background_image()

        TEXT_COLOR = (0.82, 0.34, 0.14, 1) #  NEW: rgb(208, 86, 36) (0.82f, 0.34f, 0.14f, 1f)

        menu_box = DirectFrame( 
            frameSize=(-0.60, 0.60, -0.50, 0.30),
            pos=(-0.85, 0, 0), 
            frameColor = (1,1,1,1),
        )
        menu_box.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(menu_box)

        state_label = "Victory!"

        if not self.is_victory:
            state_label = "Defeat"
        
        state_indicator = DirectLabel(text=(state_label),
                    parent = menu_box,
                    pos=(0,0,0.05), 
                    scale=0.12, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        state_indicator.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(state_indicator)

        main_menu_button = DirectButton(text=("Main Menu"),
                    parent = menu_box,
                    pos=(0,0,-0.25), 
                    scale=0.12, 
                    command=self.__return_to_main_menu, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        main_menu_button.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(main_menu_button)

    def __return_to_main_menu(self):
        messenger.send(GUI_RETURN_EVENT)
