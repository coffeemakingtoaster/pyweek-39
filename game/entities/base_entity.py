import logging
from direct.showbase import DirectObject
from abc import abstractmethod


class EntityBase(DirectObject.DirectObject):
    def __init__(self, name="BaseEntity"):
        super().__init__()
        self.logger = logging.getLogger()

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def update(self, dt):
        pass
