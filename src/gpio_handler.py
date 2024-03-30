import gpiod
from gpiod.line import Direction, Value, Edge, Bias
from gpiod import LineSettings
from datetime import timedelta

class OutputPin: # like a LED or a pin of a display
    def __init__(self, GPIO_pin: int) -> None:
        self.pin = GPIO_pin
        self.request = gpiod.request_lines("/dev/gpiochip0",
            config = {GPIO_pin: LineSettings(direction=Direction.OUTPUT, output_value=Value.INACTIVE)})
    
    def on(self):
        self.request.set_value(self.pin, Value.ACTIVE)
    
    def off(self):
        self.request.set_value(self.pin, Value.INACTIVE)

class InputPin:
    # on_change is a function that gets called if the value changes
    def __init__(self, GPIO_pin: int, debounce_period_secs: float = 0) -> None:
        self.pin = GPIO_pin
        self.request = gpiod.request_lines("/dev/gpiochip0",
            config = {
                GPIO_pin: LineSettings(
                    direction=Direction.INPUT,
                    edge_detection=Edge.FALLING,
                    bias=Bias.PULL_UP,
                    debounce_period=timedelta(seconds = debounce_period_secs))
                })

    # this is needed for a Button but not for the display's pin
    def add_change_listener(self, callback_fun):
        '''note that the callback is called on a different thread!'''
        self.on_change_fun = callback_fun

    def wait_for_change(self):
        '''Blocks the current thread until an edge event. If one arrives it calls the change listener function.'''
        while True:
            self.request.wait_edge_events() # blocks thread until an event
            print("GPIO input event on pin " + str(self.pin))
            self.request.read_edge_events(999)
            self.on_change_fun()

    @property
    def is_active(self) -> bool:
        return self.request.get_value(self.pin) == Value.ACTIVE
