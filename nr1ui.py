#!/usr/bin/python3

from __future__ import unicode_literals
import requests
import json
from pycurl import Curl
import RPi.GPIO as GPIO
from time import *
from threading import Thread
from socketIO_client import SocketIO
from datetime import datetime as datetime
from io import BytesIO
from PIL import Image

from display import *

from ConfigurationFiles.ScreenConfig1322 import *
from ConfigurationFiles.PreConfiguration import NowPlayingLayout, SpectrumActive
from ConfigurationFiles.PreConfiguration import ENCODER_LEFT_IO, ENCODER_RIGHT_IO, ENCODER_BUTTON_IO
from ConfigurationFiles.PreConfiguration import oledPause2StopTime


from modules.buttonsleds import update_leds_with_volumio_state, check_buttons_and_update_leds
from modules.display1322 import *
from modules.pushbutton import PushButton
from modules.rotaryencoder import RotaryEncoder
from modules.show_gif import show_gif

GPIO.setwarnings(False)

# Socket-IO-Configuration for Rest API
volumio_host = 'localhost'
volumio_port = 3000
volumioIO = SocketIO(volumio_host, volumio_port)


# Logic to prevent freeze if FIFO-Out for Cava is missing:
ReNewMPDconf = {'endpoint': 'music_service/mpd', 'method': 'createMPDFile', 'data': ''}
if SpectrumActive is True:
    with open('/etc/mpd.conf') as f1:
        if '/tmp/mpd.fifo' in f1.read():
            print("CAVA1 Fifo-Output is present in mpd.conf")
        else:
            print('CAVA1 FIFO-Output in /etc/mpd.conf is missing!')
            print('Rebuilding mpd.conf now, this will take ~5 seconds.')
            volumioIO.emit('callMethod', ReNewMPDconf)
            sleep(5.0)
        if '/tmp/mpd2.fifo' in f1.read():
            print("CAVA2 Fifo-Output is present in mpd.conf")
        else:
            print('CAVA2 FIFO-Output in /etc/mpd.conf is missing!')
            print('Rebuilding mpd.conf now, this will take ~5 seconds.')
            volumioIO.emit('callMethod', ReNewMPDconf)
            sleep(5.0)


with open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'r') as file:
    NowPlayingLayoutSave = file.readline().rstrip()
print('Layout selected during setup: ', NowPlayingLayout)
print('Last manually selected Layout: ', NowPlayingLayoutSave)

if NowPlayingLayout not in ScreenList:
    with open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'w') as file:
        file.write('No-Spectrum')
    NowPlayingLayout = 'No-Spectrum'

if NowPlayingLayoutSave != NowPlayingLayout:
    if NowPlayingLayoutSave not in ScreenList and SpectrumActive is False:
        with open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'w') as file:
            file.write('No-Spectrum')
        NowPlayingLayout = 'No-Spectrum'
    else:
        NowPlayingLayout = NowPlayingLayoutSave

display.SelectedScreen = NowPlayingLayout

STATE_NONE = -1
STATE_PLAYER = 0
STATE_QUEUE_MENU = 1
STATE_LIBRARY_INFO = 2
STATE_SCREEN_MENU = 3

UPDATE_INTERVAL = 0.034

image = Image.new('RGB', (display.WIDTH, display.HEIGHT))  # for Pixelshift: (display.WIDTH + 4, display.HEIGHT + 4))

display.clear()


from screen_menu import ScreenMenue
from screen_library import ScreenMediaLibraryInfo
from screen_select_menu import ScreenSelectMenu, ScreenList
from screen_playing import ScreenNowPlaying



