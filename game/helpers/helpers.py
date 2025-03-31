
from panda3d.core import Filename

from direct.showbase.PythonUtil import os

from panda3d.core import Vec3


def getFontPath(name):
    file_path = os.path.join(os.getcwd(), "assets", "fonts", name+".ttf")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getModelPath(name):
    file_path = os.path.join(os.getcwd(), "assets", "models", name+".egg")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getImagePath(name):
    file_path = os.path.join(os.getcwd(), "assets", "images", name+".png")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getTexturePath(name):
    file_path = os.path.join(os.getcwd(), "assets", "textures", name+".png")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getParticlePath(name):
    file_path = os.path.join(os.getcwd(), "assets", "particles", name+".ptf")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getMusicPath(name):
    file_path = os.path.join(os.getcwd(), "assets", "music", name+".mp3")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getSoundPath(name):
    file_path = os.path.join(os.getcwd(), "assets", "sfx", name+".mp3")
    return Filename.fromOsSpecific(file_path).getFullpath()

def normal_to_hpr(normal):
    # Normalize the normal vector
    normal = normal.normalized()

    # Compute heading (yaw) and pitch (tilt)
    heading = -normal.signedAngleDeg(Vec3(1, 0, 0), Vec3(0, 0, 1))  # Angle compared to X-axis
    pitch = -normal.signedAngleDeg(Vec3(0, 0, 1), Vec3(1, 0, 0))  # Angle compared to Z-axis

    # Construct HPR as a Vec3
    return Vec3(heading, pitch, 0)  # Roll is usually 0 unless needed
