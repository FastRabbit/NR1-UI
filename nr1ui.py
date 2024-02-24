#!/usr/bin/python3

from __future__ import unicode_literals
from luma.oled.device import ssd1322
from luma.core.interface.serial import spi
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
from PIL import ImageDraw
import numpy as np

from ConfigurationFiles.ScreenConfig1322 import *
from ConfigurationFiles.PreConfiguration import NowPlayingLayout, SpectrumActive
from ConfigurationFiles.PreConfiguration import ENCODER_LEFT_IO, ENCODER_RIGHT_IO, ENCODER_BUTTON_IO
from ConfigurationFiles.PreConfiguration import oledrotation, oledPause2StopTime


from modules.buttonsleds import update_leds_with_volumio_state
from modules.buttonsleds import check_buttons_and_update_leds
from modules.display1322 import *
from modules.pushbutton import PushButton
from modules.rotaryencoder import RotaryEncoder
from modules.show_gif import show_gif

GPIO.setwarnings(False)

# Socket-IO-Configuration for Rest API
volumio_host = 'localhost'
volumio_port = 3000
volumio_socket_io = SocketIO(volumio_host, volumio_port)

# Logic to prevent freeze if FIFO-Out for Cava is missing:
ReNewMPDconf = {'endpoint': 'music_service/mpd', 'method': 'createMPDFile', 'data': ''}
if SpectrumActive is True:
    with open('/etc/mpd.conf') as f1:
        if '/tmp/mpd.fifo' in f1.read():
            print("CAVA1 Fifo-Output is present in mpd.conf")
        else:
            print('CAVA1 FIFO-Output in /etc/mpd.conf is missing!')
            print('Rebuilding mpd.conf now, this will take ~5 seconds.')
            volumio_socket_io.emit('callMethod', ReNewMPDconf)
            sleep(5.0)
        if '/tmp/mpd2.fifo' in f1.read():
            print("CAVA2 Fifo-Output is present in mpd.conf")
        else:
            print('CAVA2 FIFO-Output in /etc/mpd.conf is missing!')
            print('Rebuilding mpd.conf now, this will take ~5 seconds.')
            volumio_socket_io.emit('callMethod', ReNewMPDconf)
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


STATE_NONE = -1
STATE_PLAYER = 0
STATE_QUEUE_MENU = 1
STATE_LIBRARY_INFO = 2
STATE_SCREEN_MENU = 3

UPDATE_INTERVAL = 0.034

oled = ssd1322(spi(device=0, port=0), rotate=oledrotation)
oled.WIDTH = 256
oled.HEIGHT = 64

oled.state = 'stop'
oled.stateTimeout = 0
oled.playstateIcon = ''
oled.timeOutRunning = False
oled.activeSong = ''
oled.activeArtist = 'VOLuMIO'
oled.playState = 'unknown'
oled.playPosition = 0
oled.seek = 1000
oled.duration = 1.0
oled.modal = None
oled.queue = []
oled.volume = 100
oled.time = datetime.now().strftime("%H:%M")
emit_track = False
newStatus = 0  # makes newStatus usable outside of onPushState
oled.activeFormat = ''  # makes oled.activeFormat globaly usable
oled.activeSamplerate = ''  # makes oled.activeSamplerate globaly usable
oled.activeBitdepth = ''  # makes oled.activeBitdepth globaly usable
oled.activeArtists = ''  # makes oled.activeArtists globaly usable
oled.activeAlbums = ''  # makes oled.activeAlbums globaly usable
oled.activeAlbum = ''
oled.activeSongs = ''  # makes oled.activeSongs globaly usable
oled.activePlaytime = ''  # makes oled.activePlaytime globaly usable
oled.ShutdownFlag = False  # helper to detect if "shutdown" is running. Prevents artifacts from Standby-Screen during shutdown
varcanc = True  # helper for pause -> stop timeout counter
secvar = 0.0
oled.SelectedScreen = NowPlayingLayout
oled.fallingL = False
oled.fallingR = False
oled.prevFallingTimerL = 0
oled.prevFallingTimerR = 0
ScrollArtistTag = 0
ScrollArtistNext = 0
ScrollArtistFirstRound = True
ScrollArtistNextRound = False
ScrollSongTag = 0
ScrollSongNext = 0
ScrollSongFirstRound = True
ScrollSongNextRound = False
ScrollAlbumTag = 0
ScrollAlbumNext = 0
ScrollAlbumFirstRound = True
ScrollAlbumNextRound = False
ScrollSpecsTag = 0
ScrollSpecsNext = 0
ScrollSpecsFirstRound = True
ScrollSpecsNextRound = False
oled.selQueue = ''
oled.repeat = False
oled.bitrate = ''
oled.repeatonce = False
oled.shuffle = False
oled.mute = False
oled.ScreenTimer10 = False
oled.ScreenTimer20 = False
oled.ScreenTimerStamp = 0.0
oled.ScreenTimerStart = True
oled.ScreenTimerChangeTime = 10.0

