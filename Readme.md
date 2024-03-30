## Internet radio for Raspberry Pi with eInk dispay

### Setup

> Note that this code will only run on a Raspberry Pi (tested on a Pi Zero 2 and a Pi 4), needs Python 3.9+

1. Enable SPI in `sudo raspi-config` (under Interface options)

2. Install dependencies: `sudo apt install mpv bluez-alsa-utils python3-dev`

3. create and activate venv: `python -m venv ./venv` and `source ./venv/bin/activate`

4. Install Python dependencies: `pip install -r requirements.txt`

5. Added `dtoverlay=spi0-0cs` to the bottom of `/boot/firmware/config.txt` (see https://github.com/raspberrypi/bookworm-feedback/issues/179 )

6. The lookup tables for Pervasive displays are not open source. You need to contact them and then add to `src/display/pervasive_luts.py`. It needs to have 2 arrays with hex code `int`s like: `fastLUT=[0x00,0x23] globalLUT=[0x12,0x34]`

7. (optional) raise BT codec quality: Run `sudo systemctl edit bluealsa` follow instructions and add `--sbc-quality=xq` to bluealsa's startup parameter.

8. (optional) The radio has a small built-in webserver to control it, you can access it on port 80. This port is only accessible for root users, to circumvent this:
   - run `which python`
   - run `realpath [which result]`
   - run `sudo setcap 'cap_net_bind_service=+ep' [realpath result]`

### Run the project

`python3 main.py`

You can set it to auto-run on startup e.g. cron: 

1. Log in as the user you want to run it.
2. run `crontab -e` and enter here: `@reboot cd /home/[PATH_TO_REPO]/pi-radio/ && start_radio.sh` (set it to executable with `chmod +x`, debug with `journalctl -u cron.service`)

### Hardware components

audio output: https://www.adafruit.com/product/3678

eink display: https://www.pervasivedisplays.com/product/5-81-e-ink-displays/

### Errors

#### No sound

- Check `alsamixer`, it should display the Adafruit card. If not you can change it with sudo and run the program as root. 

- Try connecting your BT speaker manually with `bluetoothctl` and check for errors.

- `bluealsa-aplay --list-devices` -- should list your BT device

- `/bin/echo -e "show\ninfo 12:23:34:45:56" | bluetoothctl`  -- should list your BT device

- `dbus-monitor --system` -- Lists dbus messages. You should see here when BT connects

- `sudo btmon` -- shows low level BT messages. You should see button presses here

- Uninstall `pulseaudio`, it conflicts with `bluealsa`

##### BT play/pause button does not work

- Check with `evtest` where your BT device is connected to, now its looking for a device whose name contains 'AVRCP' 

##### gpio busy

check whats using it with `cat /sys/kernel/debug/gpio`

### TODO/bugs

- use `libmpv` instead of `mpv`, so it doesnt depends on distro updates
- show errors/exceptions on the web control interface
Add New features:   
- Add "Audio Jack" to menu, when selected play via Jack.   

Current BT/Jack logic:
On startup try to connect to a saved BT device.
When connected/disconnected to a BT device OR pressing play on a device OR changing channel play on BT if its connected, on Jack if its not.