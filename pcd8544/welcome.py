#!/usr/bin/python
#########################################################
# initDisplay() - called to initialise the display
# lcdClear() - called to clear the display
# lcdShowLogo() - show Pi Logo
# lcdDisplay() - called after any changes to render display
# lcdDisplayText(int x, int y, str s, int colour)
# lcdDrawRect(int x0, int y0, int x1, int y1, int colour)
# lcdFillRect(int x0, int y0, int x1, int y1, int colour)
# lcdDrawLine(int x0, int y0, int x1, int y1, int colour)
# lcdDrawCircle(int x, int y, int, rad, int colour)
# lcdFillCircle(int x, int y, int, rad, int colour)
# lcdSetPixel(int x, int y, int colour)
# lcdGetPixel(int x, int y) returns int
# lcdSetTextColour(int colour)
# lcdSetTextSize(int size)
# lcdSetContrast(int contrast)
# lcdSetCursor(int x, int y)
#########################################################
# Released under GPL License
# Ver 0.1 - Andrew Johnson  andrew.johnson@sappsys.co.uk

import time
import sys
sys.path.append('/usr/local/lib/lcd')
from lcd import *

initDisplay()
lcdDisplayText(0,0,"This Raspberry")
lcdDisplayText(0,8,"Pi belongs to ")
lcdSetTextColour(0)
lcdDrawLine(0,19,84,19,1)
lcdDrawLine(0,22,84,22,1)
lcdDisplayText(0,24,"     Me!!!    ")
lcdDrawLine(0,33,84,33,1)
lcdDrawLine(0,36,84,36,1)
lcdSetTextColour(1)
lcdDisplay()
