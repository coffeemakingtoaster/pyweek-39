from os.path import join
from direct.gui.DirectGui import DirectFrame, DirectLabel, OnscreenImage
from game.const.player import BASE_HEALTH
from game.gui.gui_base import GuiBase
from panda3d.core import TransparencyAttrib

class HpBar(GuiBase):

    def __init__(self, base_pos, name: str, event: str, scale=0.5):
        super().__init__()
        self.scale = scale
        self.name = name
        self.base = DirectFrame( 
            frameSize=(-0.01, 0.001, -0.01, 0.01),
            pos=base_pos, 
            frameColor = (1,1,1,0),
        )

        self.hp_display_bar = OnscreenImage(
            parent=self.base,
            scale=(self.scale, 1, 0.05), 
            pos=(0, 0, 0), 
            image=join("assets", "icons", "hp_display_bar.png"), 
            color=(255,0,0,1)
        )
        self.hp_display_bar.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.hp_display_bar)

        self.hp_display_background = OnscreenImage(
            parent=self.base,
            scale=(self.scale, 1, 0.05), 
            pos=(0, 0, 0),
            image=join("assets", "icons", "hp_display_backplane.png")
        )
        self.hp_display_background.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.hp_display_background)

        self.hp_bar_text = DirectLabel(
            parent=self.base,
            text="{}: {}".format(self.name, BASE_HEALTH), 
            scale=0.1, 
            pos=(-0.009, 0, -0.025), 
            #text_font=self.font, 
            relief=None, 
            text_fg=(0, 0, 0, 1)
        )
        self.ui_elements.append(self.hp_bar_text)

        self.accept(event, self.update_value)

    def update_value(self, hp_val: int):
        hp_value = max(0, hp_val)
        self.hp_bar_text["text"] =  "{}: {}".format(self.name, hp_value)
        x_scale = (self.scale * min((hp_value/BASE_HEALTH),1))
        self.hp_display_bar.setScale(x_scale,1,0.05)
        self.hp_display_bar.setX(-self.scale + x_scale)

    # Overwrite to make cleanup easier
    def removeNode(self):
        pass
