import logging

from direct.particles.ParticleEffect import ParticleEffect
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from game.const.events import UPDATE_SHADOW_SETTINGS
from game.helpers.config import should_use_good_shadows
from game.helpers.helpers import getImagePath, getModelPath, getParticlePath
from panda3d.core import TextureStage, DirectionalLight, Vec3, Spotlight, TransparencyAttrib
import copy

from game.utils.sound import add_3d_sound_to_node

class Map(DirectObject):
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.slight = None
        self.water_fall_count = 0

        self.accept(UPDATE_SHADOW_SETTINGS, self.update_shadow_settings)

    def build_map(self):
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

        self.update_shadow_settings()
        
        slnp = render.attachNewNode(self.slight)
         # Position and rotate the spotlight
        slnp.setPos(0, 50, 50)  # Position the spotlight
        slnp.setHpr(0, -135, 0)  # Make the spotlight point at the model
        render.setLight(slnp)
       
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
        
        self.map = base.loader.loadModel(getModelPath("map"))
        
        self.map.reparentTo(render)
        
        self.map.setZ(-2)
        self.map.setShaderAuto()
        
        self.treeTops = base.loader.loadModel(getModelPath("treeTops"))
        self.treeTops.reparentTo(render)
        self.treeTops.setZ(-2)
        self.treeTops.setShaderOff()
        self.treeTops.setLightOff()
        
        self.river = base.loader.loadModel(getModelPath("river"))
        self.river.reparentTo(render)
        self.river.setZ(-2)

        texture = loader.loadTexture(getImagePath("pxArt (8)"))

        # Try to find an existing texture stage
        self.riverTextureStage = self.river.findTextureStage("dust.png")

        self.river.setTexture(self.riverTextureStage, texture, 1)  # Use priority to force replace
        taskMgr.add(self.__shift_river_texture,"shift river Task")
        
        self.waterfall = loader.loadModel(getModelPath("waterfall"))
        self.waterfall2 = loader.loadModel(getModelPath("waterfall2"))
        
        self.build_waterfall(self.waterfall)
        self.build_waterfall(self.waterfall2)
        
        self.particle_owner = render.attachNewNode("particle_owner")
        self.particle_owner.setShaderOff()
        
        
        p = ParticleEffect()
        p.loadConfig(getParticlePath("leaves"))
        p.start(parent = self.particle_owner, renderParent = self.particle_owner)
        p.setPos(12,15,0)
        
        p = ParticleEffect()
        p.loadConfig(getParticlePath("leaves"))
        p.start(parent = self.particle_owner, renderParent = self.particle_owner)
        p.setPos(-8,22,0)

        for i in range(15):
            p = ParticleEffect()
            p.loadConfig(getParticlePath("spray"))
            p.start(parent = self.particle_owner, renderParent = self.particle_owner)
            p.setPos(-5.5+i*0.8,-8,0.4)
            
            p.setDepthWrite(False)
            p.setBin("fixed", 0)

    def update_shadow_settings(self, _=None):
        if self.slight is None:
            return
        if should_use_good_shadows():
            self.slight.setShadowCaster(True, 2048, 2048) 
        else:
            self.slight.setShadowCaster(True, 512, 512) 

    def build_waterfall(self, waterfall):
        waterfall.reparentTo(render)
        waterfall.setTransparency(TransparencyAttrib.MAlpha)
        waterfall.setPos(0,0,-2)
        
        self.water_fall_count +=1
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

        taskMgr.add(self.__shift_waterfall_texture,f"shift Task {self.water_fall_count}",extraArgs=[waterfall,textureStage0,textureStage1],appendTask = True)

    def __shift_waterfall_texture(self, waterfall, textureStage0, textureStage1, task):
        waterfall.setTexOffset(textureStage0, 0, (task.time*2) % 1.0 )
        waterfall.setTexOffset(textureStage1, 0, (task.time*0.4) % 1.0 )
        return Task.cont
    
    def __shift_river_texture(self, task):
        self.river.setTexOffset(self.riverTextureStage,0,(task.time*-0.2) % 1.0)
        return Task.cont

