#!/bin/bash
# Compile the main cpushow executable
echo "Building cpushow"
gcc -o cpushow pcd8544_rpi.c PCD8544.c  -L/usr/local/lib -lwiringPi

# Compile a shard object library that can be used in Python - may need to change location of Python libraries
# depending on version of Python installed
VER=NONE
if [ -f /usr/include/python2.6/Python.h ]
then
  VER=python2.6
fi
if [ -f /usr/include/python2.7/Python.h ]
then
  VER=python2.7
fi
if [ "$VER" != "NONE" ]
then
  echo "Found Python version : "$VER
  echo "Building Shared Object Library lcd.so"
  gcc -shared -I /usr/include/$VER/ -l$VER -o lcd.so pcd8544_rpi_py.c PCD8544.c  -L/usr/local/lib -lwiringPi
  echo "Installing Shared Object Library lcd.so"
  mkdir -p /usr/local/lib/lcd
  cp -fp lcd.so /usr/local/lib/lcd/.
else
  echo "Python.h Library not found - Python 2.7 recommended"
fi
