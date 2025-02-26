#!/usr/bin/python3

from __future__ import unicode_literals
import requests
import os
import sys
import time
import threading
import signal
import json
import pycurl
import pprint
import subprocess
import RPi.GPIO as GPIO
from time import*
#from time import sleep
from datetime import timedelta as timedelta
from threading import Thread
from socketIO_client import SocketIO
from datetime import datetime as datetime
from io import BytesIO
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import smbus
from modules.pushbutton import PushButton
from modules.rotaryencoder import RotaryEncoder
from modules.buttonsleds import ButtonC_PushEvent, update_leds_with_volumio_state, check_buttons_and_update_leds, read_button_matrix, control_leds, debounce_button, activate_play, activate_pause, activate_back, activate_forward, activate_shuffle, activate_repeat, activate_favourites, activate_ButtonC
#from modules.button_functions import ButtonC_PushEvent
import uuid
import numpy as np
from ConfigurationFiles.PreConfiguration import*
import urllib.request
from urllib.parse import* #from urllib import*
from urllib.parse import urlparse
from urllib.parse import urlencode
from modules.loading_sequence import show_loading_sequence
from modules.loading_animation import show_loading_gif
from modules.bootlogo import show_boot_logo_gif
import ssl
import re
import fnmatch
sleep(5.0)

GPIO.setwarnings(False)

# Socket-IO-Configuration for Rest API
volumio_host = 'localhost'
volumio_port = 3000
volumioIO = SocketIO(volumio_host, volumio_port)

# Logic to prevent freeze if FIFO-Out for Cava is missing:
ReNewMPDconf = {'endpoint': 'music_service/mpd', 'method': 'createMPDFile', 'data': ''}
if SpectrumActive == True:
    with open('/etc/mpd.conf') as f1:
        if '/tmp/mpd.fifo' in f1.read():
            print("CAVA1 Fifo-Output is present in mpd.conf")
        else:
            print('CAVA1 FIFO-Output in /etc/mpd.conf is missing!')
            print('Rebuilding mpd.conf now, this will take ~5 seconds.')
            volumioIO.emit('callMethod', ReNewMPDconf)
            sleep(4.0)
    
    with open('/etc/mpd.conf') as f2:
        if '/tmp/mpd2.fifo' in f2.read():
            print("CAVA2 Fifo-Output is present in mpd.conf")
        else:
            print('CAVA2 FIFO-Output in /etc/mpd.conf is missing!')
            print('Rebuilding mpd.conf now, this will take ~5 seconds.')
            volumioIO.emit('callMethod', ReNewMPDconf)
            sleep(4.0)
#________________________________________________________________________________________
#	
#   ______            _____                        __  _                 
#  / ____/___  ____  / __(_)___ ___  ___________ _/ /_(_)___  ____     _ 
# / /   / __ \/ __ \/ /_/ / __ `/ / / / ___/ __ `/ __/ / __ \/ __ \   (_)
#/ /___/ /_/ / / / / __/ / /_/ / /_/ / /  / /_/ / /_/ / /_/ / / / /  _   
#\____/\____/_/ /_/_/ /_/\__, /\__,_/_/   \__,_/\__/_/\____/_/ /_/  (_)  
#                       /____/
#
if DisplayTechnology == 'spi1322':
    if SpectrumActive == True:
        ScreenList = ['Spectrum-Center', 'No-Spectrum', 'Modern', 'VU-Meter-2', 'VU-Meter-Bar']
    if SpectrumActive == False:
        ScreenList = ['No-Spectrum']

NowPlayingLayoutSave=open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt').readline().rstrip()
print('Layout selected during setup: ', NowPlayingLayout)
print('Last manually selected Layout: ', NowPlayingLayoutSave)

if DisplayTechnology == 'spi1322':
    if NowPlayingLayout not in ScreenList:
        WriteScreen1 = open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'w')
        WriteScreen1.write('No-Spectrum')
        WriteScreen1.close
        NowPlayingLayout = 'No-Spectrum'

if NowPlayingLayoutSave != NowPlayingLayout:
    if NowPlayingLayoutSave not in ScreenList and SpectrumActive == False:
        if DisplayTechnology == 'spi1322':
            WriteScreen1 = open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'w')
            WriteScreen1.write('No-Spectrum')
            WriteScreen1.close
            NowPlayingLayout = 'No-Spectrum'
    else:
        NowPlayingLayout = NowPlayingLayoutSave

#config for timers:
oledPlayFormatRefreshTime = 1.5
oledPlayFormatRefreshLoopCount = 3
#________________________________________________________________________________________
#________________________________________________________________________________________
#   _____ __             __            __     _____       _ __  _                      
#  / ___// /_____ ______/ /_      ____/ /__  / __(_)___  (_) /_(_)___  ____  _____   _ 
#  \__ \/ __/ __ `/ ___/ __/_____/ __  / _ \/ /_/ / __ \/ / __/ / __ \/ __ \/ ___/  (_)
# ___/ / /_/ /_/ / /  / /_/_____/ /_/ /  __/ __/ / / / / / /_/ / /_/ / / / (__  )  _   
#/____/\__/\__,_/_/   \__/      \__,_/\___/_/ /_/_/ /_/_/\__/_/\____/_/ /_/____/  (_)  
#     
0
firstStart = True

if DisplayTechnology == 'spi1322':
   from luma.core.interface.serial import spi
   from luma.oled.device import ssd1322
   from modules.display1322 import*
   from ConfigurationFiles.ScreenConfig1322 import*

b_obj = BytesIO() 
crl = pycurl.Curl() 

STATE_NONE = -1
STATE_PLAYER = 0
STATE_QUEUE_MENU = 1
STATE_LIBRARY_INFO = 2
STATE_SCREEN_MENU = 3

UPDATE_INTERVAL = 0.034

if DisplayTechnology == 'spi1322' or DisplayTechnology == 'Braun':
    interface = spi(device=0, port=0)
    oled = ssd1322(interface, rotate=oledrotation) 
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
oled.modal = False
oled.playlistoptions = []
oled.queue = []
oled.libraryFull = []
oled.libraryNames = []
oled.volumeControlDisabled = True
oled.volume = 100
now = datetime.now()                       #current date and time
oled.time = now.strftime("%H:%M")       #resolves time as HH:MM:SS eg. 14:33:15
oled.date = ""   #resolves time as dd.mm.YYYY eg. 17.04.2020
oled.IP = ''
emit_track = False
newStatus = 0              				   #makes newStatus usable outside of onPushState
oled.activeFormat = ''      			   #makes oled.activeFormat globaly usable
oled.activeSamplerate = ''  			   #makes oled.activeSamplerate globaly usable
oled.activeBitdepth = ''                   #makes oled.activeBitdepth globaly usable
oled.activeArtists = ''                    #makes oled.activeArtists globaly usable
oled.activeAlbums = ''                     #makes oled.activeAlbums globaly usable
oled.activeAlbum = ''
oled.activeAlbumart = ''
oled.activeSongs = ''                      #makes oled.activeSongs globaly usable
oled.activePlaytime = ''                   #makes oled.activePlaytime globaly usable
oled.randomTag = False                     #helper to detect if "Random/shuffle" is set
oled.repeatTag = False                     #helper to detect if "repeat" is set
oled.ShutdownFlag = False                  #helper to detect if "shutdown" is running. Prevents artifacts from Standby-Screen during shutdown
varcanc = True                      #helper for pause -> stop timeout counter
secvar = 0.0
oled.volume = 100
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
VOLUME_DT = 5
oled.ScreenTimer10 = False
oled.ScreenTimer20 = False
oled.ScreenTimerStamp = 0.0
oled.ScreenTimerStart = True
oled.ScreenTimerChangeTime = 10.0


