from src.HWButton import HWButton
from src.display.TextBox import TextBox
from src.display.display_engine import DisplayEngine
from src.globals import Globals, RadioChannel
from src.utils import Utils
from src.bluetooth_manager import BluetoothManager
from src.song_data_display import SongDataDisplay
from src.state_manager import StateManager
from src.radio_player import RadioPlayer
from src.linux_event_processor import LinuxEventProcessor
from src.gpio_handler import OutputPin
import src.webserver
import asyncio

def on_busy_changed(is_busy: bool):
    if is_busy:
        button_led.on()
    else:
        button_led.off()

async def main_loop():
    await Globals.bluetooth.init_async()
    LinuxEventProcessor.init(StateManager.on_play_pause)
    Globals.current_channel = Globals.radio_channels[0]
    connected_device = Globals.bluetooth.get_connected_device()
    if connected_device:
        RadioPlayer.play_radio()
        LinuxEventProcessor.on_bt_device_connected()
        Utils.log("Connected BT device: " + connected_device.name)
    StateManager.display_playing_ui()
    DisplayEngine.busy_event.handle(on_busy_changed)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(src.webserver.start_server())
        tg.create_task(asyncio.to_thread(Globals.button1.pin.wait_for_change))
        tg.create_task(asyncio.to_thread(Globals.button2.pin.wait_for_change))
        tg.create_task(asyncio.to_thread(Globals.button3.pin.wait_for_change))
        tg.create_task(asyncio.to_thread(Globals.button4.pin.wait_for_change))
        tg.create_task(asyncio.to_thread(Globals.menu_button.pin.wait_for_change))

Utils.log("===================================")
Utils.log("Starting radio")
DisplayEngine.init()
Globals.bluetooth = BluetoothManager(StateManager.on_bt_device_connected, StateManager.on_bt_device_disconnected)
Globals.tb1 = TextBox(0, 5, 180, 35, '', fontSize=23, hAlign='center')
Globals.tb2 = TextBox(180, 5, 180, 35, '', fontSize=23, hAlign='center')
Globals.tb3 = TextBox(360, 5, 180, 35, '', fontSize=23, hAlign='center')
Globals.tb4 = TextBox(540, 5, 180, 35, '', fontSize=23, hAlign='center')
Globals.status_bar = TextBox(0, 226, 720, 30, "", fontSize=23) # with PlayFair font sizes 23, 26 look nice
Globals.button1 = HWButton(20)
Globals.button2 = HWButton(16)
Globals.button3 = HWButton(12)
Globals.button4 = HWButton(6)
Globals.menu_button = HWButton(13, StateManager.display_menu)
# radio france metadata URLs from https://github.com/PaulWebster/RadioFrance/blob/master/RadioFrance/Plugin.pm#L132
Globals.radio_channels = [ # needs to have 4 elements
    RadioChannel("La Baroque",
        "http://icecast.radiofrance.fr/francemusiquebaroque-hifi.aac",
        "https://api.radiofrance.fr/livemeta/live/408/webrf_webradio_player",
        SongDataDisplay.get_and_display_song_data_radio_france,
        Globals.tb1),
    RadioChannel("Concerts",
        "http://icecast.radiofrance.fr/francemusiqueconcertsradiofrance-hifi.aac", # or https
        "https://api.radiofrance.fr/livemeta/live/403/webrf_webradio_player",
        SongDataDisplay.get_and_display_song_data_radio_france,
        Globals.tb2),
    RadioChannel("Monde",
        "https://icecast.radiofrance.fr/francemusiqueocoramonde-hifi.aac", # or https
        "https://api.radiofrance.fr/livemeta/live/404/webrf_webradio_player",
        SongDataDisplay.get_and_display_song_data_radio_france,
        Globals.tb3),
    RadioChannel("Classique+",
        "https://icecast.radiofrance.fr/francemusiqueclassiqueplus-hifi.aac", # or https
        "https://api.radiofrance.fr/livemeta/live/402/webrf_webradio_player",
        SongDataDisplay.get_and_display_song_data_radio_france,
        Globals.tb4)#,
    #RadioChannel("KEXP",
    #    "http://live-aacplus-64.kexp.org/kexp64.aac",
    #    "http://api.kexp.org/v2/plays/?format=json&limit=1&offset=0",
    #    SongDataDisplay.get_and_display_kexp,
    #    Globals.tb4)#,
    #RadioChannel("BBC 3"
    #    "http://as-hls-ww-live.akamaized.net/pool_904/live/ww/bbc_radio_three/bbc_radio_three.isml/bbc_radio_three-audio%3d96000.norewind.m3u8",
    #    "https://rms.api.bbc.co.uk/v2/services/bbc_radio_three/segments/latest",
    #    SongDataDisplay.get_and_display_bbc3,
    #    Globals.tb4)
]

button_led = OutputPin(26) # LED on main button

Globals.loop = asyncio.get_event_loop()
Globals.loop.run_until_complete(main_loop())
