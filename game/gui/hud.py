from game.const.events import DEFEAT_EVENT, WIN_EVENT
from game.gui.gui_base import GuiBase
from panda3d.core import TransparencyAttrib

from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DGG

class Hud(GuiBase):
    def __init__(self):
        super().__init__("HUD")

        TEXT_COLOR = (0.82, 0.34, 0.14, 1) #  NEW: rgb(208, 86, 36) (0.82f, 0.34f, 0.14f, 1f)

        menu_box = DirectFrame( 
            frameSize=(-0.60, 0.60, -0.50, 0.30),
            pos=(-200.85, 0, 0), #AUS MEINEM BLICKFELD
            frameColor = (1,1,1,1),
        )
        menu_box.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(menu_box)
        
        queue_indicator = DirectLabel(text=("Ingame"),
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
        queue_indicator.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(queue_indicator)

        win_button = DirectButton(text=("Win"),
                    parent = menu_box,
                    pos=(0,0,-0.25), 
                    scale=0.12, 
                    command=self.__win, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        win_button.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(win_button)

        lose_button = DirectButton(text=("Lose"),
                    parent = menu_box,
                    pos=(0,0,-0.55), 
                    scale=0.12, 
                    command=self.__lose, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1.3,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        lose_button.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(lose_button)

    def __win(self):
        self.logger.warning("Sending win event")
        messenger.send(WIN_EVENT)

    def __lose(self):
        self.logger.warning("Sending lose event")
        messenger.send(DEFEAT_EVENT)
