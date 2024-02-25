#!/usr/bin/python3

import os

from PIL import ImageFont


def load_font(filename, font_size):
    font_path = os.path.dirname(os.path.realpath(__file__)) + '/fonts/'
    try:
        font = ImageFont.truetype(font_path + filename, font_size)
    except IOError:
        print('font file not found -> using default font')
        font = ImageFont.load_default()
    return font


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
