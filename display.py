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


display = ssd1322(spi(device=0, port=0), rotate=oledrotation)
display.WIDTH = 256
display.HEIGHT = 64
display.state = 'stop'
display.stateTimeout = 0
display.playstateIcon = ''
display.timeOutRunning = False
display.activeSong = ''
display.activeArtist = 'VOLuMIO'
display.playState = 'unknown'
display.playPosition = 0
display.seek = 1000
display.duration = 1.0
display.modal = None
display.queue = []
display.volume = 100
display.time = datetime.now().strftime("%H:%M")
display.activeFormat = ''  # makes display.activeFormat globaly usable
display.activeSamplerate = ''  # makes display.activeSamplerate globaly usable
display.activeBitdepth = ''  # makes display.activeBitdepth globaly usable
display.activeArtists = ''  # makes display.activeArtists globaly usable
display.activeAlbums = ''  # makes display.activeAlbums globaly usable
display.activeAlbum = ''
display.activeSongs = ''  # makes display.activeSongs globaly usable
display.activePlaytime = ''  # makes display.activePlaytime globaly usable
display.ShutdownFlag = False  # helper to detect if "shutdown" is running. Prevents artifacts from Standby-Screen during shutdown
display.SelectedScreen = NowPlayingLayout
display.fallingL = False
display.fallingR = False
display.prevFallingTimerL = 0
display.prevFallingTimerR = 0
display.selQueue = ''
display.repeat = False
display.bitrate = ''
display.repeatonce = False
display.shuffle = False
display.mute = False
display.ScreenTimer10 = False
display.ScreenTimer20 = False
display.ScreenTimerStamp = 0.0
display.ScreenTimerStart = True
display.ScreenTimerChangeTime = 10.0

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
