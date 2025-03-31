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

        self.font = loader.loadFont("assets/fonts/the_last_shuriken.ttf")

        self.base = DirectFrame( 
            frameSize=(-0.01, 0.001, -0.01, 0.01),
            pos=base_pos, 
            frameColor = (1,1,1,0),
        )
        
        self.hp_display_background = OnscreenImage(
            parent=self.base,
            scale=(self.scale, 1, 0.05), 
            pos=(0, 0, 0),
            image=join("assets", "icons", "hp_display_backplane2.png")
        )
        self.hp_display_background.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.hp_display_background)
       
        self.hp_display_bar = OnscreenImage(
            parent=self.base,
            scale=(self.scale * 0.99, 1, 0.042), 
            pos=(0, 0, 0), 
            image=join("assets", "icons", "hp_display_bar2.png"), 
            color=(255,0,0,1)
        )
        self.hp_display_bar.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(self.hp_display_bar)
        
        self.hp_bar_text = None
        
        self.__create_name_label()
        
        self.accept(event, self.update_value)
        #self.accept(event, self.update_name)
        
    def __create_name_label(self):
        if self.hp_bar_text is not None:
            if not self.hp_bar_text.is_empty():
                # cleanup will occurr on destroy
                self.hp_bar_text.hide()
        self.hp_bar_text = DirectLabel(
            parent=self.base,
            text="{}".format(self.name), 
            text_font=self.font,
            text_scale=(self.scale/4)*3,
            scale=0.1, 
            # 40 -> magic number :)
            pos=(-0.009, 0, -self.scale/40), 
            relief=None, 
            text_fg=(0, 0, 0, 0.9)
        )
        self.ui_elements.append(self.hp_bar_text)

    def update_value(self, hp_val: int, depth=0):
        if depth == 2:
            self.logger.warning("Could not update HP count due to internal gui errors")
            return
        try:
            hp_value = max(0, hp_val)
            x_scale = (self.scale * min((hp_value/BASE_HEALTH),1))
            self.hp_display_bar.setScale(x_scale*0.92,1,0.042)
            #self.hp_display_bar.setX(-self.scale + (x_scale * 0.92))
        except:
            # Try again -> there is a weird _optionInfo bug in direct gui that we cannot fix
            self.update_value(hp_val,depth+1)

    def update_name(self, new_name: str, depth=0):
        if depth == 3:
            self.logger.warning("Could not set name for enemy name: Replacing label instead")
            self.__create_name_label()
            return
        try:
            self.hp_bar_text["text"] =  "{}".format(new_name)
        except:
            # Try again -> there is a weird _optionInfo bug in direct gui that we cannot fix
            self.update_name(new_name,depth=depth+1)

    # Overwrite to make cleanup easier
    def removeNode(self):
        pass

