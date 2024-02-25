from ConfigurationFiles.ScreenConfig1322 import *
from modules.display1322 import *

# from nr1ui import oled
# from nr1ui import font4
# from nr1ui import iconfontBottom
# from nr1ui import mediaicon

from display import *
from font import *


class ScreenMediaLibraryInfo():
    def __init__(self, height, width):
        self.height = height
        self.width = width

    def UpdateLibraryInfo(self):
        self.image = Image.new('RGB', (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)

    def DrawOn(self, image):
        self.image.paste(('black'), [0, 0, image.size[0], image.size[1]])
        self.draw.text((oledtext10), display.activeArtists, font=font4, fill='white')
        self.draw.text((oledtext11), display.activeAlbums, font=font4, fill='white')
        self.draw.text((oledtext12), display.activeSongs, font=font4, fill='white')
        self.draw.text((oledtext13), display.activePlaytime, font=font4, fill='white')
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