if DisplayTechnology == 'spi1322':
    image = Image.new('RGB', (oled.WIDTH, oled.HEIGHT))  #for Pixelshift: (oled.WIDTH + 4, oled.HEIGHT + 4)) 
oled.clear()
#________________________________________________________________________________________
#________________________________________________________________________________________
#	
#    ______            __           
#   / ____/___  ____  / /______   _ 
#  / /_  / __ \/ __ \/ __/ ___/  (_)
# / __/ / /_/ / / / / /_(__  )  _   
#/_/    \____/_/ /_/\__/____/  (_)  
#
if DisplayTechnology == 'spi1322': 
    font = load_font('NotoSansTC-Bold.otf', 18)                       #used for Artist ('Oxanium-Bold.ttf', 20)  
    font2 = load_font('NotoSansTC-Light.otf', 12)                     #used for all menus
    font3 = load_font('NotoSansTC-Regular.otf', 16)                   #used for Song ('Oxanium-Regular.ttf', 18) 
    font4 = load_font('Oxanium-Medium.ttf', 12)                       #used for Format/Smplerate/Bitdepth
    font5 = load_font('NotoSansTC-Medium.otf', 12)                    #used for Artist / Screen5
    font6 = load_font('NotoSansTC-Regular.otf', 12)                   #used for Song / Screen5
    font7 = load_font('Oxanium-Light.ttf', 10)                        #used for all other / Screen5
    font8 = load_font('NotoSansTC-Regular.otf', 10)                   #used for Song / Screen5
    font9 = load_font('NotoSansTC-Bold.otf', 16)                      #used for Artist ('Oxanium-Bold.ttf', 20)  
    font10 = load_font('NotoSansTC-Regular.otf', 14)                  #used for Artist ('Oxanium-Bold.ttf', 20)  
    font11 = load_font('Oxanium-Regular.ttf', 10)                     #used for specs in VUmeter2
    font12 = load_font('Oxanium-Regular.ttf', 12)                     #used for Artist/Song VU Meter2
    font13 = load_font('NotoSansTC-Regular.otf', 14)                      #used for Artist ('Oxanium-Bold.ttf', 20)  
    font14 = load_font('NotoSansTC-Light.otf', 12)                  #used for Artist ('Oxanium-Bold.ttf', 20)  
    mediaicon = load_font('fa-solid-900.ttf', 10)    	              #used for icon in Media-library info
    labelfont = load_font('entypo.ttf', 12)                           #used for Menu-icons
    iconfontBottom = load_font('entypo.ttf', 10)                      #used for icons under the screen / button layout
    labelfontfa = load_font('fa-solid-900.ttf', 12)                   #used for icons under the screen / button layout
    labelfontfa2 = load_font('fa-solid-900.ttf', 14)
    fontClock = load_font('DSG.ttf', 45)                              #used for clock
    fontDate = load_font('Oxanium-Light.ttf', 12)                  #used for Date 'DSEG7Classic-Regular.ttf'
    fontIP = load_font('Oxanium-Light.ttf', 12)                    #used for IP 'DSEG7Classic-Regular.ttf'

#________________________________________________________________________________________
#________________________________________________________________________________________
#    ____  _            __                  __  __          __      __           
#   / __ \(_)________  / /___ ___  __      / / / /___  ____/ /___ _/ /____     _ 
#  / / / / / ___/ __ \/ / __ `/ / / /_____/ / / / __ \/ __  / __ `/ __/ _ \   (_)
# / /_/ / (__  ) /_/ / / /_/ / /_/ /_____/ /_/ / /_/ / /_/ / /_/ / /_/  __/  _   
#/_____/_/____/ .___/_/\__,_/\__, /      \____/ .___/\__,_/\__,_/\__/\___/  (_)  
#            /_/            /____/           /_/                                 
#
def display_update_service():
    while UPDATE_INTERVAL > 0 and oled.ShutdownFlag == False:
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
        cimg = image.crop((0, 0, oled.WIDTH, oled.HEIGHT)) 
        oled.display(cimg)
        sleep(UPDATE_INTERVAL)
