
import asyncio
from src.display.display_engine import DisplayEngine
from src.globals import Globals
from src.utils import Utils
from src.bluetooth_manager import BluetoothDevice

class BluetoothMenu:
    """Menu shown when the main button is pressed"""
    current_selection: BluetoothDevice | None = None
    current_devices: list[BluetoothDevice] = []

    def on_enter_menu():
        Globals.button1.update_callback_func(BluetoothMenu.on_menu_next)
        Globals.button2.update_callback_func(BluetoothMenu.on_menu_select)
        Globals.button3.update_callback_func(BluetoothMenu.on_menu_rescan)
        BluetoothMenu.discover_devices()
    
    def discover_devices():
        duration_secs = 5
        DisplayEngine.increase_busy_counter()
        DisplayEngine.clear_display()
        DisplayEngine.draw_simple_text(5, 80, 35, "Scanning for Bluetooth speakers..")
        DisplayEngine.draw_simple_text(5, 140, 25, "This takes " + str(duration_secs) + " seconds")
        Globals.bluetooth.scan_for_devices_callback(BluetoothMenu.on_device_discover_ended, duration_secs)
    
    def on_device_discover_ended(error_result: str | None):
        DisplayEngine.clear_display()
        if error_result:
            Utils.log("Error when scanning BT devices " + error_result)
            BluetoothMenu.update_bottom_text("Scan error: " + error_result)
        else:
            devs = list(Globals.bluetooth.devs.values())
            Utils.log('found ' + str(len(devs)) + ' bluetooth device(s)')
            BluetoothMenu.current_devices = devs
            # check if selected device still in list
            if len(devs) == 0:
                BluetoothMenu.current_selection = None
            elif not BluetoothMenu.current_selection:
                BluetoothMenu.current_selection = devs[0]
            else:
                found = False
                for dev in devs:
                    if BluetoothMenu.current_selection.address == dev.address:
                        found = True
                        break
                if found == False:
                    BluetoothMenu.current_selection = devs[0]
            BluetoothMenu.display_devices()
        Globals.tb1.text = "Next"
        Globals.tb2.text = "Connect"
        Globals.tb3.text = "Rescan"
        Globals.tb4.text = "Back"
        DisplayEngine.draw_text(Globals.tb1)
        DisplayEngine.draw_text(Globals.tb2)
        DisplayEngine.draw_text(Globals.tb3)
        DisplayEngine.draw_text(Globals.tb4)
        DisplayEngine.decrease_busy_counter()

    def display_devices():
        DisplayEngine.draw_rect(0, 40, 720, 180)
        cx = 5
        cy = 40
        for dev in BluetoothMenu.current_devices:
            txt = dev.name
            txt = (txt[:15] + '..') if len(txt) > 17 else txt
            if BluetoothMenu.current_selection.address == dev.address:
                txt = '->' + txt
            DisplayEngine.draw_simple_text(cx, cy, 20, txt)
            cy = cy + 20
            if cy > 200:
                cy = 40
                cx = cx + 100
        # status bar text
        status_txt = "Select device to connect to."
        if len(BluetoothMenu.current_devices) == 0:
            status_txt = "No devices found. Press Rescan to retry."
        connected_dev = Globals.bluetooth.get_connected_device()
        if connected_dev != None:
            status_txt = 'connected to ' + connected_dev.name + '.'
        BluetoothMenu.update_bottom_text(status_txt)

    def update_bottom_text(txt: str):
        Globals.status_bar.text = txt
        DisplayEngine.draw_rect(0, 226, 720, 30)
        DisplayEngine.draw_text(Globals.status_bar)

    def on_menu_next():
        for i, dev in enumerate(BluetoothMenu.current_devices):
            if BluetoothMenu.current_selection.address == dev.address:
                if i == len(BluetoothMenu.current_devices) - 1:
                    BluetoothMenu.current_selection = BluetoothMenu.current_devices[0]
                else:
                    BluetoothMenu.current_selection = BluetoothMenu.current_devices[i + 1]
                BluetoothMenu.display_devices()
                return

    def on_menu_select():
        if BluetoothMenu.current_selection:
            asyncio.create_task(BluetoothMenu.pair_connect_trust())

    async def pair_connect_trust():
        DisplayEngine.increase_busy_counter()
        connected_device = Globals.bluetooth.get_connected_device()
        if connected_device:
            # needed because of a Bluez bug(?), that there is no event when something steals the BT speaker.
            # TODO does NOT work, cannot steal it
            await connected_device.disconnect()
        res = await BluetoothMenu.current_selection.pair_connect_trust()
        BluetoothMenu.update_bottom_text(res)
        DisplayEngine.decrease_busy_counter()

    def on_menu_rescan():
        BluetoothMenu.discover_devices()

    def on_navigated_away():
        BluetoothMenu.current_selection = None
        BluetoothMenu.current_devices = []