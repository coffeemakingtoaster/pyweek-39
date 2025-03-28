import logging
import os
from panda3d.core import WindowProperties
import json

from game.const.settings import GAME_SETTINGS
from game.utils.name_generator import generate_name

PLAYER_NAME_ENV_VAR = "PLAYER_NAME"
GOOD_SHADOW_QUALITY_ENV_VAR = "PLAYER_NAME"

LOGGER = logging.getLogger(__name__)

def load_config(path='./user_settings.json'):

    config = {}
    
    if os.path.isfile(path):
        with open(path) as config_file:
            config = json.load(config_file)

    set_sfx_volume(config.get("sfx_volume", 0.5)) 
       
    set_music_volume(config.get("music_volume", 0.5)) 

    set_fullscreen_value(config.get("fullscreen", False))

    set_shadow_map_quality(config.get("good_shadows", False))
      
    base.setFrameRateMeter(config.get("show_fps", False))

    os.environ[PLAYER_NAME_ENV_VAR] = config.get("user_name", generate_name())
        
def setup_windowed():
    wp = WindowProperties(base.win.getProperties()) 
    wp.set_fullscreen(False)
    wp.set_size(GAME_SETTINGS.DEFAULT_WINDOW_WIDTH, GAME_SETTINGS.DEFAULT_WINDOW_HEIGHT)
    wp.set_origin(-2, -2)
    base.win.requestProperties(wp) 
            
def save_config(path='./user_settings.json'):
    config = {
            "sfx_volume": float(get_sfx_volume()), 
            "music_volume": float(get_music_volume()), 
            "fullscreen": get_fullscreen_value(), 
            "show_fps": get_fps_counter_enabled(), 
            "user_name" : os.getenv(PLAYER_NAME_ENV_VAR, generate_name()),
            "good_shadows": should_use_good_shadows(),
    }
    
    with open(path, "w+") as config_file:
        config_file.write(json.dumps(config))

def get_sfx_volume():
    # This assumes that all sfx managers have the same volume
    return base.sfxManagerList[0].getVolume() 
    
def set_sfx_volume(value):
    for manager in base.sfxManagerList:
        manager.setVolume(value)
        
def get_music_volume():
    return base.musicManager.getVolume()
            
def set_music_volume(value):
    LOGGER.info(f"settings {value}")
    base.musicManager.setVolume(value)
    
def get_fullscreen_value():
    wp = WindowProperties(base.win.getProperties())  
    return wp.get_fullscreen()
    
def set_fullscreen_value(fullscreen):
    wp = WindowProperties(base.win.getProperties())  
    is_currently_in_fullscreen = wp.get_fullscreen()
    if fullscreen and not is_currently_in_fullscreen:
        wp.set_fullscreen(True)
        wp.set_size(1920, 1080)
        wp.clearCursorHidden()
        base.win.requestProperties(wp)
    elif not fullscreen and is_currently_in_fullscreen:
       setup_windowed() 

def get_fps_counter_enabled():
    return base.frameRateMeter != None

def set_fps_counter_enabled(val):
    base.setFrameRateMeter(val)

def get_player_name():
    name = os.getenv(PLAYER_NAME_ENV_VAR, generate_name())
    LOGGER.info(f"Saved name was: {name}")
    return name

def set_shadow_map_quality(val: bool):
    os.environ[GOOD_SHADOW_QUALITY_ENV_VAR] = "true" if val else "false"

def should_use_good_shadows() -> bool:
    return os.getenv(GOOD_SHADOW_QUALITY_ENV_VAR, "false") == "true"

def set_player_name(val: str):
    LOGGER.info(f"New name set: {val}")
    os.environ[PLAYER_NAME_ENV_VAR] = val