def display_update_service():
    while UPDATE_INTERVAL > 0 and display.ShutdownFlag is False:
        # Felix: check me
        prevTime = time()
        dt = time() - prevTime
        if display.stateTimeout > 0:
            display.timeOutRunning = True
            display.stateTimeout -= dt
        elif display.stateTimeout <= 0 and display.timeOutRunning:
            display.timeOutRunning = False
            display.stateTimeout = 0
            SetState(STATE_PLAYER)
        image.paste("black", [0, 0, image.size[0], image.size[1]])
        try:
            display.modal.DrawOn(image)
        except AttributeError:
            print(f"render error in state {display.state}")
            sleep(1)
        display.display(image.crop((0, 0, display.WIDTH, display.HEIGHT)))
        sleep(UPDATE_INTERVAL)


def SetState(state):
    display.state = state
    if display.state == STATE_PLAYER:
        display.modal = ScreenNowPlaying(display.HEIGHT, display.WIDTH)
    elif display.state == STATE_QUEUE_MENU:
        display.modal = ScreenMenue(display.HEIGHT, display.WIDTH)
    elif display.state == STATE_LIBRARY_INFO:
        display.modal = ScreenMediaLibraryInfo(display.HEIGHT, display.WIDTH)
    elif display.state == STATE_SCREEN_MENU:
        display.modal = ScreenSelectMenu(display.HEIGHT, display.WIDTH)


def onPushState(data):
    if display.state != STATE_SCREEN_MENU:
        global OPDsave
        global newStatus  # global definition for newStatus, used at the end-loop to update standby
        global newSong
        global newArtist
        global newFormat
        global varcanc
        global secvar
        global ScrollArtistTag
        global ScrollArtistNext
        global ScrollArtistFirstRound
        global ScrollArtistNextRound
        global ScrollSongTag
        global ScrollSongNext
        global ScrollSongFirstRound
        global ScrollSongNextRound
        OPDsave = data
        # print('data: ', str(data).encode('utf-8'))

        if 'title' in data:
            newSong = data['title']
        else:
            newSong = ''
        if newSong is None:
            newSong = ''
        if newSong == 'HiFiBerry ADC':
            newSong = 'Bluetooth-Audio'

        if 'artist' in data:
            newArtist = data['artist']
        else:
            newArtist = ''
        if newArtist is None and newSong != 'HiFiBerry ADC':  # volumio can push NoneType
            newArtist = ''
        if newArtist == '' and newSong == 'HiFiBerry ADC':
            newArtist = 'Line-Input:'

        if 'trackType' in data:
            newFormat = data['trackType']
            display.activeFormat = newFormat
        else:
            newFormat = ''
        if newFormat is None:
            newFormat = ''
        if newFormat is True and newSong != 'HiFiBerry ADC':
            newFormat = 'WebRadio'
            display.activeFormat = newFormat
        if newFormat is True and newSong == 'HiFiBerry ADC':
            newFormat = 'Live-Stream'
            display.activeFormat = newFormat

        if 'samplerate' in data:
            newSamplerate = data['samplerate']
            display.activeSamplerate = newSamplerate
        else:
            newSamplerate = ' '
            display.activeSamplerate = newSamplerate
        if newSamplerate is None:
            newSamplerate = ' '
            display.activeSamplerate = newSamplerate

        if 'bitrate' in data:
            display.bitrate = data['bitrate']
        else:
            bitrate = ''
        if display.bitrate is None:
            display.bitrate = ''

        if 'bitdepth' in data:
            newBitdepth = data['bitdepth']
            display.activeBitdepth = newBitdepth
        else:
            newBitdepth = ' '
            display.activeBitdepth = newBitdepth
        if newBitdepth is None:
            newBitdepth = ' '
            display.activeBitdepth = newBitdepth

        if 'position' in data:                      # current position in queue
            display.playPosition = data['position']    # didn't work well with volumio ver. < 2.5
        else:
            display.playPosition = None

        if 'status' in data:
            newStatus = data['status']