image = Image.new('RGB', (oled.WIDTH, oled.HEIGHT))  # for Pixelshift: (oled.WIDTH + 4, oled.HEIGHT + 4))

oled.clear()

font = load_font('NotoSansTC-Bold.otf', 18)  # used for Artist
font2 = load_font('NotoSansTC-Light.otf', 12)  # used for all menus
font14 = load_font('NotoSansTC-Light.otf', 12)  # used for Artist
font3 = load_font('NotoSansTC-Regular.otf', 16)  # used for Song
font4 = load_font('Oxanium-Medium.ttf', 12)  # used for Format/Smplerate/Bitdepth
font6 = load_font('NotoSansTC-Regular.otf', 12)  # used for Song / Screen5
font7 = load_font('Oxanium-Light.ttf', 10)  # used for all other / Screen5
font8 = load_font('NotoSansTC-Regular.otf', 10)  # used for Song / Screen5
font11 = load_font('Oxanium-Regular.ttf', 10)  # used for specs in VUmeter2
font13 = load_font('NotoSansTC-Regular.otf', 14)  # used for Artist
mediaicon = load_font('fa-solid-900.ttf', 10)  # used for icon in Media-library info
labelfont = load_font('entypo.ttf', 12)  # used for Menu-icons
iconfontBottom = load_font('entypo.ttf', 10)  # used for icons under the screen / button layout
labelfontfa = load_font('fa-solid-900.ttf', 12)  # used for icons under the screen / button layout
fontClock = load_font('DSG.ttf', 45)  # used for clock



from screen_menu import ScreenMenue
from screen_library import ScreenMediaLibraryInfo
from screen_select_menu import ScreenSelectMenu, ScreenList
from screen_playing import ScreenNowPlaying



def display_update_service():
    while UPDATE_INTERVAL > 0 and oled.ShutdownFlag is False:
        # Felix: check me
        prevTime = time()
        dt = time() - prevTime
        if oled.stateTimeout > 0:
            oled.timeOutRunning = True
            oled.stateTimeout -= dt
        elif oled.stateTimeout <= 0 and oled.timeOutRunning:
            oled.timeOutRunning = False
            oled.stateTimeout = 0
            SetState(STATE_PLAYER)
        image.paste("black", [0, 0, image.size[0], image.size[1]])
        try:
            oled.modal.DrawOn(image)
        except AttributeError:
            print("render error")
            sleep(1)
        oled.display(image.crop((0, 0, oled.WIDTH, oled.HEIGHT)))
        sleep(UPDATE_INTERVAL)


