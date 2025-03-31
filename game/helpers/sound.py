import logging

from direct.showbase.ShowBase import taskMgr
from direct.task.Task import Task

from game.helpers.helpers import getMusicPath, getSoundPath


class SoundHelper:
    def __init__(self) -> None:
        self.logger = logging.getLogger()
        self.main_menu_music =  base.loader.loadMusic(getMusicPath("main_menu"))
        self.combat_music_start = base.loader.loadMusic(getMusicPath("music_mid"))
        self.combat_music_loop = base.loader.loadMusic(getMusicPath("music_start"))
        self.victorySound = base.loader.loadSfx(getSoundPath("vicroy"))

    def start_main_menu_music(self):
        self.combat_music_loop.stop()
        self.combat_music_start.stop()
        taskMgr.remove("startLoopMusicTask")
        self.main_menu_music.setLoop(True)
        self.main_menu_music.play()

    def __start_combat_loop(self, _):
        self.combat_music_loop.setLoop(True)
        self.combat_music_loop.play()
        return Task.done

    def start_combat_music(self):
        self.combat_music_loop.stop()
        self.main_menu_music.stop()
        taskMgr.remove("startLoopMusicTask")
        self.combat_music_start.play()
        taskMgr.doMethodLater(70.171, self.__start_combat_loop,"startLoopMusicTask")

    def play_victory_sound(self):
        self.victorySound.play()

