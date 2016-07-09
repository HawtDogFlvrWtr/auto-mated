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

import sys,time
sys.path.append('/usr/local/lib/lcd')
from lcd import *

initDisplay()
lcdSetContrast(50)
lcdSetTextSize(5)
lcdSetTextColour(1)
lcdFillRect(0, 0, 84, 48, 1)

lcdSetPixel(1, 2, 0)	
lcdDisplay()