def SetState(state):
    oled.state = state
    if oled.state == STATE_PLAYER:
        oled.modal = ScreenNowPlaying(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_QUEUE_MENU:
        oled.modal = ScreenMenue(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_LIBRARY_INFO:
        oled.modal = ScreenMediaLibraryInfo(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_SCREEN_MENU:
        oled.modal = ScreenSelectMenu(oled.HEIGHT, oled.WIDTH)


def onPushState(data):
    if oled.state != STATE_SCREEN_MENU:
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
        global ScrollAlbumTag
        global ScrollAlbumNext
        global ScrollAlbumFirstRound
        global ScrollAlbumNextRound
        global ScrollSpecsTag
        global ScrollSpecsNext
        global ScrollSpecsFirstRound
        global ScrollSpecsNextRound
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
            oled.activeFormat = newFormat
        else:
            newFormat = ''
        if newFormat is None:
            newFormat = ''
        if newFormat is True and newSong != 'HiFiBerry ADC':
            newFormat = 'WebRadio'
            oled.activeFormat = newFormat
        if newFormat is True and newSong == 'HiFiBerry ADC':
            newFormat = 'Live-Stream'
            oled.activeFormat = newFormat

        if 'samplerate' in data:
            newSamplerate = data['samplerate']
            oled.activeSamplerate = newSamplerate
        else:
            newSamplerate = ' '
            oled.activeSamplerate = newSamplerate
        if newSamplerate is None:
            newSamplerate = ' '
            oled.activeSamplerate = newSamplerate

        if 'bitrate' in data:
            oled.bitrate = data['bitrate']
        else:
            bitrate = ''
        if oled.bitrate is None:
            oled.bitrate = ''

        if 'bitdepth' in data:
            newBitdepth = data['bitdepth']
            oled.activeBitdepth = newBitdepth
        else:
            newBitdepth = ' '
            oled.activeBitdepth = newBitdepth
        if newBitdepth is None:
            newBitdepth = ' '
            oled.activeBitdepth = newBitdepth

        if 'position' in data:                      # current position in queue
            oled.playPosition = data['position']    # didn't work well with volumio ver. < 2.5
        else:
            oled.playPosition = None

        if 'status' in data:
            newStatus = data['status']

#        if 'volume' in data:            #get volume on startup and remote control
#            oled.volume = int(data['volume'])
#        else:
#            oled.volume = 100

        if 'repeat' in data:
            oled.repeat = data['repeat']

        if 'repeatSingle' in data:
            oled.repeatonce = data['repeatSingle']

        if 'random' in data:
            oled.shuffle = data['random']

        if 'mute' in data:
            oled.mute = data['mute']

        if 'duration' in data:
            oled.duration = data['duration']
        else:
            oled.duration = None
        if oled.duration == int(0):
            oled.duration = None

        if 'seek' in data:
            oled.seek = data['seek']
        else:
            oled.seek = None

        if 'album' in data:
            newAlbum = data['album']
        else:
            newAlbum = None
            if newAlbum is None:
                newAlbum = 'No Album'
            if newAlbum == '':
                newAlbum = 'No Album'

        if (newSong != oled.activeSong) or (newArtist != oled.activeArtist) or (newAlbum != oled.activeAlbum):                                # new song and artist
            oled.activeSong = newSong
            oled.activeArtist = newArtist
            oled.activeAlbum = newAlbum
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
            ScrollAlbumTag = 0
            ScrollAlbumNext = 0
            ScrollAlbumFirstRound = True
            ScrollAlbumNextRound = False
            ScrollSpecsTag = 0
            ScrollSpecsNext = 0
            ScrollSpecsFirstRound = True
            ScrollSpecsNextRound = False

        if newStatus != oled.playState:
            varcanc = True  # helper for pause -> stop timeout counter
            secvar = 0.0
            oled.playState = newStatus
            if oled.state == STATE_PLAYER:
                if oled.playState != 'stop':
                    if newStatus == 'pause':
                        oled.playstateIcon = oledpauseIcon
                    if newStatus == 'play':
                        oled.playstateIcon = oledplayIcon
                    oled.modal.UpdatePlayingInfo()
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
                    oled.modal.UpdateStandbyInfo()


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

    oled.activeArtists = str(newArtists)
    oled.activeAlbums = str(newAlbums)
    oled.activeSongs = str(newSongs)
    oled.activePlaytime = str(newPlaytime)

    if oled.state == STATE_LIBRARY_INFO and oled.playState == 'info':  # this is the "Media-Library-Info-Screen"
        oled.modal.UpdateLibraryInfo()


def onPushQueue(data):
    oled.queue = [track['name'] if 'name' in track else 'no track' for track in data]


def ButtonC_PushEvent():
    print('ButtonC short press event')
    if oled.state == STATE_PLAYER and oled.playState == 'stop':
        print('RightKnob_PushEvent SHORT')
        SetState(STATE_SCREEN_MENU)
        sleep(0.2)
    pass


def ButtonD_PushEvent():
    print('ButtonD short press event')
    if oled.state == STATE_PLAYER and oled.playState == 'stop':
        b_obj = BytesIO()
        crl = Curl()
        crl.setopt(crl.URL, 'localhost:3000/api/v1/collectionstats')
        crl.setopt(crl.WRITEDATA, b_obj)
        crl.perform()
        crl.close()
        get_body = b_obj.getvalue()
        print('getBody', get_body)
        SetState(STATE_LIBRARY_INFO)
        oled.playState = 'info'
        onPushCollectionStats(get_body)
        sleep(0.5)
    elif oled.state == STATE_LIBRARY_INFO:
        SetState(STATE_PLAYER)


button_action_map = {
    'ButtonD': ButtonD_PushEvent,
    'ButtonC': ButtonC_PushEvent,
}


def RightKnob_RotaryEvent(dir):
    global emit_track
    oled.stateTimeout = 6.0
    print(f"RightKnob_RotaryEvent State: {oled.state}")
    if oled.state == STATE_PLAYER:
        SetState(STATE_QUEUE_MENU)
    elif oled.state == STATE_QUEUE_MENU and dir == RotaryEncoder.LEFT:
        oled.modal.PrevOption()
        oled.selQueue = oled.modal.SelectedOption()
        emit_track = True
    elif oled.state == STATE_QUEUE_MENU and dir == RotaryEncoder.RIGHT:
        oled.modal.NextOption()
        oled.selQueue = oled.modal.SelectedOption()
        emit_track = True
    elif oled.state == STATE_SCREEN_MENU and dir == RotaryEncoder.LEFT:
        print('leftdir Rotary')
        oled.modal.PrevOption()
        oled.SelectedScreen = oled.modal.SelectedOption()
    elif oled.state == STATE_SCREEN_MENU and dir == RotaryEncoder.RIGHT:
        oled.modal.NextOption()
        oled.SelectedScreen = oled.modal.SelectedOption()


def RightKnob_PushEvent(hold_time):
    if hold_time < 1:
        if oled.state == STATE_QUEUE_MENU:
            print('RightKnob_PushEvent SHORT')
            oled.stateTimeout = 0
        if oled.state == STATE_SCREEN_MENU:
            print('RightKnob_PushEvent Long')
            global NowPlayingLayout
            oled.SelectedScreen = oled.modal.SelectedOption()
            Screen = ScreenList[oled.SelectedScreen]
            WriteSelScreen = open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'w')
            WriteSelScreen.write(Screen)
            WriteSelScreen.close
            NowPlayingLayout = Screen
            SetState(STATE_PLAYER)
            volumio_socket_io.emit('stop')


RightKnob_Push = PushButton(ENCODER_BUTTON_IO, max_time=2)
RightKnob_Push.setCallback(RightKnob_PushEvent)
RightKnob_Rotation = RotaryEncoder(ENCODER_LEFT_IO, ENCODER_RIGHT_IO, pulses_per_cycle=4)
RightKnob_Rotation.setCallback(RightKnob_RotaryEvent)


boot_logo_path = "/home/volumio/NR1-UI/img/bootlogo.gif"
show_gif(oled, boot_logo_path, display_time=2, frame_duration=0.02)

loading_logo_path = "/home/volumio/NR1-UI/img/loading.gif"
show_gif(oled, loading_logo_path, display_time=2, frame_duration=0.02)


sleep(5)
SetState(STATE_PLAYER)

updateThread = Thread(target=display_update_service)
updateThread.daemon = True
updateThread.start()


def _receive_thread():
    volumio_socket_io.wait()


receive_thread = Thread(target=_receive_thread)
receive_thread.daemon = True
receive_thread.start()

volumio_socket_io.on('pushState', onPushState)
volumio_socket_io.on('pushQueue', onPushQueue)

# get list of Playlists and initial state
volumio_socket_io.emit('listPlaylist')
volumio_socket_io.emit('getState')
volumio_socket_io.emit('getQueue')

sleep(0.1)

try:
    # load last playing track number
    with open('oledConfigurationFiles.json', 'r') as f:
        config = json.load(f)
except IOError:
    pass
else:
    oled.playPosition = config['track']

# helper for missing Artist/Song when changing sources
# Felx: check for delet
InfoTag = 0


def PlaypositionHelper():
    while True:
        volumio_socket_io.emit('getState')
        oled.date = datetime.now().strftime("%d.%m.%Y")
        sleep(1.0)


PlayPosHelp = Thread(target=PlaypositionHelper, daemon=True)
PlayPosHelp.start()

while True:

    update_leds_with_volumio_state()
    check_buttons_and_update_leds(ButtonC_PushEvent)

    if emit_track and oled.stateTimeout < 4.5:
        emit_track = False
        try:
            SetState(STATE_PLAYER)
            InfoTag = 0
        except IndexError:
            pass
        volumio_socket_io.emit('stop')
        sleep(0.01)
        volumio_socket_io.emit('play', {'value': oled.selQueue})
    sleep(0.1)

    if oled.state == STATE_PLAYER:

        # this is the loop to push the actual time every 0.1sec to the "Standby-Screen"
        if newStatus == 'stop' and oled.ShutdownFlag is False:
            InfoTag = 0  # resets the InfoTag helper from artist/song update loop
            oled.time = datetime.now().strftime("%H:%M")
            SetState(STATE_PLAYER)
            oled.modal.UpdateStandbyInfo()
            sleep(0.2)

        # if playback is paused, here is defined when the Player goes back to "Standby"/Stop
        if newStatus == 'pause' and varcanc is True:
            secvar = int(round(time()))
            varcanc = False
        elif newStatus == 'pause' and int(round(time())) - secvar > oledPause2StopTime:
            varcanc = True
            volumio_socket_io.emit('stop')
            oled.modal.UpdateStandbyInfo()
            secvar = 0.0

        if newStatus == 'play' and oled.ScreenTimerStart is True:
            oled.ScreenTimerStamp = int(round(time()))
            oled.ScreenTimerStart = False
            oled.ScreenTimer10 = True

        if newStatus != 'stop':
            if oled.ScreenTimer10 is True and (int(round(time())) - oled.ScreenTimerStamp > oled.ScreenTimerChangeTime):
                oled.ScreenTimerChangeTime
                oled.ScreenTimer10 = False
                oled.ScreenTimer20 = True
            if oled.ScreenTimer20 is True and ((int(round(time())) - oled.ScreenTimerStamp) > (oled.ScreenTimerChangeTime * 2)):
                oled.ScreenTimer20 = False
                oled.ScreenTimerStart = True
                oled.ScreenTimerStamp = 0.0
                oled.ScreenTimer10 = True

        if oled.state != STATE_PLAYER:
            oled.ScreenTimer10 = False
            oled.ScreenTimer20 = False
            oled.ScreenTimerStart = True
            oled.ScreenTimerStamp = 0.0

    sleep(0.02)
