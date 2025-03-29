from direct.showbase import Audio3DManager
from direct.showbase.ShowBaseGlobal import NodePath

from game.helpers.helpers import getSoundPath

audio3d = None

def add_3d_sound_to_node(sound_name: str, node: NodePath, delay=0.0, loops=True):
    audio3d = Audio3DManager.Audio3DManager(base.sfxManagerList[-1], base.camera)
    sound = audio3d.loadSfx(getSoundPath(sound_name))
    audio3d.attachSoundToObject(sound, node)
    sound.setLoop(loops)
    base.taskMgr.doMethodLater(delay, sound.play, f"start_sound_delayed-{sound_name}", extraArgs=[])


