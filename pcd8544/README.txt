Files in this release :-

README.txt       - This file
PCD8544.pdf      - Introduction PDF
welcome.py       - Python script example that uses the shared object

cpu_show:/
call_lcd.py      - Python script example to call the shared object
compile.sh       - builds the C source and shared object
cpushow          - compiled example C code
lcd.so           - Python shared object
PCD8544.c        - Main code for controlling the display
PCD8544.h        - C Headers
pcd8544_rpi.c    - example C code
pcd8544_rpi_py.c - Python bindings for C functions

Before using any of the python code, the LCD shared object library needs installing.
The compile script in cpu_show/ will do this for you, or you can manually :-
#  mkdir -p /usr/local/lib/lcd
#  cp -fp cpu_show/lcd.so /usr/local/lib/lcd/.
