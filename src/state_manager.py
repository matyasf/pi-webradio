from src.globals import Screens, Globals, PlayingState, RadioChannel
from src.song_data_display import SongDataDisplay
from src.bluetooth_menu import BluetoothMenu
from src.radio_player import RadioPlayer
from src.linux_event_processor import LinuxEventProcessor

class StateManager:

    def display_playing_ui():
        '''called on init and menu back'''
        Globals.button1.update_callback_func(StateManager.on_change_channel, Globals.radio_channels[0])
        Globals.button2.update_callback_func(StateManager.on_change_channel, Globals.radio_channels[1])
        Globals.button3.update_callback_func(StateManager.on_change_channel, Globals.radio_channels[2])
        Globals.button4.update_callback_func(StateManager.on_change_channel, Globals.radio_channels[3])
        Globals.current_screen = Screens.SONG_DISPLAY
        BluetoothMenu.on_navigated_away()
        SongDataDisplay.update_playing_display()

    def display_menu():
        '''Called when entering the menu'''
        if Globals.current_screen == Screens.BLUETOOTH_MENU:
            return
        Globals.current_screen = Screens.BLUETOOTH_MENU
        SongDataDisplay.on_navigated_away()
        Globals.button4.update_callback_func(StateManager.display_playing_ui)
        BluetoothMenu.on_enter_menu()

    def on_play_pause():
        '''Called when the play/pause button is pressed'''
        if  Globals.bluetooth.get_connected_device() == None:
            return
        if Globals.playing_state == PlayingState.PLAYING:
            RadioPlayer.stop_radio()
        else:
            RadioPlayer.play_radio()
        if Globals.current_screen == Screens.SONG_DISPLAY:
            SongDataDisplay.update_playing_display()

    def on_bt_device_connected():
        RadioPlayer.play_radio()
        LinuxEventProcessor.on_bt_device_connected()
        if Globals.current_screen == Screens.SONG_DISPLAY:
            SongDataDisplay.update_playing_display()

    def on_bt_device_disconnected():
        RadioPlayer.stop_radio()
        LinuxEventProcessor.on_bt_device_disconnected()
        if Globals.current_screen == Screens.SONG_DISPLAY:
            SongDataDisplay.update_playing_display()

    def on_change_channel(new_channel: RadioChannel):
        if new_channel == Globals.current_channel:
            return
        Globals.current_channel = new_channel
        if  Globals.bluetooth.get_connected_device() == None:
            return
        RadioPlayer.play_radio()
        if Globals.current_screen == Screens.SONG_DISPLAY:
            SongDataDisplay.update_playing_display()