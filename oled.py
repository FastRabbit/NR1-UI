#!/usr/bin/python3

from datetime import datetime as datetime

from luma.oled.device import ssd1322
from luma.core.interface.serial import spi

from ConfigurationFiles.PreConfiguration import oledrotation
from ConfigurationFiles.PreConfiguration import NowPlayingLayout, SpectrumActive

if SpectrumActive:
    ScreenList = ['Spectrum-Center', 'No-Spectrum', 'Modern', 'VU-Meter-2', 'VU-Meter-Bar']
else:
    ScreenList = ['No-Spectrum']


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
oled.activeFormat = ''  # makes oled.activeFormat globaly usable
oled.activeSamplerate = ''  # makes oled.activeSamplerate globaly usable
oled.activeBitdepth = ''  # makes oled.activeBitdepth globaly usable
oled.activeArtists = ''  # makes oled.activeArtists globaly usable
oled.activeAlbums = ''  # makes oled.activeAlbums globaly usable
oled.activeAlbum = ''
oled.activeSongs = ''  # makes oled.activeSongs globaly usable
oled.activePlaytime = ''  # makes oled.activePlaytime globaly usable
oled.ShutdownFlag = False  # helper to detect if "shutdown" is running. Prevents artifacts from Standby-Screen during shutdown
oled.SelectedScreen = NowPlayingLayout
oled.fallingL = False
oled.fallingR = False
oled.prevFallingTimerL = 0
oled.prevFallingTimerR = 0
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


emit_track = False
newStatus = 0  # makes newStatus usable outside of onPushState
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

