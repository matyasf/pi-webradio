# gdbus introspect --system --dest org.bluez --object-path /org/bluez
# hostname -I returns the IP address

# which python
# realpath ./venv/bin/python
# sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3.11
import gpiod
import time
from gpiod.line import Direction, Value

#print( str(gpiod.is_gpiochip_device("/dev/gpiochip0") ) )
#with gpiod.Chip("/dev/gpiochip0") as chip: # the pins on the Pi
#    info = chip.get_info()
#    print(f"{info.name} [{info.label}] ({info.num_lines} lines)")
LINE = 26

abc = gpiod.request_lines(
    "/dev/gpiochip0",
    consumer="faszfasz",
    config={7: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)})
abc.release() # same as the with syntax

with gpiod.request_lines(
    "/dev/gpiochip0",
    config={
        LINE: gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)
    },
) as request:
    while True:
        request.set_value(LINE, Value.ACTIVE)
        time.sleep(1)
        request.set_value(LINE, Value.INACTIVE)
        time.sleep(1)
