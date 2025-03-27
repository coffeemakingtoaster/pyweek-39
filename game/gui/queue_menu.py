from direct.gui.DirectGui import DirectLabel
from game.const.events import CANCEL_QUEUE_EVENT, GUI_RETURN_EVENT
from game.gui.gui_base import GuiBase
from panda3d.core import TransparencyAttrib

from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DGG

from game.gui.gui_base import GuiBase

class QueueMenu(GuiBase):
    def __init__(self):
        super().__init__("QueueMenu")

        TEXT_COLOR = (0.82, 0.34, 0.14, 1) #  NEW: rgb(208, 86, 36) (0.82f, 0.34f, 0.14f, 1f)
        TEXT_ALTERNATE_COLOR = (1.0, 0.84, 0.62, 1) # rgb(255, 214, 159) (1f, 0.84f, 0.62f, 1f)

        self.ui_elements = []
        self.menu_elements = []

        buttonImages = loader.loadTexture("assets/textures/button_bg.png"),
        font = loader.loadFont("assets/fonts/the_last_shuriken.ttf")

        menu_box = DirectFrame( 
            frameSize=(-1.75, 1.75, -0.2, 0.2),
            pos=(0, 0, -0.85), 
            frameColor = (1,1,1,1),
            frameTexture = "assets/textures/main_menu_board.png"
        )
        menu_box.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(menu_box)
        
        queue_indicator = DirectLabel(text=("In Queue..."),
                    parent = menu_box,
                    pos=(-1,0,0), 
                    scale=0.12, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_ALTERNATE_COLOR),
                    #pad = (1, 0.1),
                    frameSize = (-4, 4, -1, 1),
                    text_font=font,
                    text_scale = 1,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,0))
        queue_indicator.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(queue_indicator)

        cancel_button = DirectButton(text=("Cancel"),
                    parent = menu_box,
                    pos=(1,0,0), 
                    scale=0.12, 
                    command=self.cancel_queue, 
                    frameTexture = buttonImages,
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_COLOR),
                    #pad = (1, 0.1),
                    text_font=font,
                    frameSize = (-4, 4, -1, 1),
                    text_scale = 1,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,1))
        cancel_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(cancel_button)

        self.ui_elements += self.menu_elements
        
    def cancel_queue(self):
        self.logger.info("Queue cancelled")
        messenger.send(GUI_RETURN_EVENT)

    def destroy(self):
        messenger.send(CANCEL_QUEUE_EVENT)
        return super().destroy()