#        if 'volume' in data:            #get volume on startup and remote control
#            display.volume = int(data['volume'])
#        else:
#            display.volume = 100

        if 'repeat' in data:
            display.repeat = data['repeat']

        if 'repeatSingle' in data:
            display.repeatonce = data['repeatSingle']

        if 'random' in data:
            display.shuffle = data['random']

        if 'mute' in data:
            display.mute = data['mute']

        if 'duration' in data:
            display.duration = data['duration']
        else:
            display.duration = None
        if display.duration == int(0):
            display.duration = None

        if 'seek' in data:
            display.seek = data['seek']
        else:
            display.seek = None

        if 'album' in data:
            newAlbum = data['album']
        else:
            newAlbum = None
            if newAlbum is None:
                newAlbum = 'No Album'
            if newAlbum == '':
                newAlbum = 'No Album'

        if (newSong != display.activeSong) or (newArtist != display.activeArtist) or (newAlbum != display.activeAlbum):                                # new song and artist
            display.activeSong = newSong
            display.activeArtist = newArtist
            display.activeAlbum = newAlbum
            varcanc = True  # helper for pause -> stop timeout counter
            secvar = 0.0
            ScrollArtistTag = 0
            ScrollArtistNext = 0
            ScrollArtistFirstRound = True
            ScrollArtistNextRound = False
            ScrollSongTag = 0
            ScrollSongNext = 0
            ScrollSongFirstRound = True
            ScrollSongNextRound = False

        if newStatus != display.playState:
            varcanc = True  # helper for pause -> stop timeout counter
            secvar = 0.0
            display.playState = newStatus
            if display.state == STATE_PLAYER:
                if display.playState != 'stop':
                    if newStatus == 'pause':
                        display.playstateIcon = oledpauseIcon
                    if newStatus == 'play':
                        display.playstateIcon = oledplayIcon
                    display.modal.UpdatePlayingInfo()
                else:
                    ScrollArtistTag = 0
                    ScrollArtistNext = 0
                    ScrollArtistFirstRound = True
                    ScrollArtistNextRound = False
                    ScrollSongTag = 0
                    ScrollSongNext = 0
                    ScrollSongFirstRound = True
                    ScrollSongNextRound = False
                    SetState(STATE_PLAYER)
                    display.modal.UpdateStandbyInfo()


def onPushCollectionStats(data):
    data = json.loads(data.decode("utf-8"))  # data import from REST-API (is set when ButtonD short-pressed in Standby)

    if "artists" in data:  # used for Media-Library-Infoscreen
        newArtists = data["artists"]
    else:
        newArtists = ''
    if newArtists is None:
        newArtists = ''

    if 'albums' in data:  # used for Media-Library-Infoscreen
        newAlbums = data["albums"]
    else:
        newAlbums = ''
    if newAlbums is None:
        newAlbums = ''

    if 'songs' in data:  # used for Media-Library-Infoscreen
        newSongs = data["songs"]
    else:
        newSongs = ''
    if newSongs is None:
        newSongs = ''

    if 'playtime' in data:  # used for Media-Library-Infoscreen
        newPlaytime = data["playtime"]
    else:
        newPlaytime = ''
    if newPlaytime is None:
        newPlaytime = ''

    display.activeArtists = str(newArtists)
    display.activeAlbums = str(newAlbums)
    display.activeSongs = str(newSongs)
    display.activePlaytime = str(newPlaytime)

    if display.state == STATE_LIBRARY_INFO and display.playState == 'info':  # this is the "Media-Library-Info-Screen"
        display.modal.UpdateLibraryInfo()


def onPushQueue(data):
    display.queue = [track['name'] if 'name' in track else 'no track' for track in data]


