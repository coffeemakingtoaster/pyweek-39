import logging
from direct.showbase import DirectObject
from direct.gui.DirectGui import OnscreenImage
from os.path import join
from panda3d.core import Filename

from direct.showbase.PythonUtil import os

class GuiBase(DirectObject.DirectObject):
    def __init__(self, readable_name="GuiBase"):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.readable_name = readable_name
        self.ui_elements = []
        
    def destroy(self):
        self.logger.info(f"Destroying {self.readable_name}")
        for ui_element in self.ui_elements:
            ui_element.destroy()
            ui_element.removeNode()

    def hide(self):
        self.logger.info(f"Hiding {self.readable_name}")
        for ui_element in self.ui_elements:
            if ui_element is not None:
                ui_element.hide()
        self.ui_elements = []
        
    def load_background_image(self):
        file_path = os.path.join(os.getcwd(), "assets", "images", "main_menu_background.png")
        file_path = Filename.fromOsSpecific(file_path).getFullpath()
        background = OnscreenImage(file_path, pos=(-0.1, 0, 0), scale=(1521 * 0.0012, 1, 859 * 0.0012))
        self.ui_elements.append(background)
