from subprocess import Popen
from src.globals import Globals, PlayingState
from src.utils import Utils

class RadioPlayer:
    process: Popen = None

    def play_radio():
        if RadioPlayer.process != None:
            Utils.log("stopping playback")
            RadioPlayer.process.terminate()
            RadioPlayer.process = None
        Globals.playing_state = PlayingState.STOPPED
        connected_device = Globals.bluetooth.get_connected_device()
        if connected_device:
            # TODO use libmpv with https://github.com/jaseg/python-mpv
            # mpv --audio-device=help  -- see all devices
            # if its choppy see how to buffer at https://learn.adafruit.com/adafruit-i2s-stereo-decoder-uda1334a/pi-i2s-tweaks
            Utils.log("RadioPlayer: playing via Bluetooth")
            Globals.playing_state = PlayingState.PLAYING
            RadioPlayer.process = Popen(["mpv", Globals.current_channel.url,
                                         "--audio-device=alsa/bluealsa:DEV=" + connected_device.address + ",PROFILE=a2dp",
                                         "--quiet"])
        #else:
        #    Utils.log("playing via jack output")
        #    RadioPlayer.process = Popen(["mpv", Globals.current_channel.url,
        #                                 "--audio-device=alsa","--quiet"]) 

    def stop_radio():
        if RadioPlayer.process != None:
            Utils.log("stopping playback")
            RadioPlayer.process.terminate()
            RadioPlayer.process = None
        Globals.playing_state = PlayingState.STOPPED