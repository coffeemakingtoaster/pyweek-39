from panda3d.core import WindowProperties

def enable_mouse():
    base.enableMouse()
    props = WindowProperties()
    props.setCursorHidden(False)
    base.win.requestProperties(props)

def disable_mouse():
    base.disableMouse()
    props = WindowProperties()
    props.setCursorHidden(True)
    base.win.requestProperties(props)
