#!/usr/bin/python
#
# Push LCD information to the front of the pi
#

sys.path.append('/usr/local/lib/lcd')
from lcd import *

def uDisplay():
    while True:
        queueSize = influxQueue.qsize()
        timeNow = time.time()
        # Setting up Engine text
        if engineStatus == False:
            engineText = "   Down"
        else:
            engineText = "     Up"
  
        # Setting up BT Text
        if portName is None:
            btStatus = "       Down"
        else:
            btStatus = "         Up"

        # Setup debug
        if debugOn == True:
            debugMsg = " DEBUG"
        else:
            debugMsg = ""
        if networkStatus == "    Up":
            lcdDisplayText(0,0, "              ")
            lcdDisplayText(0,0, "TIME: "+str(time.strftime("%I:%M:%S")))
        else:
            lcdDisplayText(0, 0, "Key:"+vehicleKey)
        lcdDisplayText(0, 8, "BT:"+btStatus)
        lcdDisplayText(0, 16, "ENGINE:"+engineText)
        lcdDisplayText(0, 24, "NETWORK:"+networkStatus)
        lcdDisplayText(0, 32, "METRICS:"+influxStatus)
        lcdDisplayText(0, 40, "Q:"+str(queueSize)+ " S:"+str(metricsSuccess)+" "+debugMsg)
        lcdDisplay()
        time.sleep(1)


# Kick off display thread
displayThread = Thread(target=uDisplay)
displayThread.setDaemon(True)
displayThread.start()
