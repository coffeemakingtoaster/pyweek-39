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
