import evdev
from src.utils import Utils
from asyncio import create_task, sleep, Task
from typing import Callable

class LinuxEventProcessor:
    """
    Class to process native Linux events.
    These are raised when e.g. a button is pushed on a Bluetooth device
    """
    evdev_task: Task | None = None
    play_pause_callback: Callable = None

    def init(play_pause_callback: Callable):
        LinuxEventProcessor.play_pause_callback = play_pause_callback

    def on_bt_device_connected():
        LinuxEventProcessor.evdev_task = create_task(LinuxEventProcessor.evdev_handler())
    
    def on_bt_device_disconnected():
        LinuxEventProcessor.evdev_task.cancel()
        LinuxEventProcessor.evdev_task = None

    async def evdev_handler():
        num_tries = 20
        while True:
            devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
            path = None
            for dev in devices:
                if dev.name.find("AVRCP") > -1: # not nice. I dont know what other BT speakers have for path
                    path = dev.path
            if path == None:
                Utils.log("LinuxEventProcessor: Cannot find device whose name contains 'AVRCP'")
                num_tries = num_tries - 1
                if num_tries == 0:
                    return # give up after 10 secs
                await sleep(0.5)
            else:
                device = evdev.InputDevice(path)
                Utils.log("LinuxEventProcessor: Reading from device " + device.name)
                try:
                    async for event in device.async_read_loop():
                        if event.type == evdev.ecodes.EV_KEY and event.value == 1:
                            if event.code == evdev.ecodes.KEY_PAUSECD or event.code == evdev.ecodes.KEY_PLAYCD:
                                Utils.log("LinuxEventProcessor: Play/pause key pressed")
                                LinuxEventProcessor.play_pause_callback()
                except OSError as err:
                    print("LinuxEventProcessor: caught OSError in read loop: " + str(err))