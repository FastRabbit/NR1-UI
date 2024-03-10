from time import *
import numpy as np
from datetime import timedelta
from ConfigurationFiles.ScreenConfig1322 import *
from modules.display1322 import *
from display import *
from font import *


class ScreenNowPlaying():
    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.image_vu = Image.open('/home/volumio/NR1-UI/img/vu.png').convert('RGB')
        self.image_vudig = Image.open('/home/volumio/NR1-UI/img/vudig.png').convert('RGB')

    def UpdatePlayingInfo(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def UpdateStandbyInfo(self):
        self.image = Image.new('RGB', (self.width, self.height))
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

        if display.SelectedScreen == 'Spectrum-Center' and newStatus != 'stop':

            if newStatus != 'stop' and display.duration is not None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                data = cava_fifo.readline().strip().split(';')
                # print(data)
                self.ArtistWidth = self.draw.textlength(display.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen2text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen2text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen2text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen2text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen2text01[1])
                self.draw.text((self.ArtistPosition), display.activeArtist, font=font, fill='white')

                self.SongWidth = self.draw.textlength(display.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound is True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen2text02)
                    elif ScrollSongFirstRound is False and ScrollSongNextRound is False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag, Screen2text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound is True:
                        if ScrollSongNext >= 0:
                            self.SongPosition = (ScrollSongNext, Screen2text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound is True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen2text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width - self.SongWidth) / 2), Screen2text02[1])
                self.draw.text((self.SongPosition), display.activeSong, font=font3, fill='white')
                if len(data) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data) - 1):
                        try:
                            self.draw.rectangle((Screen2specDistance + i * Screen2specWide1, Screen2specYposTag - int(data[i]), Screen2specDistance + i * Screen2specWide1 + Screen2specWide2, Screen2specYposTag), outline=Screen2specBorder, fill=Screen2specFill)  # (255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255
                        except:
                            pass
                self.draw.text((Screen2text28), display.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen2text06), display.activeFormat, font=font4, fill='white')

                self.RateString = str(display.activeSamplerate) + ' / ' + display.activeBitdepth
                self.RateWidth = self.draw.textlength(self.RateString, font=font4)
                self.draw.text(((256 - self.RateWidth), Screen2text07[1]), self.RateString, font=font4, fill='white')

                # self.draw.text((Screen2text07), str(display.activeSamplerate), font=font4, fill='white')
                # self.draw.text((Screen2text08), display.activeBitdepth, font=font4, fill='white')

                self.draw.text((Screen2ActualPlaytimeText), str(timedelta(seconds=round(float(display.seek) / 1000))), font=font4, fill='white')
                if display.duration is None:
                    self.playbackPoint = display.seek / display.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    self.DurationWidth = self.draw.textlength(str(timedelta(seconds=display.duration)), font=font4)
                    self.draw.text(((256 - self.DurationWidth), Screen2DurationText[1]), str(timedelta(seconds=display.duration)), font=font4, fill='white')
                    self.draw.rectangle((Screen2barLineX, Screen2barLineThick1, Screen2barLineX + Screen2barwidth, Screen2barLineThick2), outline=Screen2barLineBorder, fill=Screen2barLineFill)
                    self.draw.rectangle((self.bar + Screen2barLineX - Screen2barNibbleWidth, Screen2barThick1, Screen2barX + self.bar + Screen2barNibbleWidth, Screen2barThick2), outline=Screen2barBorder, fill=Screen2barFill)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and display.duration is None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                data = cava_fifo.readline().strip().split(';')
                # print(data)
                self.ArtistWidth = self.draw.textlength(display.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen2text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen2text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen2text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen2text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen2text01[1])
                self.draw.text((self.ArtistPosition), display.activeArtist, font=font, fill='white')
                self.SongWidth = self.draw.textlength(display.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound is True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen2text02)
                    elif ScrollSongFirstRound is False and ScrollSongNextRound is False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag, Screen2text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound is True:
                        if ScrollSongNext >= 0:
                            self.SongPosition = (ScrollSongNext, Screen2text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound is True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen2text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width - self.SongWidth) / 2), Screen2text02[1])
                self.draw.text((self.SongPosition), display.activeSong, font=font3, fill='white')
                if len(data) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data) - 1):
                        try:
                            self.draw.rectangle((Screen22specDistance + i * Screen22specWide1, Screen22specYposTag - int(data[i]), Screen22specDistance + i * Screen22specWide1 + Screen22specWide2, Screen22specYposTag), outline=Screen22specBorder, fill=Screen22specFill)  # (255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255
                        except:
                            pass

                image.paste(self.image, (0, 0))

        if display.SelectedScreen == 'No-Spectrum' and newStatus != 'stop':

            if newStatus != 'stop' and display.duration is not None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                self.ArtistWidth = self.draw.textlength(display.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen4text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen4text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen4text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen4text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen4text01[1])
                self.draw.text((self.ArtistPosition), display.activeArtist, font=font, fill='white')
                self.SongWidth = self.draw.textlength(display.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound is True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen4text02)
                    elif ScrollSongFirstRound is False and ScrollSongNextRound is False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag, Screen4text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound is True:
                        if ScrollSongNext >= 0:
                            self.SongPosition = (ScrollSongNext, Screen4text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound is True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen4text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width - self.SongWidth) / 2), Screen4text02[1])
                self.draw.text((self.SongPosition), display.activeSong, font=font3, fill='white')
                self.draw.text((Screen4text28), display.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen4text06), display.activeFormat, font=font4, fill='white')

                self.RateString = str(display.activeSamplerate) + ' / ' + display.activeBitdepth
                self.RateWidth = self.draw.textlength(self.RateString, font=font4)
                self.draw.text(((256 - self.RateWidth), Screen2text07[1]), self.RateString, font=font4, fill='white')

                # self.draw.text((Screen4text07), str(display.activeSamplerate), font=font4, fill='white')
                # self.draw.text((Screen4text08), display.activeBitdepth, font=font4, fill='white')

                if display.repeat is True:
                    if display.repeatonce is False:
                        self.draw.text((Screen4text33), oledrepeat, font=labelfont, fill='white')
                    if display.repeatonce is True:
                        self.draw.text((Screen4text33), oledrepeat, font=labelfont, fill='white')
                        self.draw.text((Screen4text34), str(1), font=font4, fill='white')
                if display.shuffle is True:
                    self.draw.text((Screen4text35), oledshuffle, font=labelfont, fill='white')
                if display.mute is False:
                    self.draw.text((Screen4text30), oledvolumeon, font=labelfontfa, fill='white')
                else:
                    self.draw.text((Screen4text31), oledvolumeoff, font=labelfontfa, fill='white')
                if display.volume >= 0:
                    self.volume = 'Vol.: ' + str(display.volume) + '%'
                    self.draw.text((Screen4text29), self.volume, font=font4, fill='white')
                self.draw.text((Screen4ActualPlaytimeText), str(timedelta(seconds=round(float(display.seek) / 1000))), font=font4, fill='white')
                if display.duration is not None:
                    self.playbackPoint = display.seek / display.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    # self.draw.text((Screen4DurationText), str(timedelta(seconds=display.duration)), font=font4, fill='white')
                    self.DurationWidth = self.draw.textlength(str(timedelta(seconds=display.duration)), font=font4)
                    self.draw.text(((256 - self.DurationWidth), Screen4DurationText[1]), str(timedelta(seconds=display.duration)), font=font4, fill='white')
                    self.draw.rectangle((Screen4barLineX, Screen4barLineThick1, Screen4barLineX + Screen4barwidth, Screen4barLineThick2), outline=Screen4barLineBorder, fill=Screen4barLineFill)
                    self.draw.rectangle((self.bar + Screen4barLineX - Screen4barNibbleWidth, Screen4barThick1, Screen4barX + self.bar + Screen4barNibbleWidth, Screen4barThick2), outline=Screen4barBorder, fill=Screen4barFill)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and display.duration is None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                self.ArtistWidth = self.draw.textlength(display.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen4text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen4text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen4text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen4text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen4text01[1])
                self.draw.text((self.ArtistPosition), display.activeArtist, font=font, fill='white')
                self.SongWidth = self.draw.textlength(display.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound is True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen4text02)
                    elif ScrollSongFirstRound is False and ScrollSongNextRound is False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag, Screen4text02[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound is True:
                        if ScrollSongNext >= 0:
                            self.SongPosition = (ScrollSongNext, Screen4text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound is True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen4text02)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width - self.SongWidth) / 2), Screen4text02[1])
                self.draw.text((self.SongPosition), display.activeSong, font=font3, fill='white')
                self.draw.text((Screen4text60), display.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen4Text61), display.activeFormat, font=font4, fill='white')
                self.draw.text((Screen4text62), display.bitrate, font=font4, fill='white')
                if display.repeat is True:
                    if display.repeatonce is False:
                        self.draw.text((Screen4text63), oledrepeat, font=labelfont, fill='white')
                    if display.repeatonce is True:
                        self.draw.text((Screen4text63), oledrepeat, font=labelfont, fill='white')
                        self.draw.text((Screen4text64), str(1), font=font4, fill='white')
                if display.shuffle is True:
                    self.draw.text((Screen4text65), oledshuffle, font=labelfont, fill='white')
                if display.mute is False:
                    self.draw.text((Screen4text66), oledvolumeon, font=labelfontfa, fill='white')
                else:
                    self.draw.text((Screen4text67), oledvolumeoff, font=labelfontfa, fill='white')
                if display.volume >= 0:
                    self.volume = 'Vol.: ' + str(display.volume) + '%'
                    self.draw.text((Screen4text68), self.volume, font=font4, fill='white')
                image.paste(self.image, (0, 0))

        if display.SelectedScreen == 'Modern' and newStatus != 'stop':

            if newStatus != 'stop' and display.duration is not None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data3 = cava_fifo.readline().strip().split(';')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = display.activeArtist + ' - ' + display.activeSong
                self.ArtistWidth = self.draw.textlength(TextBaustein, font=font6)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen5text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen5text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen5text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen5text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen5text01[1])
                self.draw.text((self.ArtistPosition), TextBaustein, font=font6, fill='white')
                if len(data3) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data3) - 1):
                        try:
                            self.draw.rectangle((Screen5specDistance + i * Screen5specWide1, Screen5specYposTag - int(data3[i]), Screen5specDistance + i * Screen5specWide1 + Screen5specWide2, Screen5specYposTag), outline=Screen5specBorder, fill=Screen5specFill)  # (255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255  ::Screen5specYposTag-int(data3[i])
                        except:
                            continue
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        for i in range(leftVU1):
                            try:
                                self.draw.rectangle((Screen5leftVUDistance + i * Screen5leftVUWide1, Screen5leftVUYpos1, Screen5leftVUDistance + i * Screen5leftVUWide1 + Screen5leftVUWide2, Screen5leftVUYpos2), outline=Screen5leftVUBorder, fill=Screen5leftVUFill)
                            except:
                                continue
                    if rightVU != '':
                        rightVU2 = int(rightVU)
                        for i in range(rightVU2):
                            try:
                                self.draw.rectangle((Screen5rightVUDistance - i * Screen5rightVUWide1, Screen5rightVUYpos1, Screen5rightVUDistance - i * Screen5rightVUWide1 + Screen5rightVUWide2, Screen5rightVUYpos2), outline=Screen5rightVUBorder, fill=Screen5rightVUFill)
                            except:
                                continue
                self.draw.line((0, 36, 255, 36), fill='white', width=1)
                self.draw.line((0, 47, 64, 47), fill='white', width=1)
                self.draw.line((64, 47, 70, 36), fill='white', width=1)
                self.draw.line((190, 47, 255, 47), fill='white', width=1)
                self.draw.line((184, 36, 190, 47), fill='white', width=1)
                self.draw.text((Screen5text28), display.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen5text06), display.activeFormat, font=font7, fill='white')
                self.draw.text((Screen5text07), display.activeSamplerate, font=font7, fill='white')
                self.draw.text((Screen5text08), display.activeBitdepth, font=font7, fill='white')
                self.draw.text((Screen5ActualPlaytimeText), str(timedelta(seconds=round(float(display.seek) / 1000))), font=font7, fill='white')
                if display.duration is not None:
                    self.playbackPoint = display.seek / display.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    self.draw.text((Screen5DurationText), str(timedelta(seconds=display.duration)), font=font7, fill='white')
                    self.draw.rectangle((Screen5barLineX, Screen5barLineThick1, Screen5barLineX + Screen5barwidth, Screen5barLineThick2), outline=Screen5barLineBorder, fill=Screen5barLineFill)
                    self.draw.rectangle((self.bar + Screen5barLineX - Screen5barNibbleWidth, Screen5barThick1, Screen5barX + self.bar + Screen5barNibbleWidth, Screen5barThick2), outline=Screen5barBorder, fill=Screen5barFill)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and display.duration is None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                cava_fifo = open("/tmp/cava_fifo", 'r')
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data = cava_fifo.readline().strip().split(';')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = display.activeArtist + ' - ' + display.activeSong
                self.ArtistWidth = self.draw.textlength(TextBaustein, font=font6)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen5text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen5text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen5text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen5text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen5text01[1])
                self.draw.text((self.ArtistPosition), TextBaustein, font=font6, fill='white')
                if len(data) >= 64 and newStatus != 'pause':
                    for i in range(0, len(data) - 1):
                        try:
                            self.draw.rectangle((Screen55specDistance + i * Screen55specWide1, Screen55specYposTag - int(data[i]), Screen55specDistance + i * Screen55specWide1 + Screen55specWide2, Screen55specYposTag), outline=Screen55specBorder, fill=Screen55specFill)  # (255, 255, 255, 200) means Icon is nearly white. Change 200 to 0 -> icon is not visible. scale = 0-255
                        except:
                            continue
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        for i in range(leftVU1):
                            try:
                                self.draw.rectangle((Screen5leftVUDistance + i * Screen55leftVUWide1, Screen55leftVUYpos1, i * Screen55leftVUWide1 + Screen55leftVUWide2, Screen55leftVUYpos2), outline=Screen55leftVUBorder, fill=Screen55leftVUFill)
                            except:
                                continue
                    if rightVU != '':
                        rightVU2 = int(rightVU)

                        for i in range(rightVU2):
                            try:
                                self.draw.rectangle((Screen55rightVUDistance - i * Screen55rightVUWide1, Screen55rightVUYpos1, Screen55rightVUDistance - i * Screen55rightVUWide1 + Screen55rightVUWide2, Screen55rightVUYpos2), outline=Screen55rightVUBorder, fill=Screen55rightVUFill)
                            except:
                                continue
                self.draw.line((0, 36, 255, 36), fill='white', width=1)
                self.draw.line((0, 47, 64, 47), fill='white', width=1)
                self.draw.line((64, 47, 70, 36), fill='white', width=1)
                self.draw.line((190, 47, 255, 47), fill='white', width=1)
                self.draw.line((184, 36, 190, 47), fill='white', width=1)
                image.paste(self.image, (0, 0))

        if display.SelectedScreen == 'VU-Meter-2' and newStatus != 'stop':
            if newStatus != 'stop' and display.duration is not None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                self.image.paste(self.image_vu, (0, 0))
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = display.activeArtist + ' - ' + display.activeSong
                self.ArtistWidth = self.draw.textlength(TextBaustein, font=font8)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen7text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen7text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen7text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen7text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen7text01[1])
                self.draw.text((self.ArtistPosition), TextBaustein, font=font8, fill='white')
                self.SpecString = display.activeFormat + ' ' + display.activeSamplerate + '/' + display.activeBitdepth
                self.draw.text((Screen7text28), display.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen7text06), self.SpecString, font=font11, fill='white')
                self.draw.text((Screen7ActualPlaytimeText), str(timedelta(seconds=round(float(display.seek) / 1000))), font=font4, fill='white')
                if display.duration is not None:
                    self.playbackPoint = display.seek / display.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    self.DurationWidth = self.draw.textlength(str(timedelta(seconds=display.duration)), font=font4)
                    self.draw.text(((256 - self.DurationWidth), Screen7DurationText[1]), str(timedelta(seconds=display.duration)), font=font4, fill='white')
                    self.draw.rectangle((Screen7barLineX, Screen7barLineThick1, Screen7barLineX + Screen7barwidth, Screen7barLineThick2), outline=Screen7barLineBorder, fill=Screen7barLineFill)
                    self.draw.rectangle((self.bar + Screen7barLineX - Screen7barNibbleWidth, Screen7barThick1, Screen7barX + self.bar + Screen7barNibbleWidth, Screen7barThick2), outline=Screen7barBorder, fill=Screen7barFill)
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

            if newStatus != 'stop' and display.duration is None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                self.image.paste(self.image_vu, (0, 0))
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                TextBaustein = display.activeArtist + ' - ' + display.activeSong
                self.ArtistWidth = self.draw.textlength(TextBaustein, font=font8)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen7text01)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen7text01[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen7text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen7text01)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen7text01[1])
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

        if display.SelectedScreen == 'VU-Meter-Bar' and newStatus != 'stop':
            global spectrumPeaksL
            global spectrumPeaksR
            if newStatus != 'stop' and display.duration is not None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                self.image.paste(self.image_vudig, (0, 0))
                spec_gradient = np.linspace(Screen8specGradstart, Screen8specGradstop, Screen8specGradSamples)
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                self.ArtistWidth = self.draw.textlength(display.activeArtist, font=font13)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width - 60:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 60
                        self.ArtistPosition = (Screen8text01[0] + 60, Screen8text01[1])
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 60:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen8text01[1])
                            ScrollArtistNext = 60
                        elif ScrollArtistTag == self.ArtistWidth - 59:
                            ScrollArtistTag = 60
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 61:
                            self.ArtistPosition = (ScrollArtistNext, Screen8text01[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == 60 and ScrollArtistNextRound is True:
                            ScrollArtistNext = 60
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 60
                            self.ArtistPosition = (Screen8text01[0] + 60, Screen8text01[1])
                if self.ArtistWidth <= self.width - 60:                  # center text
                    self.ArtistPosition = (int(((self.width - 59 - self.ArtistWidth) / 2) + 60), Screen8text01[1])
                self.draw.text((self.ArtistPosition), display.activeArtist, font=font13, fill='white')
                self.SongWidth = self.draw.textlength(display.activeSong, font=font2)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width - 60:
                    if ScrollSongFirstRound is True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 60
                        self.SongPosition = (Screen8text02[0] + 60, Screen8text02[1])
                    elif ScrollSongFirstRound is False and ScrollSongNextRound is False:
                        if ScrollSongTag <= self.SongWidth - 60:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag, Screen8text02[1])
                            ScrollSongNext = 60
                        elif ScrollSongTag == self.SongWidth - 59:
                            ScrollSongTag = 60
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound is True:
                        if ScrollSongNext >= 61:
                            self.SongPosition = (ScrollSongNext, Screen8text02[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == 60 and ScrollSongNextRound is True:
                            ScrollSongNext = 60
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = True
                            ScrollSongTag = 60
                            self.SongPosition = (Screen8text02[0] + 60, Screen8text02[1])
                if self.SongWidth <= self.width - 60:                  # center text
                    self.SongPosition = (int(((self.width - 59 - self.SongWidth) / 2) + 60), Screen8text02[1])
                self.draw.text((self.SongPosition), display.activeSong, font=font2, fill='white')
                self.draw.rectangle((0, 0, 59, 34), fill='black', outline='black')
                self.draw.text((Screen8text28), display.playstateIcon, font=labelfont, fill='white')
                self.draw.text((Screen8text06), display.activeFormat, font=font11, fill='white')
                self.draw.text((Screen8text07), str(display.activeSamplerate), font=font11, fill='white')
                self.draw.text((Screen8text08), display.activeBitdepth, font=font11, fill='white')
                if display.duration is not None:
                    self.draw.text((Screen8ActualPlaytimeText), str(timedelta(seconds=round(float(display.seek) / 1000))), font=font11, fill='white')
                    self.playbackPoint = display.seek / display.duration / 10
                    self.bar = Screen2barwidth * self.playbackPoint / 100
                    self.draw.text((Screen8DurationText), str(timedelta(seconds=display.duration)), font=font11, fill='white')
                    self.draw.rectangle((Screen8barLineX, Screen8barLineThick1, Screen8barLineX + Screen8barwidth, Screen8barLineThick2), outline=Screen8barLineBorder, fill=Screen8barLineFill)
                    self.draw.rectangle((self.bar + Screen8barLineX - Screen8barNibbleWidth, Screen8barThick1, Screen8barX + self.bar + Screen8barNibbleWidth, Screen8barThick2), outline=Screen8barBorder, fill=Screen8barFill)
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        topL = leftVU1
                        if display.prevFallingTimerL == 0:
                            spectrumPeaksL = leftVU1
                        if ((time() - display.prevFallingTimerL) > Screen8fallingTime):
                            spectrumPeaksL = topL
                        for i in range(leftVU1):
                            try:
                                self.draw.line(((Screen8leftVUDistance + i * Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance + i * Screen8leftVUWide1, Screen8leftVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8leftVUWide2)
                            except:
                                continue
                        if display.prevFallingTimerL == 0:
                            display.prevFallingTimerL = time()
                        if topL > spectrumPeaksL:
                            spectrumPeaksL = topL
                        if ((time() - display.prevFallingTimerL) > Screen8fallingTime):
                            display.fallingL = True
                            if spectrumPeaksL > topL:
                                spectrumPeaksL = topL
                                if display.fallingL:
                                    display.prevFallingTimerL = time()
                            display.prevFallingTimerL = time()
                        self.draw.line(((Screen8leftVUDistance + spectrumPeaksL * Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance + spectrumPeaksL * Screen8leftVUWide1, Screen8leftVUYpos2)), fill='white', width=2)
                    if rightVU != '':
                        rightVU1 = int(rightVU)
                        topR = rightVU1
                        if display.prevFallingTimerR == 0:
                            spectrumPeaksR = rightVU1
                        if ((time() - display.prevFallingTimerR) > Screen8fallingTime):
                            spectrumPeaksR = topR
                        for i in range(rightVU1):
                            try:
                                self.draw.line(((Screen8rightVUDistance + i * Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance + i * Screen8rightVUWide1, Screen8rightVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8rightVUWide2)
                            except:
                                continue
                        if display.prevFallingTimerR == 0:
                            display.prevFallingTimerR = time()
                        if topR > spectrumPeaksR:
                            spectrumPeaksR = topR
                        if ((time() - display.prevFallingTimerR) > Screen8fallingTime):
                            display.fallingR = True
                            if spectrumPeaksR > topR:
                                spectrumPeaksR = topR
                                if display.fallingRL:
                                    display.prevFallingTimerR = time()
                            display.prevFallingTimerR = time()
                        self.draw.line(((Screen8rightVUDistance + spectrumPeaksR * Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance + spectrumPeaksR * Screen8rightVUWide1, Screen8rightVUYpos2)), fill='white', width=Screen8PeakWidth)
                image.paste(self.image, (0, 0))

            if newStatus != 'stop' and display.duration is None:
                self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
                self.image.paste(self.image_vudig, (0, 0))
                spec_gradient = np.linspace(Screen8specGradstart, Screen8specGradstop, Screen8specGradSamples)
                cava2_fifo = open("/tmp/cava2_fifo", 'r')
                data2 = cava2_fifo.readline().strip().split(';')
                self.ArtistWidth = self.draw.textlength(display.activeArtist, font=font)
                self.ArtistStopPosition = self.ArtistWidth - self.width + ArtistEndScrollMargin
                if self.ArtistWidth >= self.width:
                    if ScrollArtistFirstRound is True:
                        ScrollArtistFirstRound = False
                        ScrollArtistTag = 0
                        self.ArtistPosition = (Screen8text11)
                    elif ScrollArtistFirstRound is False and ScrollArtistNextRound is False:
                        if ScrollArtistTag <= self.ArtistWidth - 1:
                            ScrollArtistTag += ArtistScrollSpeed
                            self.ArtistPosition = (-ScrollArtistTag, Screen8text11[1])
                            ScrollArtistNext = 0
                        elif ScrollArtistTag == self.ArtistWidth:
                            ScrollArtistTag = 0
                            ScrollArtistNextRound = True
                            ScrollArtistNext = self.width + ArtistEndScrollMargin
                    if ScrollArtistNextRound is True:
                        if ScrollArtistNext >= 0:
                            self.ArtistPosition = (ScrollArtistNext, Screen8text11[1])
                            ScrollArtistNext -= ArtistScrollSpeed
                        elif ScrollArtistNext == -ArtistScrollSpeed and ScrollArtistNextRound is True:
                            ScrollArtistNext = 0
                            ScrollArtistNextRound = False
                            ScrollArtistFirstRound = False
                            ScrollArtistTag = 0
                            self.ArtistPosition = (Screen8text11)
                if self.ArtistWidth <= self.width:                  # center text
                    self.ArtistPosition = (int((self.width - self.ArtistWidth) / 2), Screen8text11[1])
                self.draw.text((self.ArtistPosition), display.activeArtist, font=font, fill='white')
                self.SongWidth = self.draw.textlength(display.activeSong, font=font3)
                self.SongStopPosition = self.SongWidth - self.width + SongEndScrollMargin
                if self.SongWidth >= self.width:
                    if ScrollSongFirstRound is True:
                        ScrollSongFirstRound = False
                        ScrollSongTag = 0
                        self.SongPosition = (Screen8text22)
                    elif ScrollSongFirstRound is False and ScrollSongNextRound is False:
                        if ScrollSongTag <= self.SongWidth - 1:
                            ScrollSongTag += SongScrollSpeed
                            self.SongPosition = (-ScrollSongTag, Screen8text22[1])
                            ScrollSongNext = 0
                        elif ScrollSongTag == self.SongWidth:
                            ScrollSongTag = 0
                            ScrollSongNextRound = True
                            ScrollSongNext = self.width + SongEndScrollMargin
                    if ScrollSongNextRound is True:
                        if ScrollSongNext >= 0:
                            self.SongPosition = (ScrollSongNext, Screen8text22[1])
                            ScrollSongNext -= SongScrollSpeed
                        elif ScrollSongNext == -SongScrollSpeed and ScrollSongNextRound is True:
                            ScrollSongNext = 0
                            ScrollSongNextRound = False
                            ScrollSongFirstRound = False
                            ScrollSongTag = 0
                            self.SongPosition = (Screen8text22)
                if self.SongWidth <= self.width:                  # center text
                    self.SongPosition = (int((self.width - self.SongWidth) / 2), Screen8text22[1])
                self.draw.text((self.SongPosition), display.activeSong, font=font3, fill='white')
                if len(data2) >= 3:
                    leftVU = data2[0]
                    rightVU = data2[1]
                    if leftVU != '':
                        leftVU1 = int(leftVU)
                        topL = leftVU1
                        if display.prevFallingTimerL == 0:
                            spectrumPeaksL = leftVU1
                        if ((time() - display.prevFallingTimerL) > Screen8fallingTime):
                            spectrumPeaksL = topL
                        for i in range(leftVU1):
                            try:
                                self.draw.line(((Screen8leftVUDistance + i * Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance + i * Screen8leftVUWide1, Screen8leftVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8leftVUWide2)
                            except:
                                continue
                        if display.prevFallingTimerL == 0:
                            display.prevFallingTimerL = time()
                        if topL > spectrumPeaksL:
                            spectrumPeaksL = topL
                        if ((time() - display.prevFallingTimerL) > Screen8fallingTime):
                            display.fallingL = True
                            if spectrumPeaksL > topL:
                                spectrumPeaksL = topL
                                if display.fallingL:
                                    display.prevFallingTimerL = time()
                            display.prevFallingTimerL = time()
                        self.draw.line(((Screen8leftVUDistance + spectrumPeaksL * Screen8leftVUWide1, Screen8leftVUYpos1), (Screen8leftVUDistance + spectrumPeaksL * Screen8leftVUWide1, Screen8leftVUYpos2)), fill='white', width=Screen8PeakWidth)
                    if rightVU != '':
                        rightVU1 = int(rightVU)
                        topR = rightVU1
                        if display.prevFallingTimerR == 0:
                            spectrumPeaksR = rightVU1
                        if ((time() - display.prevFallingTimerR) > Screen8fallingTime):
                            spectrumPeaksR = topR
                        for i in range(rightVU1):
                            try:
                                self.draw.line(((Screen8rightVUDistance + i * Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance + i * Screen8rightVUWide1, Screen8rightVUYpos2)), fill=(int(spec_gradient[i]), int(spec_gradient[i]), int(spec_gradient[i])), width=Screen8rightVUWide2)
                            except:
                                continue
                        if display.prevFallingTimerR == 0:
                            display.prevFallingTimerR = time()
                        if topR > spectrumPeaksR:
                            spectrumPeaksR = topR
                        if ((time() - display.prevFallingTimerR) > Screen8fallingTime):
                            display.fallingR = True
                            if spectrumPeaksR > topR:
                                spectrumPeaksR = topR
                                if display.fallingRL:
                                    display.prevFallingTimerR = time()
                            display.prevFallingTimerR = time()
                        self.draw.line(((Screen8rightVUDistance + spectrumPeaksR * Screen8rightVUWide1, Screen8rightVUYpos1), (Screen8rightVUDistance + spectrumPeaksR * Screen8rightVUWide1, Screen8rightVUYpos2)), fill='white', width=2)
                # self.draw.text((self.ARTpos), display.activeArtist, font=font, fill='white')
                # self.draw.text((self.SONpos), display.activeSong, font=font3, fill='white')
                image.paste(self.image, (0, 0))

        elif display.playState == 'stop':
            self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
            self.draw.text((oledtext03), display.time, font=fontClock, fill='white')
            image.paste(self.image, (0, 0))
