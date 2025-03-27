from game.const.events import GUI_UPDATE_ANTI_HP, GUI_UPDATE_LATENCY, GUI_UPDATE_PLAYER_HP
from game.gui.gui_base import GuiBase
from panda3d.core import TransparencyAttrib

from direct.gui.DirectGui import DirectButton, DirectLabel, DirectFrame, DGG, OnscreenImage

from game.gui.hp_bar import HpBar

class Hud(GuiBase):
    def __init__(self):
        super().__init__("HUD")

        TEXT_COLOR = (0.82, 0.34, 0.14, 1) #  NEW: rgb(208, 86, 36) (0.82f, 0.34f, 0.14f, 1f)
        TEXT_ALTERNATE_COLOR = (1.0, 0.84, 0.62, 1) # rgb(255, 214, 159) (1f, 0.84f, 0.62f, 1f)

        buttonImages = loader.loadTexture("assets/textures/button_bg.png"),
        font = loader.loadFont("assets/fonts/the_last_shuriken.ttf")

        latency_box = DirectFrame( 
            frameSize=(-0.3, 0.3, -0.05, 0.05),
            pos=(1.3, 0, -0.85), 
            frameColor = (1,1,1,1),
            frameTexture = "assets/textures/main_menu_board.png"
        )
        latency_box.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(latency_box)
 

        self.latency_indicator = DirectLabel(text=("Ping: N/A"),
                    parent=latency_box,
                    pos=(0,0,0.015), 
                    scale=0.12, 
                    relief=DGG.FLAT, 
                    text_fg=(TEXT_ALTERNATE_COLOR),
                    #pad = (1, 0.1),
                    text_font = font,
                    frameSize = (-2, 2, -0.5, 0.2),
                    text_scale = 0.5,
                    text_pos = (0, -0.3),
                    frameColor = (1,1,1,0))
        self.latency_indicator.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.latency_indicator)

        self.player_hp_bar = HpBar(
            base_pos=(-1.3,0,-0.85),
            name="Player",
            event=GUI_UPDATE_PLAYER_HP,
        )
        self.ui_elements.append(self.player_hp_bar)

        self.anti_hp_bar = HpBar(
            base_pos=(0,0,0.8),
            name="Enemy",
            event=GUI_UPDATE_ANTI_HP,
            scale=1,
        )
        self.ui_elements.append(self.anti_hp_bar)

        self.accept(GUI_UPDATE_LATENCY, self.__update_latency)

    def __update_latency(self, time_ms: float):
        try:
            self.latency_indicator.setText(f"Ping: ~{time_ms:6.2f}ms")
        except Exception as e:
            self.logger.error(f"Error occured updating ping display: {e}")
