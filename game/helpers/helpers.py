
from os.path import join
from panda3d.core import Filename

from direct.showbase.PythonUtil import os

def getModelPath(name):
    file_path = os.path.join(os.getcwd(), "assets", "models", name+".egg")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getImagePath(name):
    file_path = os.path.join(os.getcwd(), "assets", "images", name+".png")
    return Filename.fromOsSpecific(file_path).getFullpath()

def getParticlePath(name):
    file_path = os.path.join(os.getcwd(), "assets", "particles", name+".ptf")
    return Filename.fromOsSpecific(file_path).getFullpath()