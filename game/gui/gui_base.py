import logging
from direct.showbase import DirectObject

from game.helpers.helpers import getFontPath


class GuiBase(DirectObject.DirectObject):
    def __init__(self, readable_name="GuiBase"):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.readable_name = readable_name
        self.ui_elements = []
        self.font = loader.loadFont(getFontPath("the_last_shuriken"))
       
    def destroy(self):
        self.logger.info(f"Destroying {self.readable_name}")
        self.ignoreAll()
        for ui_element in self.ui_elements:
            ui_element.destroy()
            ui_element.removeNode()

    def hide(self):
        self.logger.info(f"Hiding {self.readable_name}")
        for ui_element in self.ui_elements:
            if ui_element is not None:
                ui_element.hide()
        self.ui_elements = []
