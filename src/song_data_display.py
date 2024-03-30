from urllib.error import URLError
from urllib import request
import json
import time
import asyncio
from datetime import datetime
from src.display.TextBox import TextBox
from src.display.display_engine import DisplayEngine
from src.globals import Globals, PlayingState
from src.utils import Utils

class SongDataDisplay:

    next_update_timer:asyncio.TimerHandle = None
    large_text: TextBox = TextBox(0, 35, 720, 40, '', fontSize=55)
    small_text: TextBox = TextBox(0, 135, 720, 30, '', fontSize=30, line_spacing=1.2)
    time_text: TextBox = TextBox(0, -45, 720, 210, '', fontSize=250, hAlign='center', font='assets/static/IBMPlexSans-Medium.ttf')
    
    def update_playing_display():
        if SongDataDisplay.next_update_timer != None:
            SongDataDisplay.next_update_timer.cancel()
        if Globals.bluetooth.get_connected_device() != None and Globals.playing_state == PlayingState.PLAYING:
            Globals.tb1.text = Globals.radio_channels[0].name
            Globals.tb2.text = Globals.radio_channels[1].name
            Globals.tb3.text = Globals.radio_channels[2].name
            Globals.tb4.text = Globals.radio_channels[3].name
            selected_tb = Globals.current_channel.textbox
            selected_tb.text = ">" + selected_tb.text
            DisplayEngine.draw_rect(0, 10, 720, 30)
            DisplayEngine.draw_text(Globals.tb1)
            DisplayEngine.draw_text(Globals.tb2)
            DisplayEngine.draw_text(Globals.tb3)
            DisplayEngine.draw_text(Globals.tb4)
            # calls one of the get_and_display functions below
            Globals.current_channel.data_func(Globals.current_channel.meta_data_url)
        else:
            Globals.current_artist = ''
            Globals.current_song = ''
            SongDataDisplay.display_just_time()
        DisplayEngine.draw_rect(0, 226, 720, 30)
        Globals.status_bar.text = Globals.get_playing_message()
        DisplayEngine.draw_text(Globals.status_bar)
    
    def display_just_time():
        # Utils.log("updating time")
        DisplayEngine.draw_rect(0, 0, 720, 225)
        SongDataDisplay.time_text.text = datetime.now().strftime('%H:%M')
        DisplayEngine.draw_text(SongDataDisplay.time_text)
        next_update_in = 61 - datetime.now().second # update every 1st second of each minute
        SongDataDisplay.next_update_timer = Globals.loop.call_later(next_update_in, SongDataDisplay.display_just_time)

    def get_and_display_bbc3(meta_data_url: str):
        req = request.Request(meta_data_url,
        headers={'Accept':'*/*', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'})
        try:
            with request.urlopen(req) as result:
                data = json.loads(result.read().decode('utf-8'))
                #print(data)
                if data["data"] and len(data["data"]) > 0:
                    song = data["data"][0]["titles"]
                    Globals.current_song = song["primary"]
                    Globals.current_artist = song["secondary"]
                else:
                    Globals.current_artist = "BBC3"
                    Globals.current_song = "Wrong API response :("
                    Utils.log("BBC 3 wrong API response " + str(data))
                SongDataDisplay.large_text.text = Utils.truncate(Globals.current_artist, 50)
                SongDataDisplay.small_text.text = Utils.truncate(Globals.current_song, 80)
                time_until_next: int = 60 # TODO fix
                DisplayEngine.draw_rect(0, 40, 720, 186)
                y_pos = DisplayEngine.draw_text(SongDataDisplay.large_text)
                SongDataDisplay.small_text.yc = y_pos + 6
                DisplayEngine.draw_text(SongDataDisplay.small_text)
                #Utils.log("BBC 3 refresh. Next metadata query in 60 secs")
                SongDataDisplay.next_update_timer = Globals.loop.call_later(time_until_next, SongDataDisplay.get_and_display_bbc3, meta_data_url)
        except URLError as err:
            SongDataDisplay.next_update_timer = Globals.loop.call_later(15, SongDataDisplay.get_and_display_bbc3, meta_data_url)
            Utils.log("BBC3 metadata fail. Retrying in 15 secs.")
            Utils.log(str(err))
    
    def get_and_display_kexp(meta_data_url: str):
        req = request.Request(meta_data_url,
        headers={'Accept':'*/*', 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'})
        try:
            with request.urlopen(req) as result:
                data = json.loads(result.read().decode('utf-8'))
                song = data["results"][0]
                time_until_next: int = 60 # TODO fix
                Globals.current_artist = song.get('artist', '---')
                Globals.current_song = song.get('song', '---')
                SongDataDisplay.large_text.text = Utils.truncate(Globals.current_artist, 46)
                SongDataDisplay.small_text.text = Utils.truncate(Globals.current_song, 80)
                DisplayEngine.draw_rect(0, 40, 720, 186)
                y_pos = DisplayEngine.draw_text(SongDataDisplay.large_text)
                SongDataDisplay.small_text.yc = y_pos + 10
                DisplayEngine.draw_text(SongDataDisplay.small_text)
                #Utils.log("KEXP refresh. Next metadata query in 60 secs")
                SongDataDisplay.next_update_timer = Globals.loop.call_later(time_until_next, SongDataDisplay.get_and_display_kexp, meta_data_url)
        except URLError as err:
            SongDataDisplay.next_update_timer = Globals.loop.call_later(15, SongDataDisplay.get_and_display_kexp, meta_data_url)
            Utils.log("KEXP metadata fail. Retrying in 15 secs.")
            Utils.log(str(err))

    def get_and_display_song_data_radio_france(meta_data_url: str):
        '''
        Retrieve and display the current song's data from Radio France.
        Will call itself if there is new data.
        '''
        req = request.Request(meta_data_url)
        try:
            with request.urlopen(req) as result:
                data = json.loads(result.read().decode(result.info().get_param('charset') or 'utf-8'))
                now_list = data["now"]
                #print(str(now_list))
                next_refresh: int = now_list["endTime"] if now_list["endTime"] != None else time.time() + 35
                time_until_next: int = next_refresh - time.time() + 3# in secs. The display update adds a little extra time
                Globals.current_song = now_list["firstLine"]
                Globals.current_artist = now_list["secondLine"]
                SongDataDisplay.large_text.text = Utils.truncate(Globals.current_artist, 30)
                SongDataDisplay.small_text.text = Utils.truncate(Globals.current_song, 140)
                DisplayEngine.draw_rect(0, 40, 720, 186)
                y_pos = DisplayEngine.draw_text(SongDataDisplay.large_text)
                SongDataDisplay.small_text.yc = y_pos + 20
                DisplayEngine.draw_text(SongDataDisplay.small_text)
                time_until_next = 10 if time_until_next < 0 else time_until_next
                #Utils.log("RadioFrance refresh. next metadata query in: " +  str(time_until_next))
                SongDataDisplay.next_update_timer = Globals.loop.call_later(time_until_next, SongDataDisplay.get_and_display_song_data_radio_france, meta_data_url)
        except URLError as err:
            SongDataDisplay.next_update_timer = Globals.loop.call_later(15, SongDataDisplay.get_and_display_song_data_radio_france, meta_data_url)
            Utils.log("RadioFrance metadata fail. Retrying in 15 secs.")
            Utils.log(str(err))
    
    def on_navigated_away():
        if SongDataDisplay.next_update_timer != None:
            SongDataDisplay.next_update_timer.cancel()
