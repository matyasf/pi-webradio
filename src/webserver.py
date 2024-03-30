
from microdot import Microdot, send_file
from src.globals import Globals
from src.display.display_engine import DisplayEngine
from src.state_manager import StateManager

app = Microdot()

@app.route('/static/<path:path>')
async def static(request, path):
    if '..' in path:
        return 'Not found', 404 # directory traversal is not allowed
    return send_file('assets/static/' + path, max_age=2592000)

@app.route('favicon.ico')
async def favicon(request):
    return send_file('assets/static/favicon.png', max_age=2592000)

@app.route('/')
async def index(request):
    return send_file('assets/static/index.html', max_age=2592000)

@app.route('/api/getStatus')
async def get_status(request):
    output_str = Globals.get_playing_message()
    result = {
        'channels': [],
        'currentChannel': Globals.current_channel.name,
        'state': Globals.playing_state,
        'output': output_str,
        'currentSong': Globals.current_song,
        'currentArtist': Globals.current_artist
    }
    for channel in Globals.radio_channels:
        result['channels'].append(channel.name)
    return result

@app.route('/api/playPause')
async def play_pause(request):
    if DisplayEngine.busy_counter != 0:
        print("API: is busy!")
        return {'status':  "Radio is busy, please try later"}
    StateManager.on_play_pause()
    return {'state': Globals.playing_state}

@app.route('/api/volumeDown', methods=['POST'])
async def on_volume_down(request):
    if DisplayEngine.busy_counter != 0:
        return {'status':  "Radio is busy, please try later"}
    dev = Globals.bluetooth.get_connected_device()
    if dev and dev.media_control1:
        await dev.media_control1.volume_down()
    else:
        return {'status': "Volume setting only possible when a Bluetooth device is connected"} 
    return {'status': "OK"}

@app.route('/api/volumeUp', methods=['POST'])
async def on_volume_up(request):
    if DisplayEngine.busy_counter != 0:
        return {'status':  "Radio is busy, please try later"}
    dev = Globals.bluetooth.get_connected_device()
    if dev and dev.media_control1:
        await dev.media_control1.volume_up()
    else:
        return {'status': "Volume setting only possible when a Bluetooth device is connected"} 
    return {'status': "OK"}

@app.route('/api/changeChannel', methods=['POST'])
async def change_channel(request):
    channel_name = request.json['channelName']
    print("API: received channel " + channel_name)
    if DisplayEngine.busy_counter != 0:
        return {'status':  "Radio is busy, please try later"}
    for channel in Globals.radio_channels:
        if channel.name == channel_name:
            StateManager.on_change_channel(channel)
            return {'status':  "OK"}
    print("API: change_channel err: unknown channel " + channel_name)
    return {'status': "unknown channel " + channel_name}

async def start_server():
    await app.start_server(port=80) # will never return