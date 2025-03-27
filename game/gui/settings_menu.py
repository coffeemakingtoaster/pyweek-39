from game.const.events import GUI_RETURN_EVENT
from game.gui.gui_base import GuiBase
from panda3d.core import TextNode, TransparencyAttrib

from game.helpers.config import get_player_name, set_music_volume, set_player_name, set_sfx_volume, set_fullscreen_value, get_music_volume, get_sfx_volume, get_fullscreen_value, get_fps_counter_enabled, set_fps_counter_enabled

from direct.gui.DirectGui import DirectButton, DirectCheckButton, DirectEntry, DirectSlider, DirectLabel, DirectFrame, DGG, OnscreenImage

from os.path import join

class SettingsMenu(GuiBase):
    def __init__(self) -> None:
        super().__init__("SettingsMenu")

        TEXT_COLOR = (0.82, 0.34, 0.14, 1) #  NEW: rgb(208, 86, 36) (0.82f, 0.34f, 0.14f, 1f)
        TEXT_ALTERNATE_COLOR = (1.0, 0.84, 0.62, 1) # rgb(255, 214, 159) (1f, 0.84f, 0.62f, 1f)
        TEXT_BOX_COLOR = (1, 1, 1, 1) # RGB: 235, 198, 81

        buttonImages = loader.loadTexture("assets/textures/button_bg.png"),
        font = loader.loadFont("assets/fonts/the_last_shuriken.ttf")

        self.menu_elements = []

        menu_box = DirectFrame(
            frameColor=TEXT_BOX_COLOR, 
            frameSize=(-1.4, 1.4, 0.8, -0.8),
            pos=(0, 0, 0), 
            frameTexture = "assets/textures/settings_menu_board.png"
        )
        menu_box.setTransparency(TransparencyAttrib.MAlpha)
        self.ui_elements.append(menu_box)

        self.menu_elements.append(DirectLabel(
            parent = menu_box,
            text="Settings", 
            scale=0.2, 
            pos=(0,0,0.5), 
            relief=None, 
            text_fg=(TEXT_ALTERNATE_COLOR), 
            text_font = font, 
            text_align = TextNode.ACenter)
        )

        checkbox_image = loader.loadTexture("assets/textures/checkbox.png")
        checkbox_checked_image = loader.loadTexture("assets/textures/checkbox_checked.png")

        self.player_name_input = DirectEntry(
            parent=menu_box,
            text = "", 
            pos = (-0.5, 0, 0.25),
            width=16,
            scale=.1, 
            command = self.update_player_name,
            text_align = TextNode.ACenter,
            initialText = get_player_name(), 
            frameTexture = buttonImages,
            text_scale = 0.7,
            numLines = 1, 
            focus = 0, 
            text_font=font
        )
        self.menu_elements.append(self.player_name_input)

        save_player_name_button = DirectButton(
            parent = menu_box,
            text=("Confirm"),
            text_fg=(TEXT_COLOR),
            text_font = font,
            relief=DGG.FLAT,
            pos = (0.5, 0, 0.275),
            scale=0.05, 
            frameTexture = buttonImages,
            #pad = (1, 0.1),
            frameSize = (-4, 4, -1, 1),
            text_pos = (0, -0.2),
            text_scale=0.5,
            frameColor = (1,1,1,1),
            command=self.update_player_name_from_button)
        save_player_name_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(save_player_name_button)

        fullscreen_checkbox = DirectCheckButton(
            parent = menu_box,
            text="Fullscreen", 
            pos=(0,0,0.05),
            scale=0.15, 
            indicatorValue=get_fullscreen_value(), 
            command=self.toggle_fullscreen,
            relief=None,
            boxImage = (checkbox_image, checkbox_checked_image),
            boxPlacement = 'right',
            boxImageScale = 0.5,
            boxRelief = None,
            text_fg=(TEXT_ALTERNATE_COLOR),
            text_font = font,
            text_scale = 0.7,
            pad = (0.5,0), 
            text_align = TextNode.ALeft
        )
        fullscreen_checkbox.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(fullscreen_checkbox)

        fps_checkbox = DirectCheckButton(
            parent = menu_box,
            text="Show FPS", 
            pos=(-1,0,0.05),
            scale=0.15,
            relief=None, 
            indicatorValue=get_fps_counter_enabled(), 
            command=self.update_fps,
            boxPlacement = 'right',
            boxRelief = None,
            boxImage = (checkbox_image, checkbox_checked_image),
            boxImageScale = 0.5,
            text_fg=(TEXT_ALTERNATE_COLOR),
            text_font = font,
            text_scale = 0.7,
            pad = (1,0), 
            text_align = TextNode.ALeft
        )
        fps_checkbox.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(fps_checkbox)
        
        current_music_volume = get_music_volume()
        music_slider_text = DirectLabel(
            parent = menu_box,
            text="Music volume",
            relief=None, 
            text_fg=(TEXT_ALTERNATE_COLOR),
            text_font = font,
            scale=0.1, 
            pos=(-0.5,0,-0.15)
        )
        self.menu_elements.append(music_slider_text)

        self.music_volume_slider = DirectSlider(
            parent = menu_box,
            pageSize=1, 
            range=(0,100), 
            pos=(-0.5,0,-0.25), 
            value=int(current_music_volume * 100),
            thumb_image_scale = 0.5,
            scale=0.06, 
            thumb_image = checkbox_image,
            thumb_scale = 0.2,
            frameSize =  (-3, 3, -0.5, 0.5),
            thumb_relief = None,  
            command=self.update_music_volume,
            geom_scale=(10, 1, 1)
            )
        self.music_volume_slider.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(self.music_volume_slider)

        current_sfx_volume = get_sfx_volume()
        sfx_slider_text = DirectLabel(
            parent = menu_box,
            text="SFX volume",
            text_fg=(TEXT_ALTERNATE_COLOR),
            text_font = font,
            relief=None,  
            scale=0.1, 
            pos=(0.5,0,-0.15)
        )
        self.menu_elements.append(sfx_slider_text)

        self.sfx_volume_slider = DirectSlider(
            parent = menu_box,
            pageSize=1, 
            range=(0,100), 
            pos=(0.5,0,-0.25),  
            scale=0.06, 
            thumb_image = checkbox_image,
            thumb_image_scale = 0.5,
            frameSize =  (-3, 3, -0.5, 0.5),
            value=int(current_sfx_volume * 100),
            thumb_relief = None,
            command=self.update_sfx_volume)
        self.sfx_volume_slider.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(self.sfx_volume_slider)

        play_sample_sfx_button = DirectButton(
            parent = menu_box,
            text=("Test sound"),
            text_fg=(TEXT_COLOR),
            text_font = font,
            relief=DGG.FLAT,
            pos=(0.5,0,-0.4), 
            scale=0.05, 
            frameTexture = buttonImages,
            #pad = (1, 0.1),
            frameSize = (-4, 4, -1, 1),
            text_pos = (0, -0.2),
            text_scale=0.5,
            frameColor = (1,1,1,1),
            command=self.play_sample_sound)
        play_sample_sfx_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(play_sample_sfx_button)

        main_menu_button = DirectButton(
            parent = menu_box,
            text=("Main Menu"),
            text_fg=(TEXT_COLOR),
            text_font = font,
            relief=DGG.FLAT, 
            pos=(0,0,-0.6), 
            scale=0.1, 
            frameTexture = buttonImages,
            #pad = (1, 0.1),
            frameSize = (-4, 4, -1, 1),
            text_scale=0.75,
            frameColor = (1,1,1,1),
            text_pos = (0, -0.2),
            command=self.return_to_main_menu)
        main_menu_button.setTransparency(TransparencyAttrib.MAlpha)
        self.menu_elements.append(main_menu_button)

    def return_to_main_menu(self):
        messenger.send(GUI_RETURN_EVENT)

    def toggle_fullscreen(self, status):
        set_fullscreen_value(status == 1)

    def toggle_fps_counter(self, status):
        set_fullscreen_value(status == 1)

    def update_sfx_volume(self):
        value = self.sfx_volume_slider["value"]
        set_sfx_volume(value/100)

    def update_music_volume(self):
        value = self.music_volume_slider["value"]
        set_music_volume(value/100)

    def update_player_name(self, new_name: str):
        if len(new_name) == 0:
            return
        set_player_name(new_name)

    def update_player_name_from_button(self):
        self.update_player_name(self.player_name_input.get())

    def play_sample_sound(self):
        sample_sfx = base.loader.loadSfx(join("assets", "sfx", "sample.wav"))
        sample_sfx.play()

    def update_fps(self, status):
        set_fps_counter_enabled(status == 1)
