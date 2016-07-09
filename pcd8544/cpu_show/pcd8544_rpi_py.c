/*
=================================================================================
 Name        : pcd8544_rpi_py.c
 Version     : 0.1

 Copyright (C) 2015 by Andrew Johnson - andrew.johnson@sappsys.co.uk
   Based on the work of Andre Wussow, 2012, desk@binerry.de

 Description : Python bindings to build a shared object.
     A simple PCD8544 LCD (Nokia3310/5110) for Raspberry Pi for displaying some system informations.
	 Makes use of WiringPI-library of Gordon Henderson (https://projects.drogon.net/raspberry-pi/wiringpi/)

	 Recommended connection (http://www.raspberrypi.org/archives/384):
	 LCD pins      Raspberry Pi
	 LCD1 - GND    P06  - GND
	 LCD2 - VCC    P01 - 3.3V
	 LCD3 - CLK    P11 - GPIO0
	 LCD4 - Din    P12 - GPIO1
	 LCD5 - D/C    P13 - GPIO2
	 LCD6 - CS     P15 - GPIO3
	 LCD7 - RST    P16 - GPIO4
	 LCD8 - LED    P01 - 3.3V 

================================================================================
This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.
================================================================================
Still to implement :-
void LCDdrawbitmap(uint8_t x, uint8_t y,  const uint8_t *bitmap, uint8_t w, uint8_t h,  uint8_t colo
 */
#include <Python.h>
#include <wiringPi.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/sysinfo.h>
#include <time.h>
#include "PCD8544.h"

// pin setup
int _sclk = 0;
int _din = 1;
int _dc = 2;
int _cs = 3;
int _rst = 4;
  
// lcd contrast 
//may be need modify to fit your screen!  normal: 30- 90 ,default is:45 !!!maybe modify this value!
int contrast = 45;  
  
static PyObject* py_initDisplay(PyObject* self, PyObject* args)
{
  // check wiringPi setup
  if (wiringPiSetup() == -1)
  {
        return Py_BuildValue("i", -1);
  }
  
  // init and clear lcd
  LCDInit(_sclk, _din, _dc, _cs, _rst, contrast);
  LCDclear();
  LCDdisplay();
  return Py_BuildValue("i", 0);
}

static PyObject* py_lcdClear(PyObject* self, PyObject* args)
{
  // Clear the LCD Display
  LCDclear();
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdShowLogo(PyObject* self, PyObject* args)
{
  // Display the Logo
  LCDshowLogo();
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdDisplay(PyObject* self, PyObject* args)
{
  // Process the LCD Display Buffer
  LCDdisplay();
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdDisplayText(PyObject* self, PyObject* args)
{
  int x,y;
  const char *pyarg;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "iis", &x, &y, &pyarg))
    return Py_BuildValue("i", -1); 
  // Display text
  LCDdrawstring_P(x, y, pyarg);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdDrawRect(PyObject* self, PyObject* args)
{
  int x,y,w,h,c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "iiiii", &x, &y, &w, &h, &c))
    return Py_BuildValue("i", -1); 
  // Draw Rectangle
  LCDdrawrect(x, y, w, h, c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdFillRect(PyObject* self, PyObject* args)
{
  int x,y,w,h,c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "iiiii", &x, &y, &w, &h, &c))
    return Py_BuildValue("i", -1); 
  // Draw Filled Rectangle
  LCDfillrect(x, y, w, h, c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdDrawLine(PyObject* self, PyObject* args)
{
  int xa,ya,xb,yb,c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "iiiii", &xa, &ya, &xb, &yb, &c))
    return Py_BuildValue("i", -1); 
  // Draw Line
  LCDdrawline(xa, ya, xb, yb, c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdDrawCircle(PyObject* self, PyObject* args)
{
  int x,y,r,c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "iiii", &x, &y, &r, &c))
    return Py_BuildValue("i", -1); 
  // Draw Circle
  LCDdrawcircle(x, y, r, c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdFillCircle(PyObject* self, PyObject* args)
{
  int x,y,r,c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "iiii", &x, &y, &r, &c))
    return Py_BuildValue("i", -1); 
  // Draw Filled Circle
  LCDfillcircle(x, y, r, c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdSetPixel(PyObject* self, PyObject* args)
{
  int x,y,c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "iii", &x, &y, &c))
    return Py_BuildValue("i", -1); 
  // Draw Pixel
  LCDsetPixel(x, y, c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdGetPixel(PyObject* self, PyObject* args)
{
  int x,y,c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "ii", &x, &y))
    return Py_BuildValue("i", -1); 
  // Query Pixel
  c=LCDgetPixel(x, y);
  return Py_BuildValue("i", c);
}
static PyObject* py_lcdSetTextColour(PyObject* self, PyObject* args)
{
  int c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "i", &c))
    return Py_BuildValue("i", -1); 
  // Set Text Colour
  LCDsetTextColor(c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdSetTextSize(PyObject* self, PyObject* args)
{
  int s;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "i", &s))
    return Py_BuildValue("i", -1); 
  // Set Text Size
  LCDsetTextSize(s);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdSetContrast(PyObject* self, PyObject* args)
{
  int c;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "i", &c))
    return Py_BuildValue("i", -1); 
  // Set Text Contrast
  LCDsetContrast(c);
  return Py_BuildValue("i", 0);
}
static PyObject* py_lcdSetCursor(PyObject* self, PyObject* args)
{
  int x,y;

  // Get passed data to display 
  if (!PyArg_ParseTuple(args, "ii", &x, &y))
    return Py_BuildValue("i", -1); 
  // Set Text Contrast
  LCDsetCursor(x,y);
  return Py_BuildValue("i", 0);
}


/*
 * Bind Python function names to our C functions
 */
static PyMethodDef lcd_methods[] = {
  {"initDisplay", py_initDisplay, METH_VARARGS},
  {"lcdClear", py_lcdClear, METH_VARARGS},
  {"lcdShowLogo", py_lcdShowLogo, METH_VARARGS},
  {"lcdDisplay", py_lcdDisplay, METH_VARARGS},
  {"lcdDisplayText", py_lcdDisplayText, METH_VARARGS},
  {"lcdDrawRect", py_lcdDrawRect, METH_VARARGS},
  {"lcdFillRect", py_lcdFillRect, METH_VARARGS},
  {"lcdDrawLine", py_lcdDrawLine, METH_VARARGS},
  {"lcdDrawCircle", py_lcdDrawCircle, METH_VARARGS},
  {"lcdFillCircle", py_lcdFillCircle, METH_VARARGS},
  {"lcdSetPixel", py_lcdSetPixel, METH_VARARGS},
  {"lcdGetPixel", py_lcdGetPixel, METH_VARARGS},
  {"lcdSetTextColour", py_lcdSetTextColour, METH_VARARGS},
  {"lcdSetTextSize", py_lcdSetTextSize, METH_VARARGS},
  {"lcdSetContrast", py_lcdSetContrast, METH_VARARGS},
  {"lcdSetCursor", py_lcdSetCursor, METH_VARARGS},
  {NULL, NULL}
};

/*
 * Python calls this to let us initialize our module
 */
void initlcd()
{
  (void) Py_InitModule("lcd", lcd_methods);
}
