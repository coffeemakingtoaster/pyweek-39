import logging
import math
from direct.task.Task import Task, messenger
from panda3d.core import *

from direct.showbase.ShowBase import ShowBase
from pandac.PandaModules import TransparencyAttrib
import copy

from game.gui.const import GuiStates, StateTransitionEvents

from game.const.events import CANCEL_QUEUE_EVENT, DEFEAT_EVENT, ENTER_QUEUE_EVENT, GUI_FORCE_MAIN_MENU_EVENT, GUI_MAIN_MENU_EVENT, GUI_PLAY_EVENT, GUI_QUEUE_EVENT, GUI_RETURN_EVENT, GUI_SETTINGS_EVENT, GUI_UPDATE_ANTI_PLAYER_NAME, NETWORK_SEND_PRIORITY_EVENT, RESET_PLAYER_CAMERA, START_GAME_EVENT, UPDATE_SHADOW_SETTINGS, WIN_EVENT
from game.const.networking import TIME_BETWEEN_PACKAGES_IN_S
from game.const.player import MAIN_MENU_CAMERA_HEIGHT, MAIN_MENU_CAMERA_ROTATION_RADIUS, MAIN_MENU_CAMERA_ROTATION_SPEED, MAIN_MENU_PLAYER_POSITION
from game.entities.anti_player import AntiPlayer
from game.entities.bot import Bot
from game.entities.player import Player
from game.helpers.config import get_player_name, load_config, is_attacker_authority
from game.helpers.helpers import *
from game.gui.gui_manager import GuiManager
import uuid

from game.networking.queue import check_queue_status, join_queue, leave_queue
from game.networking.websocket import MatchWS
from game.utils.input import disable_mouse, enable_mouse
from game.utils.name_generator import generate_name
from game.utils.sound import add_3d_sound_to_node
from shared.const.queue_status import QueueStatus
from pandac.PandaModules import WindowProperties

from shared.types.player_info import PlayerInfo
from shared.types.status_message import StatusMessages
from shared.utils.validation import parse_game_status, parse_player_info

from direct.particles.ParticleEffect import ParticleEffect
from direct.actor.Actor import Actor

