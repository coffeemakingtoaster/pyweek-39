import logging
from direct.task.Task import Task, messenger
from panda3d.core import *

from direct.showbase.ShowBase import ShowBase
from pandac.PandaModules import TransparencyAttrib



from game.const.events import CANCEL_QUEUE_EVENT, DEFEAT_EVENT, ENTER_QUEUE_EVENT, GUI_MAIN_MENU_EVENT, GUI_PLAY_EVENT, GUI_QUEUE_EVENT, GUI_RETURN_EVENT, GUI_SETTINGS_EVENT, NETWORK_SEND_PRIORITY_EVENT, START_GAME_EVENT, WIN_EVENT
from game.const.networking import TIME_BETWEEN_PACKAGES_IN_S
from game.entities.anti_player import AntiPlayer
from game.entities.player import Player
from game.helpers.helpers import *
from game.gui.gui_manager import GuiManager, GuiStates, StateTransitionEvents
import uuid

from game.networking.queue import check_queue_status, join_queue, leave_queue
from game.networking.websocket import MatchWS
from game.utils.name_generator import generate_name
from shared.const.queue_status import QueueStatus
from pandac.PandaModules import WindowProperties

from shared.types.player_info import PlayerInfo
from shared.types.status_message import StatusMessages
from shared.utils.validation import parse_game_status, parse_player_info


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
        base.cTrav.showCollisions(render)
        
        self.mouse_locked = False

        self.player: None | Player = None
        self.anti_player: None | AntiPlayer  = None

        # Setup gui handling
        self.gui_manager = GuiManager()
        self.accept("escape", self.gui_manager.handle_custom, [StateTransitionEvents.ESC])
        self.accept(GUI_RETURN_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.RETURN])
        self.accept(GUI_SETTINGS_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.SETTINGS])
        self.accept(GUI_PLAY_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.PLAY])
        self.accept(GUI_MAIN_MENU_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.MAIN_MENU])
        self.accept(GUI_QUEUE_EVENT, self.gui_manager.handle_custom, [StateTransitionEvents.QUEUE])
        self.logger.debug("Gui handling and state machine initialized...")

        # General event handling
        self.accept(START_GAME_EVENT, self.__start_game)
        self.accept(ENTER_QUEUE_EVENT, self.__enter_queue)
        self.accept(CANCEL_QUEUE_EVENT, self.__cancel_queue)
        self.accept(WIN_EVENT, self.__finish_game, [True])
        self.accept(DEFEAT_EVENT, self.__finish_game, [False])
        self.accept(NETWORK_SEND_PRIORITY_EVENT, self.__priority_ws_send)

        self.player_id: str = str(uuid.uuid4())
        self.player_name = generate_name()
        self.match_id: None | str = None

        self.is_online: bool = False
        self.ws: None | MatchWS = None

        self.time_since_last_package: int = 1_000_000
        self.buildMap()

    def buildMap(self):
        
        self.waterfallbackground = loader.loadModel(getModelPath("waterfall"))
        self.waterfallbackground.reparentTo(render)
        
        self.waterfallbackground.setZ(2)
        self.waterfallbackground.setY(-4)
        
    
        self.waterfall = loader.loadModel("box")
        self.waterfall.reparentTo(render)
        self.waterfall.setTransparency(TransparencyAttrib.MAlpha)
        self.waterfall.setPos(-20,-34,-3)
        self.waterfall.setScale(40,0.1,36)

        texture2 = loader.loadTexture(getImagePath("transWater2"))
        texture = loader.loadTexture(getImagePath("transWater"))
        transTexture = loader.loadTexture(getImagePath("blue"))
        self.waterfall.setTexture(transTexture)
        self.textureStage0 = TextureStage("stage0")
        self.textureStage0.setMode(TextureStage.MBlend)
        
        self.waterfall.setTexture(self.textureStage0,texture,1)
        self.waterfall.setTexScale(self.textureStage0, 2, 2)

        
        self.textureStage1 = TextureStage("stage1")
        self.textureStage1.setMode(TextureStage.MAdd)
        
        self.waterfall.setTexture(self.textureStage1,texture,1)
        self.waterfall.setTexScale(self.textureStage1, 1, 1)
        
        
        
        taskMgr.add(self.shiftWaterfallTextureTask,"shift Task")
        
    def shiftWaterfallTextureTask(self,task):
        self.waterfall.setTexOffset(self.textureStage0, 0, (task.time*2) % 1.0 )
        self.waterfall.setTexOffset(self.textureStage1, 0, (task.time*0.4) % 1.0 )
        return Task.cont
    
    def __finish_game(self, is_victory):
        base.enableMouse()
        self.toggle_mouse()
        self.logger.info(f"Received game finish where victory: {is_victory}")
        if self.ws is not None:
            self.ws.close(reason="Finished")
        if self.ws_handle_task is not None:
            self.ws_handle_task.cancel()
            self.ws_handle_task = None
        self.is_online = False
        self.match_id = None
        if self.player is not None:
            self.player.destroy()
        if self.anti_player is not None:
            self.anti_player.destroy()
        if is_victory:
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

    def toggle_mouse(self):
        if self.mouse_locked:
            self.mouse_locked = False
            props = WindowProperties()
            props.setCursorHidden(False)
            base.win.requestProperties(props)
        else:
            self.mouse_locked = True
            props = WindowProperties()
            props.setCursorHidden(True)
            base.win.requestProperties(props)
    
    
    def __start_game(self, match_id="", is_offline=True):
        
        #cubeMap = loader.loadCubeMap(getImagePath("skybox"))
        self.spaceSkyBox = loader.loadModel(getModelPath("skysphere"))
        self.spaceSkyBox.setScale(200)
        self.spaceSkyBox.setZ(-40)
        self.spaceSkyBox.setBin('background', 0)
        self.spaceSkyBox.setDepthWrite(0)
        self.spaceSkyBox.setTwoSided(True)
        #self.spaceSkyBox.setTexGen(TextureStage.getDefault(), TexGenAttrib.MWorldCubeMap)
        self.spaceSkyBox.reparentTo(render)
        self.spaceSkyBox.setLightOff()
        #self.spaceSkyBox.setTexture(cubeMap, 1)
        
        self.is_online = not is_offline
        base.disableMouse()
        self.toggle_mouse()
        
        dlight = DirectionalLight('my dlight')
        dlight.color = (1,1,1,1)
        dlight.setDirection(Vec3(0,-1,-0.2))
        dlnp = render.attachNewNode(dlight)
        alight = AmbientLight("ambi light")
        alight.color = (0.1,0.1,0.1,1)
        ambientnp = render.attachNewNode(alight)
        render.setLight(dlnp)     
        render.setLight(ambientnp) 
        
        
        
        render.setLight(dlnp)
        self.player = Player(self.camera,self.win)
        
        self.anti_player = AntiPlayer(self.win, self.is_online)
        self.camera.reparentTo(self.player.head)
        self.camera.setPos(0,-3,0.4)
        
        self.map = self.loader.loadModel("assets/models/map.egg")
        
        self.map.reparentTo(self.render)
        
        self.map.setZ(1.5)
        if is_offline:
            self.logger.info("Starting game in offline mode...")
            self.match_id = None
            self.player.start_match_timer()
            self.anti_player.start_match_timer()
        else:
            self.logger.info("Starting online game...")
            if self.queue_task is not None:
                self.queue_task.remove()
            self.queue_task = None
            self.ws = MatchWS(
                match_id=match_id, 
                player_id=self.player_id, 
                player_name=self.player_name,
                recv_callback=self.__process_ws_message)
        messenger.send(GUI_PLAY_EVENT)
           
    def __process_ws_message(self, msg):
        if self.anti_player is not None:
            # Player info package
            if (player_info := parse_player_info(msg)) is not None:
                self.anti_player.set_state(player_info)
                return
            if (game_status := parse_game_status(msg)) is not None:
                match game_status.message:
                    case StatusMessages.DEFEAT.value:
                        messenger.send(DEFEAT_EVENT)
                    case StatusMessages.VICTORY.value:
                        messenger.send(WIN_EVENT)
                    case StatusMessages.PLAYER_NAME.value:
                        self.anti_player.set_name(game_status.detail)
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
            self.ws.send_game_data(packet)

    def __main_loop_online(self, dt):
        self.time_since_last_package += dt
        if self.time_since_last_package > TIME_BETWEEN_PACKAGES_IN_S:
            packet = self.player.get_current_state()
            self.ws.send_game_data(packet)
            self.time_since_last_package = 0

    def __main_loop(self, task):
        dt = self.clock.dt

        if self.gui_manager.gui_state_machine.getCurrentOrNextState() != GuiStates.RUNNING.value:
            return Task.cont

        self.player.update(dt)
        self.anti_player.update(dt)

        if self.is_online:
            self.__main_loop_online(dt)
            return Task.cont
        else:
            pass
        return Task.cont
