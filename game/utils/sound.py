from direct.showbase import Audio3DManager
from direct.showbase.ShowBaseGlobal import NodePath

from game.helpers.helpers import getSoundPath

audio3d = None

def add_3d_sound_to_node(sound_name: str, node: NodePath):
    audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[-1], base.camera)
    sound = audio3d.loadSfx(getSoundPath(sound_name))
    audio3d.attachSoundToObject(sound, node)
    sound.setLoop(True)
    sound.play()
