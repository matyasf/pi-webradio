from src.HWButton import HWButton
from src.display.TextBox import TextBox
import typing
from typing import Callable
from asyncio import AbstractEventLoop
if typing.TYPE_CHECKING:
    from src.bluetooth_manager import BluetoothManager

class RadioChannel:
    def __init__(self, name:str, url:str, meta_data_url:str, data_func: Callable, textbox: TextBox) -> None:
        self.name = name
        self.url = url
        self.meta_data_url = meta_data_url
        self.data_func = data_func
        self.textbox = textbox

class PlayingState(object):
    PLAYING = "Playing"
    STOPPED = "Stopped"

class Screens(object):
    SONG_DISPLAY = "SONG_DISPLAY"
    BLUETOOTH_MENU = "BLUETOOTH_MENU"

class Globals:
    loop: AbstractEventLoop = None
    bluetooth: 'BluetoothManager' = None
    # hardware buttons at the top
    button1: HWButton = None
    button2: HWButton = None
    button3: HWButton = None
    button4: HWButton = None
    menu_button: HWButton = None
    # textboxes below the buttons
    tb1: TextBox = None
    tb2: TextBox = None
    tb3: TextBox = None
    tb4: TextBox = None
    # bottom status bar
    status_bar: TextBox = None
    radio_channels: list[RadioChannel] = None
    current_channel: RadioChannel = None
    playing_state: str = PlayingState.STOPPED
    current_artist: str = ''
    current_song: str = ''
    current_screen: str = Screens.SONG_DISPLAY

    def get_playing_message():
        status_msg = "Bluetooth not connected"
        connected_device = Globals.bluetooth.get_connected_device()
        if connected_device != None:
            if Globals.playing_state == PlayingState.PLAYING:
                status_msg = "Playing via " + connected_device.name
            else: status_msg = "Connected to " + connected_device.name + ", Playback stopped"
        return status_msg 