#________________________________________________________________________________________
#________________________________________________________________________________________
#
#   ____  __      _           __ _           
#  / __ \/ /_    (_)__  _____/ /( )_____   _ 
# / / / / __ \  / / _ \/ ___/ __/// ___/  (_)
#/ /_/ / /_/ / / /  __/ /__/ /_  (__  )  _   
#\____/_.___/_/ /\___/\___/\__/ /____/  (_)  
#          /___/                             
#
def SetState(status):
    oled.state = status
    if oled.state == STATE_PLAYER:
        oled.modal = NowPlayingScreen(oled.HEIGHT, oled.WIDTH) 
    elif oled.state == STATE_QUEUE_MENU:
        oled.modal = MenuScreen(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_LIBRARY_INFO:
        oled.modal = MediaLibrarayInfo(oled.HEIGHT, oled.WIDTH)
    elif oled.state == STATE_SCREEN_MENU:
        oled.modal = ScreenSelectMenu(oled.HEIGHT, oled.WIDTH)
#________________________________________________________________________________________
#________________________________________________________________________________________
#        
#    ____        __              __  __                ____              
#   / __ \____ _/ /_____ _      / / / /___ _____  ____/ / /__  _____   _ 
#  / / / / __ `/ __/ __ `/_____/ /_/ / __ `/ __ \/ __  / / _ \/ ___/  (_)
# / /_/ / /_/ / /_/ /_/ /_____/ __  / /_/ / / / / /_/ / /  __/ /     _   
#/_____/\__,_/\__/\__,_/     /_/ /_/\__,_/_/ /_/\__,_/_/\___/_/     (_)  
#   
def JPGPathfinder(String):
    print('JPGPathfinder')
    albumstring = String
    global FullJPGPath
    try:
        p1 = 'path=(.+?)&metadata'
        result = re.search(p1, albumstring)
        URL = result.group(1)
        URLPath = "/mnt" + URL + '/'
        accepted_extensions = ['jpg', 'jpeg', 'gif', 'png', 'bmp']
        filenames = [fn for fn in os.listdir(URLPath) if fn.split(".")[-1] in accepted_extensions]
        JPGName = filenames[0]
        FullJPGPath = URLPath + JPGName
    except:
        FullJPGPath = '/home/volumio/NR1-UI/NoCover.bmp'
    JPGSave(FullJPGPath)
    print('FullJPGPath: ', FullJPGPath)

def JPGSave(Path):
    print('JPGSave')
    FullJPGPath = Path
    img = Image.open(FullJPGPath)     # puts our image to the buffer of the PIL.Image object
    width, height = img.size
    asp_rat = width/height
    new_width = 90
    new_height = 90
    new_rat = new_width/new_height
    img = img.resize((new_width, new_height), Image.ANTIALIAS)
    img.save('/home/volumio/album.bmp') 

def JPGSaveURL(link):
    print('JPGSaveURL')
    try:
        httpLink = urllib.parse.quote(link).replace('%3A',':')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(httpLink, context=ctx) as url:
            with open('temp.jpg', 'wb') as f:
                f.write(url.read())
        img = Image.open('temp.jpg')
    except:
        img = Image.open('/home/volumio/NR1-UI/NoCover.bmp')    
    width, height = img.size
    asp_rat = width/height
    new_width = 90
    new_height = 90
    new_rat = new_width/new_height
    img = img.resize((new_width, new_height), Image.ANTIALIAS)
    img.save('/home/volumio/album.bmp') 

def onPushState(data):
    if oled.state != 3:
        global OPDsave	
        global newStatus #global definition for newStatus, used at the end-loop to update standby
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
        #print('data: ', str(data).encode('utf-8'))    
    
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
        if newArtist is None and newSong != 'HiFiBerry ADC':   #volumio can push NoneType
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
        if newFormat == True and newSong != 'HiFiBerry ADC':
            newFormat = 'WebRadio'
            oled.activeFormat = newFormat
        if newFormat == True and newSong == 'HiFiBerry ADC':
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
        if NR1UIRemoteActive == True:
            if 'albumart' in data:
                newAlbumart = data['albumart']
            else:
                newAlbumart = None
            if newAlbumart is None:
                newAlbumart = 'nothing'
            AlbumArtHTTP = newAlbumart.startswith('http')

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
            varcanc = True                      #helper for pause -> stop timeout counter
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
            varcanc = True                      #helper for pause -> stop timeout counter
            secvar = 0.0
            oled.playState = newStatus
            if oled.state == STATE_PLAYER:
                if oled.playState != 'stop':
                    if newStatus == 'pause':
                        if ledActive == True:
                            PlayLEDoff()
                        oled.playstateIcon = oledpauseIcon
                    if newStatus == 'play':
                        if ledActive == True:
                            PlayLEDon()
                        oled.playstateIcon = oledplayIcon
                    oled.modal.UpdatePlayingInfo()
                else:
                    if ledActive == True:
                        PlayLEDoff()
                        StereoLEDoff()
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
        
        if NR1UIRemoteActive == True:
            if newAlbumart != oled.activeAlbumart:
                oled.activeAlbumart = newAlbumart
                if AlbumArtHTTP is True and newFormat == 'WebRadio':
                    JPGSaveURL(newAlbumart)
                else:
                    albumdecode = urllib.parse.unquote(newAlbumart, encoding='utf-8', errors='replace')
                    JPGPathfinder(albumdecode)

def onPushCollectionStats(data):
    data = json.loads(data.decode("utf-8"))             #data import from REST-API (is set when ButtonD short-pressed in Standby)

    if "artists" in data:               #used for Media-Library-Infoscreen
        newArtists = data["artists"]
    else:
        newArtists = ''
    if newArtists is None:
        newArtists = ''

    if 'albums' in data:                #used for Media-Library-Infoscreen
        newAlbums = data["albums"]
    else:
        newAlbums = ''
    if newAlbums is None:
        newAlbums = ''

    if 'songs' in data:                 #used for Media-Library-Infoscreen
        newSongs = data["songs"]
    else:
        newSongs = ''
    if newSongs is None:
        newSongs = ''

    if 'playtime' in data:               #used for Media-Library-Infoscreen
        newPlaytime = data["playtime"]
    else:
        newPlaytime = ''
    if newPlaytime is None:
        newPlaytime = ''

    oled.activeArtists = str(newArtists) 
    oled.activeAlbums = str(newAlbums)
    oled.activeSongs = str(newSongs)
    oled.activePlaytime = str(newPlaytime)
	
    if oled.state == STATE_LIBRARY_INFO and oled.playState == 'info':                                   #this is the "Media-Library-Info-Screen"
       oled.modal.UpdateLibraryInfo() 

def onPushQueue(data):
    oled.queue = [track['name'] if 'name' in track else 'no track' for track in data]

#__________________________________________________________________________________________________________

class NowPlayingScreen():
    def __init__(self, height, width):
        self.height = height
        self.width = width

    def UpdatePlayingInfo(self):
        if DisplayTechnology != 'i2c1306':
            self.image = Image.new('RGB', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
        if DisplayTechnology == 'i2c1306':
            self.image = Image.new('1', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)

    def UpdateStandbyInfo(self):
        if DisplayTechnology != 'i2c1306':
            self.image = Image.new('RGB', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
        if DisplayTechnology == 'i2c1306':
            self.image = Image.new('1', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)

    def DrawOn(self, image):
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

#__________________________________________________________________________________________________________
#               _    ___________  ___      __                            __      
#   _________  (_)  <  /__  /__ \|__ \    / /   ____ ___  ______  __  __/ /______
#  / ___/ __ \/ /   / / /_ <__/ /__/ /   / /   / __ `/ / / / __ \/ / / / __/ ___/
# (__  ) /_/ / /   / /___/ / __// __/   / /___/ /_/ / /_/ / /_/ / /_/ / /_(__  ) 
#/____/ .___/_/   /_//____/____/____/  /_____/\__,_/\__, /\____/\__,_/\__/____/  
#    /_/                                           /____/                        
#__________________________________________________________________________________________________________

        if NowPlayingLayout == 'Spectrum-Center' and newStatus != 'stop':# and DisplayTechnology == 'spi1322'

            if newStatus != 'stop' and oled.duration != None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                data = cava_fifo.readline().strip().split(';')
                #print(data)
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(oled.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen2text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen2text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen2text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen2text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen2text01[1])  
                self.draw.text((self.ArtistPosition), oled.activeArtist, font=font, fill='white')

                self.SongWidth, self.SongHeight = self.draw.textsize(oled.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound == True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen2text02)
                    elif ScrollSongFirstRound == False and ScrollSongNextRound == False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag ,Screen2text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound == True:        
                        if ScrollSongNext >= 0:                    
                            self.SongPosition = (ScrollSongNext ,Screen2text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound == True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen2text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width-self.SongWidth)/2), Screen2text02[1])  
                self.draw.text((self.SongPosition), oled.activeSong, font=font3, fill='white')
                if len(data) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data)-1):
                        try:
                            self.draw.rectangle((Screen2specDistance+i*Screen2specWide1, Screen2specYposTag-int(data[i]), Screen2specDistance+i*Screen2specWide1+Screen2specWide2, Screen2specYposTag), outline = Screen2specBorder, fill =Screen2specFill)  #(255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255
                        except:
                            pass
                self.draw.text((Screen2text28), oled.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen2text06), oled.activeFormat, font=font4, fill='white')

                self.RateString = str(oled.activeSamplerate) + ' / ' + oled.activeBitdepth
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.RateWidth, self.RateHeight = self.draw.textsize(self.RateString, font=font4)
                self.draw.text(((256 - self.RateWidth), Screen2text07[1]), self.RateString, font=font4, fill='white')

                #self.draw.text((Screen2text07), str(oled.activeSamplerate), font=font4, fill='white')
                #self.draw.text((Screen2text08), oled.activeBitdepth, font=font4, fill='white')
                
                self.draw.text((Screen2ActualPlaytimeText), str(timedelta(seconds=round(float(oled.seek) / 1000))), font=font4, fill='white')
                if oled.duration != None:
                    self.playbackPoint = oled.seek / oled.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                    self.DurationWidth, self.DurationHeight = self.draw.textsize(str(timedelta(seconds=oled.duration)), font=font4)
                    self.draw.text(((256 - self.DurationWidth), Screen2DurationText[1]), str(timedelta(seconds=oled.duration)), font=font4, fill='white')
                    self.draw.rectangle((Screen2barLineX , Screen2barLineThick1, Screen2barLineX+Screen2barwidth, Screen2barLineThick2), outline=Screen2barLineBorder, fill=Screen2barLineFill)
                    self.draw.rectangle((self.bar+Screen2barLineX-Screen2barNibbleWidth, Screen2barThick1, Screen2barX+self.bar+Screen2barNibbleWidth, Screen2barThick2), outline=Screen2barBorder, fill=Screen2barFill)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and oled.duration == None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                data = cava_fifo.readline().strip().split(';')
                #print(data)
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(oled.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen2text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen2text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen2text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen2text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen2text01[1])  
                self.draw.text((self.ArtistPosition), oled.activeArtist, font=font, fill='white')

