from ConfigurationFiles.ScreenConfig1322 import *
from nr1ui import oled
from nr1ui import font2
from modules.display1322 import *


class ScreenMenue():
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
        self.firstrowindex = max(self.firstrowindex, self.selectedOption - (self.menurows - 1))
        for row in range(self.onscreenoptions):
            if (self.firstrowindex + row) == self.selectedOption:
                color = oledMenuHighlightColor  # "black"
                bgcolor = oledMenuHighlightBackGround  # "white"
            else:
                color = oledMenuNotSelectedColor  # "white"
                bgcolor = oledMenuNotSelectedBackground  # "black"
            optionText = self.menuList[row + self.firstrowindex]
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
            self.menuText[row].DrawOn(image, (oledListTextPosX, row * oledListTextPosY))  # Here is the position of the list entrys from left set (42)
        if self.totaloptions == 0:
            self.menuText[0].DrawOn(image, (oledEmptyListTextPosition))  # Here is the position of the list entrys from left set (42)