def RightKnob_RotaryEvent(dir):
    global emit_track
    display.stateTimeout = 6.0
    print(f"RightKnob_RotaryEvent State: {display.state}")
    if display.state == STATE_PLAYER:
        SetState(STATE_QUEUE_MENU)
    elif display.state == STATE_QUEUE_MENU and dir == RotaryEncoder.LEFT:
        display.modal.PrevOption()
        display.selQueue = display.modal.SelectedOption()
        emit_track = True
    elif display.state == STATE_QUEUE_MENU and dir == RotaryEncoder.RIGHT:
        display.modal.NextOption()
        display.selQueue = display.modal.SelectedOption()
        emit_track = True
    elif display.state == STATE_SCREEN_MENU and dir == RotaryEncoder.LEFT:
        print('leftdir Rotary')
        display.modal.PrevOption()
        display.SelectedScreen = display.modal.SelectedOption()
    elif display.state == STATE_SCREEN_MENU and dir == RotaryEncoder.RIGHT:
        display.modal.NextOption()
        display.SelectedScreen = display.modal.SelectedOption()


def RightKnob_PushEvent(hold_time):
    if hold_time < 1:
        if display.state == STATE_QUEUE_MENU:
            print('RightKnob_PushEvent SHORT')
            display.stateTimeout = 0
        if display.state == STATE_SCREEN_MENU:
            print('RightKnob_PushEvent Long')
            global NowPlayingLayout
            display.SelectedScreen = display.modal.SelectedOption()
            Screen = ScreenList[display.SelectedScreen]
            print(f"changed screen to {Screen}")
            WriteSelScreen = open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'w')
            WriteSelScreen.write(Screen)
            WriteSelScreen.close
            NowPlayingLayout = Screen
            display.SelectedScreen = Screen
            SetState(STATE_PLAYER)
            volumioIO.emit('stop')


RightKnob_Push = PushButton(ENCODER_BUTTON_IO, max_time=2)
RightKnob_Push.setCallback(RightKnob_PushEvent)
RightKnob_Rotation = RotaryEncoder(ENCODER_LEFT_IO, ENCODER_RIGHT_IO, pulses_per_cycle=4)
RightKnob_Rotation.setCallback(RightKnob_RotaryEvent)


boot_logo_path = "/home/volumio/NR1-UI/img/bootlogo.gif"
show_gif(display, boot_logo_path, display_time=2, frame_duration=0.02)

loading_logo_path = "/home/volumio/NR1-UI/img/loading.gif"
show_gif(display, loading_logo_path, display_time=2, frame_duration=0.02)


# sleep(5)
SetState(STATE_PLAYER)

updateThread = Thread(target=display_update_service)
updateThread.daemon = True
updateThread.start()


def _receive_thread():
    volumioIO.wait()


receive_thread = Thread(target=_receive_thread)
receive_thread.daemon = True
receive_thread.start()

volumioIO.on('pushState', onPushState)
volumioIO.on('pushQueue', onPushQueue)

# get list of Playlists and initial state
volumioIO.emit('listPlaylist')
volumioIO.emit('getState')
volumioIO.emit('getQueue')

sleep(0.1)


def PlaypositionHelper():
    while True:
        volumioIO.emit('getState')
        display.date = datetime.now().strftime("%d.%m.%Y")
        sleep(1.0)


PlayPosHelp = Thread(target=PlaypositionHelper, daemon=True)
PlayPosHelp.start()


def activate_play():
    print("Activating play.")
    try:
        volumioIO.emit('play')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Playback started.")


def activate_pause():
    print("Activating pause.")
    try:
        volumioIO.emit('pause')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Playback paused.")


def activate_back():
    print("Activating previous track.")
    try:
        volumioIO.emit('previous')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Track skipped back.")


def activate_forward():
    print("Activating next track.")
    try:
        volumioIO.emit('next')
    except Exception as e:
        print("Error: ", e)
    else:
        print("Track skipped forward.")


def activate_shuffle():
    try:
        volumio_state = get_volumio_state()
        if volumio_state and "random" in volumio_state:
            current_random = volumio_state["random"]
            new_random_mode = not current_random
            volumioIO.emit('setRandom', {'value': new_random_mode})
    except Exception as e:
        print("Error: ", e)
    else:
        print("Random mode toggled.")