#
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.SongWidth, self.SongHeight = self.draw.textsize(oled.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound == True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen2text02)
                    elif ScrollSongFirstRound == False and ScrollSongNextRound == False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag ,Screen2text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound == True:        
                        if ScrollSongNext >= 0:                    
                            self.SongPosition = (ScrollSongNext ,Screen2text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound == True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen2text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width-self.SongWidth)/2), Screen2text02[1])  
                self.draw.text((self.SongPosition), oled.activeSong, font=font3, fill='white')
                if len(data) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data)-1):
                        try:
                            self.draw.rectangle((Screen22specDistance+i*Screen22specWide1, Screen22specYposTag-int(data[i]), Screen22specDistance+i*Screen22specWide1+Screen22specWide2, Screen22specYposTag), outline = Screen22specBorder, fill = Screen22specFill)  #(255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255
                        except:
                            pass

                image.paste(self.image, (0, 0))

        if NowPlayingLayout == 'No-Spectrum' and newStatus != 'stop':# and DisplayTechnology == 'spi1322'

            if newStatus != 'stop' and oled.duration != None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(oled.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen4text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen4text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen4text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen4text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen4text01[1])  
                self.draw.text((self.ArtistPosition), oled.activeArtist, font=font, fill='white')
#
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.SongWidth, self.SongHeight = self.draw.textsize(oled.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound == True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen4text02)
                    elif ScrollSongFirstRound == False and ScrollSongNextRound == False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag ,Screen4text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound == True:        
                        if ScrollSongNext >= 0:                    
                            self.SongPosition = (ScrollSongNext ,Screen4text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound == True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen4text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width-self.SongWidth)/2), Screen4text02[1])  
                self.draw.text((self.SongPosition), oled.activeSong, font=font3, fill='white')
                self.draw.text((Screen4text28), oled.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen4text06), oled.activeFormat, font=font4, fill='white')

                self.RateString = str(oled.activeSamplerate) + ' / ' + oled.activeBitdepth
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.RateWidth, self.RateHeight = self.draw.textsize(self.RateString, font=font4)
                self.draw.text(((256 - self.RateWidth), Screen2text07[1]), self.RateString, font=font4, fill='white')

                #self.draw.text((Screen4text07), str(oled.activeSamplerate), font=font4, fill='white')
                #self.draw.text((Screen4text08), oled.activeBitdepth, font=font4, fill='white')

                if oled.repeat == True:
                    if oled.repeatonce == False:
                        self.draw.text((Screen4text33), oledrepeat, font=labelfont, fill='white')
                    if oled.repeatonce == True:
                        self.draw.text((Screen4text33), oledrepeat, font=labelfont, fill='white')
                        self.draw.text((Screen4text34), str(1), font=font4, fill='white')
                if oled.shuffle == True:
                    self.draw.text((Screen4text35), oledshuffle, font=labelfont, fill='white')
                if oled.mute == False:
                    self.draw.text((Screen4text30), oledvolumeon, font=labelfontfa, fill='white')
                else:
                    self.draw.text((Screen4text31), oledvolumeoff, font=labelfontfa, fill='white')
                if oled.volume >= 0:
                    self.volume = 'Vol.: ' + str(oled.volume) + '%'
                    self.draw.text((Screen4text29), self.volume, font=font4, fill='white')
                self.draw.text((Screen4ActualPlaytimeText), str(timedelta(seconds=round(float(oled.seek) / 1000))), font=font4, fill='white')
                if oled.duration != None:
                    self.playbackPoint = oled.seek / oled.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    #self.draw.text((Screen4DurationText), str(timedelta(seconds=oled.duration)), font=font4, fill='white')
                    #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                    self.DurationWidth, self.DurationHeight = self.draw.textsize(str(timedelta(seconds=oled.duration)), font=font4)
                    self.draw.text(((256 - self.DurationWidth), Screen4DurationText[1]), str(timedelta(seconds=oled.duration)), font=font4, fill='white')
                    self.draw.rectangle((Screen4barLineX , Screen4barLineThick1, Screen4barLineX+Screen4barwidth, Screen4barLineThick2), outline=Screen4barLineBorder, fill=Screen4barLineFill)
                    self.draw.rectangle((self.bar+Screen4barLineX-Screen4barNibbleWidth, Screen4barThick1, Screen4barX+self.bar+Screen4barNibbleWidth, Screen4barThick2), outline=Screen4barBorder, fill=Screen4barFill)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and oled.duration == None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(oled.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen4text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen4text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen4text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen4text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen4text01[1])  
                self.draw.text((self.ArtistPosition), oled.activeArtist, font=font, fill='white')
