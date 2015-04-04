"""
A simple Python script to send messages to an ODBLink LX using PyBluez (with Python 2).
"""
 
import bluetooth
import os

# Your mac address 
serverMACAddress = '00:04:3E:08:42:2F'
port = 1
s = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
s.connect((serverMACAddress, port))
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
      s.send('STP31\r\n')
      s.send('ATSH1C0\r\n')
      s.send('69AA37901100\r\n')
    elif ans=="2":
      s.send('STP31\r\n')
      s.send('ATSH1C0\r\n')
      s.send('6AAA37901100\r\n')
    elif ans=="3":
      s.send('STP31\r\n')
      s.send('ATSH1C0\r\n')
      s.send('24746C901100\r\n')
    elif ans=="4":
      s.send('STP31\r\n')
      s.send('ATSH1C0\r\n')
      s.send('21746C901100\r\n')
    elif ans=="5":
      break 
    elif ans !="":
      print("\n Not Valid Choice Try again") 
s.close()