def activate_repeat():
    try:
        volumio_state = get_volumio_state()
        if volumio_state and "repeat" in volumio_state:
            current_repeat = volumio_state["repeat"]
            new_repeat_mode = not current_repeat
            volumioIO.emit('setRepeat', {'value': new_repeat_mode})
    except Exception as e:
        print('Error:', e)
    else:
        print('Repeat mode toggled.')


def activate_favourites():
    try:
        volumioIO.emit('playPlaylist', {'name': 'favourites'})
    except Exception as e:
        print("Error: ", e)
    else:
        print("Favourites playlist loaded.")


def ButtonC_PushEvent():
    print('ButtonC short press event')
    if display.state == STATE_PLAYER and display.playState == 'stop':
        print('RightKnob_PushEvent SHORT')
        SetState(STATE_SCREEN_MENU)
        sleep(0.2)
    pass


def ButtonD_PushEvent():
    print('ButtonD short press event')
    if display.state == STATE_PLAYER and display.playState == 'stop':
        b_obj = BytesIO()
        crl = Curl()
        crl.setopt(crl.URL, 'localhost:3000/api/v1/collectionstats')
        crl.setopt(crl.WRITEDATA, b_obj)
        crl.perform()
        crl.close()
        get_body = b_obj.getvalue()
        print('getBody', get_body)
        SetState(STATE_LIBRARY_INFO)
        display.playState = 'info'
        onPushCollectionStats(get_body)
        sleep(0.5)
    elif display.state == STATE_LIBRARY_INFO:
        SetState(STATE_PLAYER)


button_action_map = {
    0: activate_play,
    1: activate_pause,
    2: activate_back,
    3: activate_forward,
    4: activate_shuffle,
    5: activate_repeat,
    6: activate_favourites,
    7: ButtonC_PushEvent,
}


def get_volumio_state():
    try:
        response = requests.get("http://localhost:3000/api/v1/getState")
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error: ", e)
        return None
    else:
        return json.loads(response.text)


while True:

    volumio_state = get_volumio_state()
    update_leds_with_volumio_state(volumio_state)
    check_buttons_and_update_leds(button_action_map)

    if emit_track and display.stateTimeout < 4.5:
        emit_track = False
        try:
            SetState(STATE_PLAYER)
        except IndexError:
            pass
        volumioIO.emit('stop')
        sleep(0.01)
        volumioIO.emit('play', {'value': display.selQueue})
    sleep(0.1)

    if display.state == STATE_PLAYER:

        if newStatus == 'stop' and display.ShutdownFlag is False:
            display.time = datetime.now().strftime("%H:%M")
            SetState(STATE_PLAYER)
            display.modal.UpdateStandbyInfo()
            sleep(0.2)

        if newStatus == 'pause' and varcanc is True:
            secvar = int(round(time()))
            varcanc = False
        elif newStatus == 'pause' and int(round(time())) - secvar > oledPause2StopTime:
            varcanc = True
            volumioIO.emit('stop')
            display.modal.UpdateStandbyInfo()
            secvar = 0.0

        if newStatus == 'play' and display.ScreenTimerStart is True:
            display.ScreenTimerStamp = int(round(time()))
            display.ScreenTimerStart = False
            display.ScreenTimer10 = True

        if newStatus != 'stop':
            if display.ScreenTimer10 is True and (int(round(time())) - display.ScreenTimerStamp > display.ScreenTimerChangeTime):
                display.ScreenTimerChangeTime
                display.ScreenTimer10 = False
                display.ScreenTimer20 = True
            if display.ScreenTimer20 is True and ((int(round(time())) - display.ScreenTimerStamp) > (display.ScreenTimerChangeTime * 2)):
                display.ScreenTimer20 = False
                display.ScreenTimerStart = True
                display.ScreenTimerStamp = 0.0
                display.ScreenTimer10 = True

    if display.state != STATE_PLAYER:
        display.ScreenTimer10 = False
        display.ScreenTimer20 = False
        display.ScreenTimerStart = True
        display.ScreenTimerStamp = 0.0

    sleep(0.02)