#
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.SongWidth, self.SongHeight = self.draw.textsize(oled.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound == True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen4text02)
                    elif ScrollSongFirstRound == False and ScrollSongNextRound == False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag ,Screen4text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound == True:        
                        if ScrollSongNext >= 0:                    
                            self.SongPosition = (ScrollSongNext ,Screen4text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound == True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen4text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width-self.SongWidth)/2), Screen4text02[1])  
                self.draw.text((self.SongPosition), oled.activeSong, font=font3, fill='white')
                self.draw.text((Screen4text60), oled.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen4Text61), oled.activeFormat, font=font4, fill='white')
                self.draw.text((Screen4text62), oled.bitrate, font=font4, fill='white')
                if oled.repeat == True:
                    if oled.repeatonce == False:
                        self.draw.text((Screen4text63), oledrepeat, font=labelfont, fill='white')
                    if oled.repeatonce == True:
                        self.draw.text((Screen4text63), oledrepeat, font=labelfont, fill='white')
                        self.draw.text((Screen4text64), str(1), font=font4, fill='white')
                if oled.shuffle == True:
                    self.draw.text((Screen4text65), oledshuffle, font=labelfont, fill='white')
                if oled.mute == False:
                    self.draw.text((Screen4text66), oledvolumeon, font=labelfontfa, fill='white')
                else:
                    self.draw.text((Screen4text67), oledvolumeoff, font=labelfontfa, fill='white')
                if oled.volume >= 0:
                    self.volume = 'Vol.: ' + str(oled.volume) + '%'
                    self.draw.text((Screen4text68), self.volume, font=font4, fill='white')
                image.paste(self.image, (0, 0))

        if NowPlayingLayout == 'Modern' and newStatus != 'stop':# and DisplayTechnology == 'spi1322'

            if newStatus != 'stop' and oled.duration != None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data3 = cava_fifo.readline().strip().split(';')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = oled.activeArtist + ' - ' + oled.activeSong
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(TextBaustein, font=font6)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen5text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen5text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen5text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen5text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen5text01[1])  
                self.draw.text((self.ArtistPosition), TextBaustein, font=font6, fill='white')
                if len(data3) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data3)-1):
                        try:
                            self.draw.rectangle((Screen5specDistance+i*Screen5specWide1, Screen5specYposTag-int(data3[i]), Screen5specDistance+i*Screen5specWide1+Screen5specWide2, Screen5specYposTag), outline = Screen5specBorder, fill =Screen5specFill)  #(255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255  ::Screen5specYposTag-int(data3[i])
                        except:
                            continue
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        for i in range(leftVU1):
                            try:
                                self.draw.rectangle((Screen5leftVUDistance+i*Screen5leftVUWide1, Screen5leftVUYpos1, Screen5leftVUDistance+i*Screen5leftVUWide1+Screen5leftVUWide2, Screen5leftVUYpos2), outline = Screen5leftVUBorder, fill = Screen5leftVUFill)
                            except:
                                continue
                    if rightVU != '':
                        rightVU2 = int(rightVU)        
                        for i in range(rightVU2):
                            try:
                                self.draw.rectangle((Screen5rightVUDistance-i*Screen5rightVUWide1, Screen5rightVUYpos1, Screen5rightVUDistance-i*Screen5rightVUWide1+Screen5rightVUWide2, Screen5rightVUYpos2), outline = Screen5rightVUBorder, fill = Screen5rightVUFill)
                            except:
                                continue    
                self.draw.line((0, 36, 255, 36), fill='white', width=1)
                self.draw.line((0, 47, 64, 47), fill='white', width=1)
                self.draw.line((64, 47, 70, 36), fill='white', width=1)
                self.draw.line((190, 47, 255, 47), fill='white', width=1)
                self.draw.line((184, 36, 190, 47), fill='white', width=1)
                self.draw.text((Screen5text28), oled.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen5text06), oled.activeFormat, font=font7, fill='white')
                self.draw.text((Screen5text07), oled.activeSamplerate, font=font7, fill='white')
                self.draw.text((Screen5text08), oled.activeBitdepth, font=font7, fill='white')
                self.draw.text((Screen5ActualPlaytimeText), str(timedelta(seconds=round(float(oled.seek) / 1000))), font=font7, fill='white')
                if oled.duration != None:
                    self.playbackPoint = oled.seek / oled.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    self.draw.text((Screen5DurationText), str(timedelta(seconds=oled.duration)), font=font7, fill='white')
                    self.draw.rectangle((Screen5barLineX , Screen5barLineThick1, Screen5barLineX+Screen5barwidth, Screen5barLineThick2), outline=Screen5barLineBorder, fill=Screen5barLineFill)
                    self.draw.rectangle((self.bar+Screen5barLineX-Screen5barNibbleWidth, Screen5barThick1, Screen5barX+self.bar+Screen5barNibbleWidth, Screen5barThick2), outline=Screen5barBorder, fill=Screen5barFill)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and oled.duration == None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data = cava_fifo.readline().strip().split(';')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = oled.activeArtist + ' - ' + oled.activeSong
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(TextBaustein, font=font6)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen5text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen5text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen5text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen5text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen5text01[1])  
                self.draw.text((self.ArtistPosition), TextBaustein, font=font6, fill='white')                
                if len(data) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data)-1):
                        try:
                            self.draw.rectangle((Screen55specDistance+i*Screen55specWide1, Screen55specYposTag-int(data[i]), Screen55specDistance+i*Screen55specWide1+Screen55specWide2, Screen55specYposTag), outline = Screen55specBorder, fill =Screen55specFill)  #(255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255
                        except:
                            continue
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        for i in range(leftVU1):
                            try:
                                self.draw.rectangle((Screen5leftVUDistance+i*Screen55leftVUWide1, Screen55leftVUYpos1, i*Screen55leftVUWide1+Screen55leftVUWide2, Screen55leftVUYpos2), outline = Screen55leftVUBorder, fill = Screen55leftVUFill)
                            except:
                                continue
                    if rightVU != '':
                        rightVU2 = int(rightVU)
   
                        for i in range(rightVU2):
                            try:
                                self.draw.rectangle((Screen55rightVUDistance-i*Screen55rightVUWide1, Screen55rightVUYpos1, Screen55rightVUDistance-i*Screen55rightVUWide1+Screen55rightVUWide2, Screen55rightVUYpos2), outline = Screen55rightVUBorder, fill = Screen55rightVUFill)
                            except:
                                continue    
                self.draw.line((0, 36, 255, 36), fill='white', width=1)
                self.draw.line((0, 47, 64, 47), fill='white', width=1)
                self.draw.line((64, 47, 70, 36), fill='white', width=1)
                self.draw.line((190, 47, 255, 47), fill='white', width=1)
                self.draw.line((184, 36, 190, 47), fill='white', width=1)
                image.paste(self.image, (0, 0))

        if NowPlayingLayout == 'VU-Meter-2' and newStatus != 'stop':# and DisplayTechnology == 'spi1322'
            if newStatus != 'stop' and oled.duration != None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                logoImage = Image.open('/home/volumio/NR1-UI/img/vu2.png').convert('RGB')
                self.image.paste(logoImage, (0, 0))
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = oled.activeArtist + ' - ' + oled.activeSong
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(TextBaustein, font=font8)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen7text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen7text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen7text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen7text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen7text01[1])  
                self.draw.text((self.ArtistPosition), TextBaustein, font=font8, fill='white')
                self.SpecString = oled.activeFormat + ' ' + oled.activeSamplerate + '/' + oled.activeBitdepth
                self.draw.text((Screen7text28), oled.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen7text06), self.SpecString, font=font11, fill='white')
                self.draw.text((Screen7ActualPlaytimeText), str(timedelta(seconds=round(float(oled.seek) / 1000))), font=font4, fill='white')
                if oled.duration != None:
                    self.playbackPoint = oled.seek / oled.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                    self.DurationWidth, self.DurationHeight = self.draw.textsize(str(timedelta(seconds=oled.duration)), font=font4)
                    self.draw.text(((256 - self.DurationWidth), Screen7DurationText[1]), str(timedelta(seconds=oled.duration)), font=font4, fill='white')
                    self.draw.rectangle((Screen7barLineX , Screen7barLineThick1, Screen7barLineX+Screen7barwidth, Screen7barLineThick2), outline=Screen7barLineBorder, fill=Screen7barLineFill)
                    self.draw.rectangle((self.bar+Screen7barLineX-Screen7barNibbleWidth, Screen7barThick1, Screen7barX+self.bar+Screen7barNibbleWidth, Screen7barThick2), outline=Screen7barBorder, fill=Screen7barFill)  
                if len(data2) >= 3:
                    leftVU = data2[0]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        self.draw.line(Screen7leftVUcoordinates[leftVU1], fill='white', width=2)                  
                    rightVU = data2[1]
                    if rightVU != '':
                        rightVU1 = int(rightVU)
                        self.draw.line(Screen7rightVUcoordinates[rightVU1], fill='white', width=2)                                              
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and oled.duration == None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                logoImage = Image.open('/home/volumio/NR1-UI/img/vu2.png').convert('RGB')
                self.image.paste(logoImage, (0, 0))
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = oled.activeArtist + ' - ' + oled.activeSong
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(TextBaustein, font=font8)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen7text01)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen7text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen7text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen7text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen7text01[1])  
                self.draw.text((self.ArtistPosition), TextBaustein, font=font8, fill='white')      
                if len(data2) >= 3:
                    leftVU = data2[0]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        self.draw.line(Screen7leftVUcoordinates[leftVU1], fill='white', width=2)                  
                    rightVU = data2[1]
                    if rightVU != '':
                        rightVU1 = int(rightVU)
                        self.draw.line(Screen7rightVUcoordinates[rightVU1], fill='white', width=2)                        
                image.paste(self.image, (0, 0))

        if NowPlayingLayout == 'VU-Meter-Bar' and newStatus != 'stop':# and DisplayTechnology == 'spi1322'
            global spectrumPeaksL
            global spectrumPeaksR
            if newStatus != 'stop' and oled.duration != None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                logoImage = Image.open('/home/volumio/NR1-UI/img/vudig.png').convert('RGB')
                self.image.paste(logoImage, (0, 0))
                spec_gradient = np.linspace(Screen8specGradstart, Screen8specGradstop, Screen8specGradSamples)
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(oled.activeArtist, font=font13)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width - 60:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 60
                        self.ArtistPosition = (Screen8text01[0] + 60, Screen8text01[1])
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 60:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen8text01[1])
                            ScrollArtistNext = 60
                        elif ScrollArtistTag == self.ArtistWidth - 59:
                            ScrollArtistTag = 60
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 61:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen8text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == 60 and ScrollArtistNextRound == True:
                            ScrollArtistNext = 60
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 60
                            self.ArtistPosition = (Screen8text01[0] + 60, Screen8text01[1])
                if self.ArtistWidth <= self.width - 60:                  # center text
                    self.ArtistPosition = (int(((self.width-59-self.ArtistWidth)/2) + 60), Screen8text01[1])  
                self.draw.text((self.ArtistPosition), oled.activeArtist, font=font13, fill='white')
