#!/usr/bin/python
# 
# OBD2 Loop routine for metrics
# Created by Christopher Phipps (hawtdogflvrwtr@gmail.com)
# 5/1/2015
#

import obd
import time

#obd.debug.console = True

def loopMetrics():
    while 1:
        # Loop until engine is shut off then wait
        connection.watch(obd.commands.RPM)
        connection.start()
        connection.stop()
        print connection.query(obd.commands.RPM)
        time.sleep(5)

# Auto connect to obd device
connection = obd.Async('/dev/pts/14')

# Check if connected and continue, else loop
while not connection.is_connected():
    print "No valid device found. Please ensure ELM327 is on and connected. Looping with 5 seconds pause"
    connection = obd.Async('/dev/pts/14')
    time.sleep(5)
print "Connected to device successfully"
connection.watch(obd.commands.RPM)
connection.start()
connection.stop()
checkEngineOn = connection.query(obd.commands.RPM)

# Once connected, check if engine is running
while checkEngineOn.value is None:
    print "Engine is not started. Looping until the vehicle is turned on."
    time.sleep(5)
print "Engine is started.. doing my thing!"
loopMetrics()