class MainGame(ShowBase):
    def __init__(self) -> None:
        super().__init__()
        self.logger = logging.getLogger(__name__)
        properties = WindowProperties()
        properties.setSize(1280, 720)
        self.win.requestProperties(properties)
        self.game_task = base.taskMgr.add(self.__main_loop, "gameLoop")
        self.queue_task = None
        self.ws_handle_task = None
        self.logger.debug("Window setup done...")
        base.camLens.setNear(0.1)
        base.camLens.setFov(120)
        
        base.cTrav = CollisionTraverser()
        #base.cTrav.showCollisions(render)
        base.enableParticles()
        
        loadPrcFileData("", "interpolate-frames 1")
        load_config()
        
        self.waterfallCount = 0
        self.mouse_locked = False

        self.player: None | Player = None
        self.anti_player: None | AntiPlayer | Bot = None

        # Setup gui handling
        self.gui_manager = GuiManager()
        self.accept("escape", self.gui_manager.handle_custom, [StateTransitionEvents.ESC])
        self.accept(GUI_RETURN_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.RETURN])
        self.accept(GUI_SETTINGS_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.SETTINGS])
        self.accept(GUI_PLAY_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.PLAY])
        self.accept(GUI_MAIN_MENU_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.MAIN_MENU])
        self.accept(GUI_QUEUE_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.QUEUE])
        self.accept(GUI_FORCE_MAIN_MENU_EVENT, self.__force_main_menu)
        self.logger.debug("Gui handling and state machine initialized...")

        # General event handling
        self.accept(START_GAME_EVENT, self.__start_game)
        self.accept(ENTER_QUEUE_EVENT, self.__enter_queue)
        self.accept(CANCEL_QUEUE_EVENT, self.__cancel_queue)
        self.accept(WIN_EVENT, self.__finish_game, [True])
        self.accept(DEFEAT_EVENT, self.__finish_game, [False])
        self.accept(UPDATE_SHADOW_SETTINGS, self.__update_shadow_settings)
        self.accept(RESET_PLAYER_CAMERA, self.__position_player_camera)

        self.accept(NETWORK_SEND_PRIORITY_EVENT, self.__priority_ws_send)

        self.player_id: str = str(uuid.uuid4())
        self.match_id: None | str = None

        self.is_online: bool = False
        self.ws: None | MatchWS = None

        self.time_since_last_package: int = 1_000_000
        self.camera_angle = 0

        self.slight = None

        self.buildMap()

    def __force_main_menu(self):
        if self.gui_manager.is_ingame():
            self.__finish_game(False, fast_exit=True)
        self.gui_manager.handle_custom(StateTransitionEvents.FORCE_MAIN_MENU)

    def buildMap(self):
        """ Build map and place dummy player for main menu """
        
        dlight = DirectionalLight('my dlight')
        dlight.color = (0.6,0.6,1.3,1)
        dlight.setDirection(Vec3(0,1,-0.5))
        dlnp = render.attachNewNode(dlight)

        # @Heuserus do we need this? This is the loc that was causing the particle issues 
        render.setShaderAuto()
        
        #render.setLight(ambientnp) 
        render.setLight(dlnp)
        
        # Create a spotlight
        self.slight = Spotlight('slight')
        self.slight.setColor((2, 2, 3, 1))  # Set light color

        self.__update_shadow_settings()
        
        slnp = self.render.attachNewNode(self.slight)
         # Position and rotate the spotlight
        slnp.setPos(0, 50, 50)  # Position the spotlight
        slnp.setHpr(0, -135, 0)  # Make the spotlight point at the model
        self.render.setLight(slnp)
       
        #cubeMap = loader.loadCubeMap(getImagePath("skybox"))
        self.spaceSkyBox = loader.loadModel(getModelPath("skysphere"))
        self.spaceSkyBox.setScale(200)
        self.spaceSkyBox.setZ(-40)
        self.spaceSkyBox.setH(90)
        self.spaceSkyBox.setBin('background', 0)
        self.spaceSkyBox.setDepthWrite(0)
        self.spaceSkyBox.setTwoSided(True)
        #self.spaceSkyBox.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldCubeMap)
        self.spaceSkyBox.reparentTo(render)
        self.spaceSkyBox.setLightOff()
        #self.spaceSkyBox.setTexture(cubeMap, 1)
        
        self.map = self.loader.loadModel("assets/models/map.egg")
        
        self.map.reparentTo(self.render)
        
        self.map.setZ(-2)
        self.map.setShaderAuto()
        
        self.treeTops = self.loader.loadModel(getModelPath("treeTops"))
        self.treeTops.reparentTo(self.render)
        self.treeTops.setZ(-2)
        self.treeTops.setShaderOff()
        self.treeTops.setLightOff()
        
        self.river = self.loader.loadModel(getModelPath("river"))
        self.river.reparentTo(self.render)
        self.river.setZ(-2)
        
        texture = loader.loadTexture(getImagePath("pxArt (8)"))

        # Try to find an existing texture stage
        self.riverTextureStage = self.river.findTextureStage("dust.png")

        self.river.setTexture(self.riverTextureStage, texture, 1)  # Use priority to force replace
        taskMgr.add(self.shiftRiverTextureTask,"shift river Task")
        
        self.waterfall = loader.loadModel(getModelPath("waterfall"))
        self.waterfall2 = loader.loadModel(getModelPath("waterfall2"))
        
        self.waterFallMaker(self.waterfall)
        self.waterFallMaker(self.waterfall2)
        
        self.particle_owner = render.attachNewNode("particle_owner")
        self.particle_owner.setShaderOff()
        
        
        p = ParticleEffect()
        p.loadConfig(getParticlePath("leaves"))
        p.start(parent = self.particle_owner, renderParent = self.particle_owner)
        p.setPos(12,15,0)
        
        
        for i in range(15):
            p = ParticleEffect()
            p.loadConfig(getParticlePath("spray"))
            p.start(parent = self.particle_owner, renderParent = self.particle_owner)
            p.setPos(-5.5+i*0.8,-8,0.4)
            
            p.setDepthWrite(False)
            p.setBin("fixed", 0)

        self.__add_and_focus_main_menu_player()

        '''
        color = (0.5, 0.5, 0.5)
        linfog = Fog("A linear-mode Fog node")
        linfog.setColor(*color)
        linfog.setLinearRange(1000, 1000)
        #linfog.setExpDensity(0.1)            
        linfog.setLinearFallback(20, 50, 80)
        fogNode = render.attachNewNode(linfog) 
        fogNode.setPos(0,0,-5)
        fogNode.lookAt(0,0,-10)
        render.setFog(linfog) 
        '''

    def waterFallMaker(self,waterfall):
        waterfall.reparentTo(render)
        waterfall.setTransparency(TransparencyAttrib.MAlpha)
        waterfall.setPos(0,0,-2)
        
        self.waterfallCount +=1
        texture2 = loader.loadTexture(getImagePath("transWater2"))
        texture = loader.loadTexture(getImagePath("transWater"))
        transTexture = loader.loadTexture(getImagePath("blue"))
        
        waterfall.setTexture(transTexture)
        textureStage0 = waterfall.findTextureStage("pxArt (8).png")
        textureStage0.setMode(TextureStage.MBlend)
        
        waterfall.setTexture(textureStage0,texture,1)
        waterfall.setTexScale(textureStage0, 2, 2)
        
        textureStage1 = copy.copy(textureStage0)
        textureStage1.setMode(TextureStage.MAdd)
        
        waterfall.setTexture(textureStage1,texture,1)
        waterfall.setTexScale(textureStage1, 1, 1)

        add_3d_sound_to_node("waterfall", self.waterfall, delay=1)

        taskMgr.add(self.shiftWaterfallTextureTask,("shift Task")+str(self.waterfallCount),extraArgs=[waterfall,textureStage0,textureStage1],appendTask = True)
    
    def __update_shadow_settings(self, task=None):
        if self.slight is None:
            return
        if is_attacker_authority():
            self.slight.setShadowCaster(True, 2048, 2048) 
        else:
            self.slight.setShadowCaster(True, 512, 512) 

    def __add_and_focus_main_menu_player(self):
        self.logger.info("Place camera and player")
        if self.player is not None:
            self.player.destroy()
        self.player = Actor(getModelPath("idle_actor"),{"idle": getModelPath("idle_actor-Idle")})
        self.player.setPos(MAIN_MENU_PLAYER_POSITION)
        self.player.loop("idle")
        
        self.player.reparentTo(render)
        self.camera.reparentTo(render)
        self.camera_angle = 0
        
    def shiftWaterfallTextureTask(self,waterfall,textureStage0,textureStage1,task):
        waterfall.setTexOffset(textureStage0, 0, (task.time*2) % 1.0 )
        waterfall.setTexOffset(textureStage1, 0, (task.time*0.4) % 1.0 )
        return Task.cont
    
    def shiftRiverTextureTask(self,task):
        self.river.setTexOffset(self.riverTextureStage,0,(task.time*-0.2) % 1.0)
        return Task.cont
    
    def __finish_game(self, is_victory, fast_exit=None):
        enable_mouse()
        self.logger.info(f"Received game finish where victory: {is_victory}")
        self.gui_manager.set_online(False)
       
        if self.ws is not None:
            self.ws.close(reason="Finished")
        if self.ws_handle_task is not None:
            self.ws_handle_task.cancel()
            self.ws_handle_task = None
        self.is_online = False
        self.match_id = None
        if self.player is not None:
            self.player.destroy()
        self.__add_and_focus_main_menu_player()
        if self.anti_player is not None:
            self.anti_player.destroy()
        if fast_exit:
            return
        if is_victory:
            victorySound = base.loader.loadSfx(getSoundPath("vicroy"))
            self.background_music.stop()
            victorySound.play()
            self.gui_manager.handle_custom(StateTransitionEvents.WIN)
        else:
            self.gui_manager.handle_custom(StateTransitionEvents.DEFEAT)

    def __enter_queue(self):
        messenger.send(GUI_QUEUE_EVENT)
        self.queue_task = base.taskMgr.doMethodLater(1, self.__check_queue_status, "queue_check")
        base.taskMgr.add(join_queue, 'join_queue_task', extraArgs=[self.player_id])

    def __cancel_queue(self):
        if self.match_id is None:
            self.logger.info("Exiting queue and stopping background check.")
            leave_queue(self.player_id)
        if self.queue_task is not None:
            self.queue_task.remove()
        self.queue_task = None

    def __check_queue_status(self, task):
        success, status, match_id = check_queue_status(self.player_id)
        if not success:
            return Task.again
        if status != QueueStatus.MATCHED.value:
            return Task.again
        if len(match_id) > 0:
            self.match_id = match_id
            self.logger.info("Game found! Joining game...")
            self.__start_game(match_id, False)
            return Task.done

    def startLoopMusic(self,task):
        self.background_music = base.loader.loadMusic(getMusicPath("music_mid"))
        self.background_music.setLoop(True)
        self.background_music.play()
    
    def __start_game(self, match_id="", is_offline=True):
        
        self.background_music = base.loader.loadMusic(getMusicPath("music_start"))
        self.background_music.play()
        taskMgr.doMethodLater(70.171,self.startLoopMusic,"startLoopMusicTask")
        
        self.is_online = not is_offline
        self.gui_manager.set_online(not is_offline)

        disable_mouse()
        
        if self.player is not None:
            self.player.removeNode()

        self.player = Player(self.camera,self.win, self.is_online)
        self.__position_player_camera()
               
        if is_offline:
            self.logger.info("Starting game in offline mode...")
            self.match_id = None
            self.anti_player = Bot(self.win)
            self.player.set_player(StatusMessages.PLAYER_1)
            self.anti_player.set_player(StatusMessages.PLAYER_2)
            self.player.start_match_timer()
            self.anti_player.start_match_timer()
        else:
            self.logger.info("Starting online game...")
            self.anti_player = AntiPlayer(self.win, self.is_online)
            if self.queue_task is not None:
                self.queue_task.remove()
            self.queue_task = None
            self.ws = MatchWS(
                match_id=match_id, 
                player_id=self.player_id, 
                player_name=get_player_name(),
                recv_callback=self.__process_ws_message)
        messenger.send(GUI_PLAY_EVENT)
        if is_offline:
            messenger.send(GUI_UPDATE_ANTI_PLAYER_NAME, [generate_name()])

    def __position_player_camera(self, update_pointer=True):
        if type(self.player) is Player and self.player is not None:
            self.camera.setHpr(0,0,0)
            self.camera.reparentTo(self.player.head)
            self.camera.setPos(0,0.1,0.4)
            self.player.head.setP(0)
            if update_pointer:
                self.win.movePointer(0, self.win.getXSize() // 2, self.win.getYSize() // 2)
                  
    def __process_ws_message(self, msg):
        if self.anti_player is not None:
            # Player info package
            if (player_info := parse_player_info(msg)) is not None:
                self.player.update_state(player_info)
                self.anti_player.set_state(player_info)
                return
            if (game_status := parse_game_status(msg)) is not None:
                match game_status.message:
                    case StatusMessages.DEFEAT.value:
                        messenger.send(DEFEAT_EVENT)
                    case StatusMessages.VICTORY.value:
                        messenger.send(WIN_EVENT)
                    case StatusMessages.PLAYER_NAME.value:
                        self.logger.debug(f"enemy named {game_status.detail}")
                        self.anti_player.set_name(game_status.detail)
                        messenger.send(GUI_UPDATE_ANTI_PLAYER_NAME, [game_status.detail])
                    case StatusMessages.PLAYER_1.value:
                        self.player.set_player(StatusMessages.PLAYER_1)
                        self.anti_player.set_player(StatusMessages.PLAYER_2)
                    case StatusMessages.PLAYER_2.value:
                        self.player.set_player(StatusMessages.PLAYER_2)
                        self.anti_player.set_player(StatusMessages.PLAYER_1)
                    case StatusMessages.LOBBY_STARTING.value:
                        self.player.start_match_timer()
                        self.anti_player.start_match_timer()
                    case _:
                        self.logger.warning(f"Status message contained status {game_status.message} which is not implemented")
                return
            self.logger.warning(f"Message was thrown out: {msg}")

    def __priority_ws_send(self, packet: PlayerInfo):
        if not self.is_online:
            return
        if self.ws is not None:
            packet.health = self.player.health
            packet.enemy_health = self.anti_player.health
            self.ws.send_game_data(packet)

    def __main_loop_online(self, dt):
        self.time_since_last_package += dt
        if self.time_since_last_package > TIME_BETWEEN_PACKAGES_IN_S:
            packet = self.player.get_current_state()
            packet.enemy_health = self.anti_player.health
            self.ws.send_game_data(packet)
            self.time_since_last_package = 0

    def rotate_camera(self, dt):
        self.camera_angle += MAIN_MENU_CAMERA_ROTATION_SPEED * dt

        # Compute new position
        x = MAIN_MENU_PLAYER_POSITION.x +  MAIN_MENU_CAMERA_ROTATION_RADIUS * math.cos(self.camera_angle)
        y = MAIN_MENU_PLAYER_POSITION.y + MAIN_MENU_CAMERA_ROTATION_RADIUS * math.sin(self.camera_angle)

        # Set camera position and look at the center
        self.camera.setPos(x, y, MAIN_MENU_CAMERA_HEIGHT)
        self.camera.lookAt(MAIN_MENU_PLAYER_POSITION)

    def __main_loop(self, task):
        dt = self.clock.dt

        if not self.gui_manager.is_ingame():
            self.rotate_camera(dt)
            return Task.cont

        # Fix issue within settings overlay and camera pos
        if self.gui_manager.gui_state_machine.getCurrentOrNextState() == GuiStates.SETTINGS_OVERLAY.value:
            self.__position_player_camera(update_pointer=False)

        if type(self.player) is not Actor:
            self.player.update(dt)

        if self.is_online:
            self.anti_player.update(dt)
            self.__main_loop_online(dt)
            return Task.cont
        else:
            self.anti_player.update(dt, self.player)
        return Task.cont