#
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.SongWidth, self.SongHeight = self.draw.textsize(oled.activeSong, font=font14)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width - 60:
                    if ScrollSongFirstRound == True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 60
                        self.SongPosition = (Screen8text02[0] + 60, Screen8text02[1])
                    elif ScrollSongFirstRound == False and ScrollSongNextRound == False:
                        if ScrollSongTag <= self.SongWidth - 60:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag ,Screen8text02[1])
                            ScrollSongNext = 60
                        elif ScrollSongTag == self.SongWidth - 59:
                            ScrollSongTag = 60
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound == True:        
                        if ScrollSongNext >= 61:                    
                            self.SongPosition = (ScrollSongNext ,Screen8text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == 60 and ScrollSongNextRound == True:
                            ScrollSongNext = 60
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = True
                            ScrollSongTag = 60
                            self.SongPosition = (Screen8text02[0] + 60, Screen8text02[1])
                if self.SongWidth <= self.width - 60:                  # center text
                    self.SongPosition = (int(((self.width-59-self.SongWidth)/2) + 60), Screen8text02[1])  
                self.draw.text((self.SongPosition), oled.activeSong, font=font14, fill='white')
                self.draw.rectangle((0, 0, 59, 34), fill = 'black', outline = 'black')
                self.draw.text((Screen8text28), oled.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen8text06), oled.activeFormat, font=font11, fill='white')
                self.draw.text((Screen8text07), str(oled.activeSamplerate), font=font11, fill='white')
                self.draw.text((Screen8text08), oled.activeBitdepth, font=font11, fill='white')
                if oled.duration != None:
                    self.draw.text((Screen8ActualPlaytimeText), str(timedelta(seconds=round(float(oled.seek) / 1000))), font=font11, fill='white')
                    self.playbackPoint = oled.seek / oled.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    self.draw.text((Screen8DurationText), str(timedelta(seconds=oled.duration)), font=font11, fill='white')
                    self.draw.rectangle((Screen8barLineX , Screen8barLineThick1, Screen8barLineX+Screen8barwidth, Screen8barLineThick2), outline=Screen8barLineBorder, fill=Screen8barLineFill)
                    self.draw.rectangle((self.bar+Screen8barLineX-Screen8barNibbleWidth, Screen8barThick1, Screen8barX+self.bar+Screen8barNibbleWidth, Screen8barThick2), outline=Screen8barBorder, fill=Screen8barFill)
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        topL = leftVU1
                        if oled.prevFallingTimerL == 0:
                            spectrumPeaksL = leftVU1
                        if ((time() - oled.prevFallingTimerL) > Screen8fallingTime):
                            spectrumPeaksL = topL
                        for i in range(leftVU1):
                            try:
                                self.draw.line(((Screen8leftVUDistance+i*Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance+i*Screen8leftVUWide1, Screen8leftVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8leftVUWide2)
                            except:
                                continue
                        if oled.prevFallingTimerL == 0:
                            oled.prevFallingTimerL = time()
                        if topL > spectrumPeaksL:
                            spectrumPeaksL = topL
                        if ((time() - oled.prevFallingTimerL) > Screen8fallingTime):
                            oled.fallingL = True
                            if spectrumPeaksL > topL:
                                spectrumPeaksL = topL
                                if oled.fallingL:
                                    oled.prevFallingTimerL = time()
                            oled.prevFallingTimerL = time()
                        self.draw.line(((Screen8leftVUDistance+spectrumPeaksL*Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance+spectrumPeaksL*Screen8leftVUWide1, Screen8leftVUYpos2)), fill='white', width=2)
                    if rightVU != '':
                        rightVU1 = int(rightVU)
                        topR = rightVU1
                        if oled.prevFallingTimerR == 0:
                            spectrumPeaksR = rightVU1
                        if ((time() - oled.prevFallingTimerR) > Screen8fallingTime):
                            spectrumPeaksR = topR
                        for i in range(rightVU1):
                            try:
                                self.draw.line(((Screen8rightVUDistance+i*Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance+i*Screen8rightVUWide1, Screen8rightVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8rightVUWide2)
                            except:
                                continue
                        if oled.prevFallingTimerR == 0:
                            oled.prevFallingTimerR = time()
                        if topR > spectrumPeaksR:
                            spectrumPeaksR = topR
                        if ((time() - oled.prevFallingTimerR) > Screen8fallingTime):
                            oled.fallingR = True
                            if spectrumPeaksR > topR:
                                spectrumPeaksR = topR
                                if oled.fallingRL:
                                    oled.prevFallingTimerR = time()
                            oled.prevFallingTimerR = time()
                        self.draw.line(((Screen8rightVUDistance+spectrumPeaksR*Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance+spectrumPeaksR*Screen8rightVUWide1, Screen8rightVUYpos2)), fill='white', width=Screen8PeakWidth)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and oled.duration == None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                logoImage = Image.open('/home/volumio/NR1-UI/img/vudig.png').convert('RGB')
                self.image.paste(logoImage, (0, 0))
                spec_gradient = np.linspace(Screen8specGradstart, Screen8specGradstop, Screen8specGradSamples)
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                #
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.ArtistWidth, self.ArtistHeight = self.draw.textsize(oled.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound == True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen8text11)
                    elif ScrollArtistFirstRound == False and ScrollArtistNextRound == False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag ,Screen8text11[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound == True:        
                        if ScrollArtistNext >= 0:                    
                            self.ArtistPosition = (ScrollArtistNext ,Screen8text11[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound == True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen8text11)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width-self.ArtistWidth)/2), Screen8text11[1])  
                self.draw.text((self.ArtistPosition), oled.activeArtist, font=font, fill='white')
#
                #
                #
                # DeprecationWarning: textsize is deprecated and will be removed in Pillow 10 (2023-07-01). Use textbbox or textlength instead.
                self.SongWidth, self.SongHeight = self.draw.textsize(oled.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound == True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen8text22)
                    elif ScrollSongFirstRound == False and ScrollSongNextRound == False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag ,Screen8text22[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound == True:        
                        if ScrollSongNext >= 0:                    
                            self.SongPosition = (ScrollSongNext ,Screen8text22[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound == True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen8text22)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width-self.SongWidth)/2), Screen8text22[1])  
                self.draw.text((self.SongPosition), oled.activeSong, font=font3, fill='white')
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        topL = leftVU1
                        if oled.prevFallingTimerL == 0:
                            spectrumPeaksL = leftVU1
                        if ((time() - oled.prevFallingTimerL) > Screen8fallingTime):
                            spectrumPeaksL = topL
                        for i in range(leftVU1):
                            try:
                                self.draw.line(((Screen8leftVUDistance+i*Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance+i*Screen8leftVUWide1, Screen8leftVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8leftVUWide2)
                            except:
                                continue
                        if oled.prevFallingTimerL == 0:
                            oled.prevFallingTimerL = time()
                        if topL > spectrumPeaksL:
                            spectrumPeaksL = topL
                        if ((time() - oled.prevFallingTimerL) > Screen8fallingTime):
                            oled.fallingL = True
                            if spectrumPeaksL > topL:
                                spectrumPeaksL = topL
                                if oled.fallingL:
                                    oled.prevFallingTimerL = time()
                            oled.prevFallingTimerL = time()
                        self.draw.line(((Screen8leftVUDistance+spectrumPeaksL*Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance+spectrumPeaksL*Screen8leftVUWide1, Screen8leftVUYpos2)), fill='white', width=Screen8PeakWidth)
                    if rightVU != '':
                        rightVU1 = int(rightVU)
                        topR = rightVU1
                        if oled.prevFallingTimerR == 0:
                            spectrumPeaksR = rightVU1
                        if ((time() - oled.prevFallingTimerR) > Screen8fallingTime):
                            spectrumPeaksR = topR
                        for i in range(rightVU1):
                            try:
                                self.draw.line(((Screen8rightVUDistance+i*Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance+i*Screen8rightVUWide1, Screen8rightVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8rightVUWide2)
                            except:
                                continue
                        if oled.prevFallingTimerR == 0:
                            oled.prevFallingTimerR = time()
                        if topR > spectrumPeaksR:
                            spectrumPeaksR = topR
                        if ((time() - oled.prevFallingTimerR) > Screen8fallingTime):
                            oled.fallingR = True
                            if spectrumPeaksR > topR:
                                spectrumPeaksR = topR
                                if oled.fallingRL:
                                    oled.prevFallingTimerR = time()
                            oled.prevFallingTimerR = time()
                        self.draw.line(((Screen8rightVUDistance+spectrumPeaksR*Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance+spectrumPeaksR*Screen8rightVUWide1, Screen8rightVUYpos2)), fill='white', width=2)
                #self.draw.text((self.ARTpos), oled.activeArtist, font=font, fill='white')
                #self.draw.text((self.SONpos), oled.activeSong, font=font3, fill='white')
                image.paste(self.image, (0, 0))

#_____________________________________________________________________________________________________________
#   _____ __                  ____               _____                         
#  / ___// /_____ _____  ____/ / /_  __  __     / ___/_____________  ___  ____ 
#  \__ \/ __/ __ `/ __ \/ __  / __ \/ / / /_____\__ \/ ___/ ___/ _ \/ _ \/ __ \
# ___/ / /_/ /_/ / / / / /_/ / /_/ / /_/ /_____/__/ / /__/ /  /  __/  __/ / / /
#/____/\__/\__,_/_/ /_/\__,_/_.___/\__, /     /____/\___/_/   \___/\___/_/ /_/ 
#                                 /____/                                       
#_____________________________________________________________________________________________________________
        elif oled.playState == 'stop':
            self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
            if DisplayTechnology == 'spi1351' or DisplayTechnology == 'st7735': 
                self.draw.text((oledtext03), oled.time, font=fontClock, fill=(0, 255, 0))
            else: 
                self.draw.text((oledtext03), oled.time, font=fontClock, fill='white')
            image.paste(self.image, (0, 0))

class MediaLibrarayInfo():
    def __init__(self, height, width):
        self.height = height
        self.width = width

    def UpdateLibraryInfo(self):
        if DisplayTechnology != 'i2c1306': 
            self.image = Image.new('RGB', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
        if DisplayTechnology == 'i2c1306':
            self.image = Image.new('1', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)

    def DrawOn(self, image):
        self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
        self.draw.text((oledtext10), oled.activeArtists, font=font4, fill='white')
        self.draw.text((oledtext11), oled.activeAlbums, font=font4, fill='white')
        self.draw.text((oledtext12), oled.activeSongs, font=font4, fill='white')
        self.draw.text((oledtext13), oled.activePlaytime, font=font4, fill='white')
        self.draw.text((oledtext14), oledArt, font=font4, fill='white')
        self.draw.text((oledtext15), oledAlb, font=font4, fill='white')
        self.draw.text((oledtext16), oledSon, font=font4, fill='white')
        self.draw.text((oledtext17), oledPla, font=font4, fill='white')
        self.draw.text((oledtext19), oledlibraryReturn, font=iconfontBottom, fill='white')
        self.draw.text((oledtext20), oledArtistIcon, font=mediaicon, fill='white')
        self.draw.text((oledtext21), oledAlbumIcon, font=mediaicon, fill='white')            
        self.draw.text((oledtext22), oledSongIcon, font=mediaicon, fill='white')
        self.draw.text((oledtext23), oledPlaytimeIcon, font=mediaicon, fill='white')
        image.paste(self.image, (0, 0))

class MenuScreen():
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.selectedOption = oled.playPosition
        self.menurows = oledListEntrys
        self.menuText = [None for i in range(self.menurows)]
        self.menuList = oled.queue
        self.totaloptions = len(oled.queue)
        self.onscreenoptions = min(self.menurows, self.totaloptions)
        self.firstrowindex = 0
        self.MenuUpdate()

    def DrawOption(self, text, y_pos, selected):
        if selected:
            color = oledMenuHighlightColor
            bgcolor = oledMenuHighlightBackGround
        else:
            color = oledMenuNotSelectedColor
            bgcolor = oledMenuNotSelectedBackground

        option_text = StaticText(self.height, self.width, text, font2, fill=color, bgcolor=bgcolor)
        option_text.DrawOn(self.image, (oledListTextPosX, y_pos))

    def Clear(self):
        self.image.paste(('black'), [0, 0, self.width, self.height])


    def MenuUpdate(self):
        self.firstrowindex = min(self.firstrowindex, self.selectedOption)
        self.firstrowindex = max(self.firstrowindex, self.selectedOption - (self.menurows-1))
        for row in range(self.onscreenoptions):
            if (self.firstrowindex + row) == self.selectedOption:
                color = oledMenuHighlightColor  #"black"
                bgcolor = oledMenuHighlightBackGround #"white"
            else:
                color = oledMenuNotSelectedColor #"white"
                bgcolor = oledMenuNotSelectedBackground #"black"
            optionText = self.menuList[row+self.firstrowindex]
            self.menuText[row] = StaticText(self.height, self.width, optionText, font2, fill=color, bgcolor=bgcolor)
        if self.totaloptions == 0:
            self.menuText[0] = StaticText(self.height, self.width, oledEmptyListText, font2, fill="white", bgcolor="black")
            
    def NextOption(self):
        self.selectedOption = min(self.selectedOption + 1, self.totaloptions - 1)
        self.MenuUpdate()

    def PrevOption(self):
        self.selectedOption = max(self.selectedOption - 1, 0)
        self.MenuUpdate()

    def SelectedOption(self):
        return self.selectedOption 

    def DrawOn(self, image):
        for row in range(self.onscreenoptions):
            self.menuText[row].DrawOn(image, (oledListTextPosX, row*oledListTextPosY))       #Here is the position of the list entrys from left set (42)
        if self.totaloptions == 0:
            self.menuText[0].DrawOn(image, (oledEmptyListTextPosition))                  #Here is the position of the list entrys from left set (42)

class ScreenSelectMenu():
    def __init__(self, height, width):
        self.height = height
        self.width = width
        index = ScreenList.index(NowPlayingLayout)
        self.selectedOption = int(index)
        self.menurows = oledListEntrys
        self.menuText = [None for i in range(self.menurows)]
        self.menuList = ScreenList
        self.totaloptions = len(ScreenList)
        self.onscreenoptions = min(self.menurows, self.totaloptions)
        self.firstrowindex = 0
        self.MenuUpdate()

    def MenuUpdate(self):
        self.firstrowindex = min(self.firstrowindex, self.selectedOption)
        self.firstrowindex = max(self.firstrowindex, self.selectedOption - (self.menurows-1))
        for row in range(self.onscreenoptions):
            if (self.firstrowindex + row) == self.selectedOption:
                color = oledMenuHighlightColor  #"black"
                bgcolor = oledMenuHighlightBackGround #"white"
            else:
                color = oledMenuNotSelectedColor #"white"
                bgcolor = oledMenuNotSelectedBackground #"black"
            optionText = self.menuList[row+self.firstrowindex]
            self.menuText[row] = StaticText(self.height, self.width, optionText, font2, fill=color, bgcolor=bgcolor)
        if self.totaloptions == 0:
            self.menuText[0] = StaticText(self.height, self.width, oledEmptyListText, font2, fill="white", bgcolor="black")
            
    def NextOption(self):
        self.selectedOption = min(self.selectedOption + 1, self.totaloptions - 1)
        self.MenuUpdate()

    def PrevOption(self):
        self.selectedOption = max(self.selectedOption - 1, 0)
        self.MenuUpdate()

    def SelectedOption(self):
        return self.selectedOption 

    def DrawOn(self, image):
        for row in range(self.onscreenoptions):
            self.menuText[row].DrawOn(image, (oledListTextPosX, row*oledListTextPosY))       #Here is the position of the list entrys from left set (42)
        if self.totaloptions == 0:
            self.menuText[0].DrawOn(image, (oledEmptyListTextPosition))                  #Here is the position of the list entrys from left set (42)

#________________________________________________________________________________________
#________________________________________________________________________________________
#	
#    ____        __  __                 ____                 __  _                      
#   / __ )__  __/ /_/ /_____  ____     / __/_  ______  _____/ /_(_)___  ____  _____   _ 
#  / __  / / / / __/ __/ __ \/ __ \   / /_/ / / / __ \/ ___/ __/ / __ \/ __ \/ ___/  (_)
# / /_/ / /_/ / /_/ /_/ /_/ / / / /  / __/ /_/ / / / / /__/ /_/ / /_/ / / / (__  )  _   
#/_____/\__,_/\__/\__/\____/_/ /_/  /_/  \__,_/_/ /_/\___/\__/_/\____/_/ /_/____/  (_)  
#                                                                                       	


def ButtonC_PushEvent():
    print('ButtonC short press event')
    if oled.state == STATE_PLAYER and oled.playState == 'stop':
        print ('RightKnob_PushEvent SHORT')
        SetState(STATE_SCREEN_MENU)
        oled.state = 3
        oled.modal = ScreenSelectMenu(oled.HEIGHT, oled.WIDTH)
        sleep(0.2)
    pass

def ButtonD_PushEvent():
    print('ButtonD short press event')
    if oled.state == STATE_PLAYER and oled.playState == 'stop':
        b_obj = BytesIO()
        crl = pycurl.Curl()
        crl.setopt(crl.URL, 'localhost:3000/api/v1/collectionstats')
        crl.setopt(crl.WRITEDATA, b_obj)
        crl.perform()
        crl.close()
        get_body = b_obj.getvalue()
        print('getBody',get_body)
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
            print ('RightKnob_PushEvent SHORT')
            oled.stateTimeout = 0
        if oled.state == STATE_SCREEN_MENU:
            print ('RightKnob_PushEvent Long')
            global NowPlayingLayout
            oled.SelectedScreen = oled.modal.SelectedOption()
            Screen = ScreenList[oled.SelectedScreen]
            WriteSelScreen = open('/home/volumio/NR1-UI/ConfigurationFiles/LayoutSet.txt', 'w')
            WriteSelScreen.write(Screen)
            WriteSelScreen.close
            NowPlayingLayout = Screen
            SetState(STATE_PLAYER)
            volumioIO.emit('stop')
#________________________________________________________________________________________
#________________________________________________________________________________________

RightKnob_Push = PushButton(oledRtrBtn, max_time=2)
RightKnob_Push.setCallback(RightKnob_PushEvent)
RightKnob_Rotation = RotaryEncoder(oledRtrLeft, oledRtrRight, pulses_per_cycle=4)
RightKnob_Rotation.setCallback(RightKnob_RotaryEvent)

#________________________________________________________________________________________
#________________________________________________________________________________________
#    
#    ____              __        __                          
#   / __ )____  ____  / /_      / /   ____  ____ _____     _ 
#  / __  / __ \/ __ \/ __/_____/ /   / __ \/ __ `/ __ \   (_)
# / /_/ / /_/ / /_/ / /_/_____/ /___/ /_/ / /_/ / /_/ /  _   
#/_____/\____/\____/\__/     /_____/\____/\__, /\____/  (_)  
#    
boot_logo_path = "/home/volumio/NR1-UI/img/bootlogo.gif"
#show_logo(oledBootLogo, oled)
#sleep(5)

loading_logo_path = "/home/volumio/NR1-UI/img/loading.gif"
show_boot_logo_gif(oled, boot_logo_path, display_time=10)

# Display the loading logo for 30 seconds
show_loading_gif(oled, loading_logo_path, display_time=30)


if ledActive == True and firstStart == True:
    SysStart()

# Show loading sequence
#show_loading_sequence(oled, "NR1-UI/img")

#show_logo(oled1BootLogo, oled)
#show_logo2(oled2BootLogo, oled2)
if ledActive == True and firstStart == True:
    Processor = threading.Thread(target=CPUload, daemon=True)
    Processor.start()
    firstStart = False
else: 
    firstStart = False
#sleep(2.0)
sleep(5)
SetState(STATE_PLAYER)
#________________________________________________________________________________________
#________________________________________________________________________________________
#  
#   __  __          __      __          ________                        __         
#  / / / /___  ____/ /___ _/ /____     /_  __/ /_  ________  ____ _____/ /____   _ 
# / / / / __ \/ __  / __ `/ __/ _ \     / / / __ \/ ___/ _ \/ __ `/ __  / ___/  (_)
#/ /_/ / /_/ / /_/ / /_/ / /_/  __/    / / / / / / /  /  __/ /_/ / /_/ (__  )  _   
#\____/ .___/\__,_/\__,_/\__/\___/    /_/ /_/ /_/_/   \___/\__,_/\__,_/____/  (_)  
#    /_/ 
#     
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

try:
    with open('oledConfigurationFiles.json', 'r') as f:   #load last playing track number
        config = json.load(f)
except IOError:
    pass
else:
    oled.playPosition = config['track']
    

InfoTag = 0                         #helper for missing Artist/Song when changing sources


def PlaypositionHelper():
    while True:
        volumioIO.emit('getState')
        now = datetime.now() 
        oled.date = now.strftime("%d.%m.%Y")
        sleep(1.0)

PlayPosHelp = threading.Thread(target=PlaypositionHelper, daemon=True)
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
        volumioIO.emit('stop')
        sleep(0.01)
        volumioIO.emit('play', {'value':oled.selQueue})
    sleep(0.1)


#this is the loop to push the actual time every 0.1sec to the "Standby-Screen"
    if oled.state == STATE_PLAYER and newStatus == 'stop' and oled.ShutdownFlag == False:
        InfoTag = 0  #resets the InfoTag helper from artist/song update loop
        oled.state = 0
        oled.time = strftime("%H:%M")
        SetState(STATE_PLAYER)
        oled.modal.UpdateStandbyInfo()
        sleep(0.2)  

#if playback is paused, here is defined when the Player goes back to "Standby"/Stop		
    if oled.state == STATE_PLAYER and newStatus == 'pause' and varcanc == True:
        secvar = int(round(time()))
        varcanc = False
    elif oled.state == STATE_PLAYER and newStatus == 'pause' and int(round(time())) - secvar > oledPause2StopTime:
        varcanc = True
        volumioIO.emit('stop')
        oled.modal.UpdateStandbyInfo()
        secvar = 0.0

    if oled.state == STATE_PLAYER and newStatus == 'play' and oled.ScreenTimerStart == True:
        oled.ScreenTimerStamp = int(round(time()))
        oled.ScreenTimerStart = False
        oled.ScreenTimer10 = True

    if oled.state == STATE_PLAYER and newStatus != 'stop': 
        if oled.ScreenTimer10 == True and (int(round(time())) - oled.ScreenTimerStamp > oled.ScreenTimerChangeTime):
            oled.ScreenTimerChangeTime
            oled.ScreenTimer10 = False
            oled.ScreenTimer20 = True
        if oled.ScreenTimer20 == True and ((int(round(time())) - oled.ScreenTimerStamp) > (oled.ScreenTimerChangeTime * 2)):
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
