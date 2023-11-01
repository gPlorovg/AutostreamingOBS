import obspython as obs
import os


# Description displayed in the Scripts dialog window
def script_description():
    return """Source Shake!!
            Shake a source in the current scene when a hotkey is pressed. Go to Settings
             then Hotkeys to select the key combination.Check the
            Source Shake Scripting Tutorial on the OBS Wiki for more information."""


def do():
    print("do")


def script_load(settings):
    obs.timer_add(do, 5000)

