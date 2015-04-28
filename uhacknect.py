"""
A simple Python script to send messages to an ODBLink LX using PyBluez (with Python 2).
"""
 
import serial
import os

s = serial.Serial( "/dev/rfcomm0", baudrate=38400 )
s.write('STP31\r\n')
s.write('ATSH1C0\r\n')
s.write('STP31\r\n')
s.write('ATSH1C0\r\n')
s.write('STP31\r\n')
s.write('ATSH1C0\r\n')
s.write('STP31\r\n')
s.write('ATSH1C0\r\n')
ans=True
while ans:
    print ("""
    1.Start
    2.Stop
    3.Unlock
    4.Lock
    5.Exit/Quit
    """)
    ans=raw_input("What would you like to do? ") 
    if ans=="1": 
      s.write('69AA37901100\r\n')
    elif ans=="2":
      s.write('6AAA37901100\r\n')
    elif ans=="3":
      s.write('24746C901100\r\n')
    elif ans=="4":
      s.write('21746C901100\r\n')
    elif ans=="5":
      break 
    elif ans !="":
      print("\n Not Valid Choice Try again") 
s.close()
