from typing import Callable
from src.display.display_engine import DisplayEngine
from src.gpio_handler import InputPin

class HWButton:
    def __init__(self, GPIO_pin: int, callback: Callable = None, *callback_args):
        self.callback_args = callback_args
        self.callback = callback
        self.GPIO_pin = GPIO_pin
        self.pin = InputPin(GPIO_pin, debounce_period_secs=0.1)
        self.is_busy = False
        # needed because it queues up events while busy and calls them later
        DisplayEngine.busy_event.handle(self.on_busy_changed)
        self.pin.add_change_listener(self.onclick_callback)
    
    def on_busy_changed(self, is_busy: bool):
        self.is_busy = is_busy

    def update_callback_func(self, callback: Callable, *callback_args):
        self.callback_args = callback_args
        self.callback = callback

    def onclick_callback(self):
        if not self.is_busy:
            from src.globals import Globals
            Globals.loop.call_soon_threadsafe(self.callback, *self.callback_args)
