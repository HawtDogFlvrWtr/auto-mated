#!/usr/bin/python
# OBD2 Loop routine for metrics
# Created by Christopher Phipps (hawtdogflvrwtr@gmail.com)
# 5/1/2015
#

from Queue import Queue
from threading import Thread
import obd
import sys
sys.path.append('/usr/local/lib/lcd')
from lcd import *
import psutil
import time
import urllib2
import syslog
import ConfigParser
import os.path
import string
import random
import json
import serial
from datetime import datetime

debugOn = False 
obd.debug.console = True
 
# Setup Influx Queue
influxQueue = Queue(maxsize=0)
num_threads = 5 

# Setting initial global variables
global engineStatus
engineStatus = False

global portName
portName = None

global networkStatus
networkStatus = False

global influxStatus
influxStatus = False

global metricSuccess
metricsSuccess = 0

global vehicleKey
global inAction
inAction = 0


# Checking if a config file exists, if it doesn't, then create one and fill it.
configFile = '/etc/uhacknect.conf'
if os.path.isfile(configFile):
    Config = ConfigParser.ConfigParser()
    Config.read(configFile)
    vehicleKey = Config.get('config', 'vehiclekey')
else:
    syslog.syslog('First startup... generating config file')
    vehicleKey = ''.join(random.SystemRandom().choice(string.uppercase + string.digits) for _ in xrange(10))
    cfgFile = open(configFile, 'w')
    Config = ConfigParser.ConfigParser()
    Config.read(configFile)
    Config.add_section('config')
    Config.set('config', 'vehiclekey', vehicleKey)
    try:
        Config.write(cfgFile)
    except:
        syslog.syslog("Failed writing config to "+configFile+".")
    cfgFile.close()

mainHost = "http://www.auto-mated.com/api/influxPush.php?key="+vehicleKey+"&metric="
metricsArray = ["time", "RPM", "SPEED", "TIMING_ADVANCE", "INTAKE_TEMP", "THROTTLE_POS", "MAF", "RUN_TIME", "FUEL_LEVEL", "COOLANT_TEMP", "ENGINE_LOAD", "FUEL_PRESSURE", "INTAKE_PRESSURE", "AMBIANT_AIR_TEMP", "OIL_TEMP"]
metricsList = ','.join([str(x) for x in metricsArray])

def uDisplay():
    initDisplay()
    lcdSetContrast(50)  # Universal contrast value for most lcd's
    lcdShowLogo()
    time.sleep(2)
    while True:
        cpuload = psutil.cpu_percent()
        memused = psutil.virtual_memory()
        rootused = psutil.disk_usage('/')
        queueSize = influxQueue.qsize()
        timeNow = time.time()
        # Setting up network/metric stuff
        if networkStatus == False or influxStatus == False:
            network = "  Down"
        else:
            network = "    Up"
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
        if networkStatus == True:
            lcdDisplayText(0, 0, "              ")
            lcdDisplayText(0, 0, "TIME: "+str(time.strftime("%I:%M:%S")))
        else:
            lcdDisplayText(0, 0, "Key:"+vehicleKey)
        lcdDisplayText(0, 8, "BT:"+btStatus)
        lcdDisplayText(0, 16, "ENGINE:"+engineText)
        lcdDisplayText(0, 24, "NETWORK:"+network)
        lcdDisplayText(0, 32, "              ")
        lcdDisplayText(0, 32, "CM/:"+str(cpuload).split('.', 1)[0]+" "+str(memused.percent).split('.', 1)[0]+" "+str(rootused.percent).split('.', 1)[0]+"")
        lcdDisplayText(0, 40, "              ")
        lcdDisplayText(0, 40, "QT:"+str(queueSize)+ " "+str(metricsSuccess)+" "+debugMsg)
        lcdDisplay()
        time.sleep(1)

# Kick off display thread
displayThread = Thread(target=uDisplay)
displayThread.setDaemon(True)
displayThread.start()

def obdWatch(connection, metric):
    syslog.syslog('Watching: '+metric)
    connection.watch(obd.commands[metric])  # loop through each

def dumpObd(connection, sleepTime):
    connection.stop()
    connection.unwatch_all()
    time.sleep(sleepTime)

def callBack():
    while True:
        if engineStatus == True:
            engineCallback = '1'
        else:
            engineCallback = '0'

        if portName is None:
            elmCallback = '0'
        else:
            elmCallback = '1'
        global networkStatus
        try:
            urllib2.urlopen("http://www.auto-mated.com/api/callback.php?ping&key="+vehicleKey+"&enginestatus="+engineCallback+"&elmstatus="+elmCallback).read()
            syslog.syslog('Pinging auto-mated.com to let them know we are online')
            networkStatus = True
        except:  # Woops, we have no network connection. 
            syslog.syslog('Unable to ping auto-mated.com as the network appears to be down. Trying again')
            networkStatus = False
        time.sleep(10)

def pushInflux(influxQueue):
    while True:
        global influxStatus
        global metricsSuccess
        influxQueueGet = influxQueue.get()
        influxInfo = influxQueueGet.split(':')
        # Attempt to push, loop over if no network connection
        try:
            if debugOn is False:
                output = urllib2.urlopen(mainHost+influxInfo[0]+"&values="+influxInfo[1]).read()
                syslog.syslog('Influxdb Web Return: '+output)
            else:
                syslog.syslog('Debug on.. not pushing to influxdb')
            influxStatus = True
            metricsSuccess += 1
            syslog.syslog(influxInfo[1])
            influxQueue.task_done()  # If success, skim that off the top of the queue
        except:  # If we have no network connection. FIX: NEED TO HAVE THIS WRITE TO A FILE AND UPLOAD WHEN AVAILABLE
            influxQueue.put(influxQueueGet)
            influxQueue.task_done()  # Have to mark it as done anyway, but we roll it back into the Queue. 
            syslog.syslog('Failed sending metric, Tossing record back into queue and trying again.')
            influxStatus = False
        time.sleep(1)
    influxQueue.join()

def checkCodes(connection):
    syslog.syslog('Checking engine for error codes...')
    obdQuery(connection, 'GET_DTC')
    readCodes = connection.query(obd.commands.GET_DTC)
    print readCodes

def getVehicleInfo(connection):
    syslog.syslog('Getting vehicle information')
    obdQuery(connection, 'GET_VIN')
    vinNum = connection.query(obd.commands.GET_VIN)
    print vinNum

def pushAction(action, portName):
    attempts = 2
    buffer = b''
    s = serial.Serial(portName, baudrate=9600)
    s.write('ATZ\r\n')
    time.sleep(1)
    s.write('STP31\r\n')
    s.write('ATSH1C0\r\n')
    s.write(action)
    s.flush()
    while True:
        c = s.read(1)
        # if nothing was received
        if not c:

            if attempts <= 0:
                syslog.syslog('never received prompt character')
                break

            syslog.syslog('found nothing')
            attempts -= 1
            continue
        # end on chevron (ELM prompt character)
        if c == b'>':
            break

        # skip null characters (ELM spec page 9)
        if c == b'\x00':
            continue

        buffer += c

    raw = buffer.encode('ascii', 'ignore')
    return raw
    s.close()

def getActions():
    while True:
        try:
            actionURL = "http://www.auto-mated.com/api/actionPull.php?key="+vehicleKey
            actionOutput = urllib2.urlopen(actionURL).read()
            data = json.loads(actionOutput)
            try:  # Attempt to push, loop over if no network connection
                for actions in data:
                    global inAction
                    inAction = 1
                    if actions['action'] == 'start' and engineStatus == False:
                        syslog.syslog('Remote action found... Starting vehicle')
                        returnOut = pushAction('69AA37901100\r\n', portName)
                    elif actions['action'] == 'stop' and engineStatus == True:
                        syslog.syslog('Remote action found... Stopping vehicle')
                        returnOut = pushAction('6AAA37901100\r\n', portName)
                    elif actions['action'] == 'unlock' and engineStatus == False:
                        syslog.syslog('Remote action found... Unlocking vehicle')
                        returnOut = pushAction('24746C901100\r\n', portName)
                    elif actions['action'] == 'lock' and engineStatus == False:
                        syslog.syslog('Remote action found... Locking vehicle')
                        returnOut = pushAction('21746C901100\r\n', portName)
                while returnOut.find("OK") == -1:
                  syslog.syslog("PUSH OUTPUT: "+returnOut)
                if returnOut.find("OK") != -1:
                    syslog.syslog("PUSH OUTPUT: "+str(returnOut.find("OK")))
                    try:
                        actionCallbackUrl = "http://www.auto-mated.com/api/actionPull.php?key="+vehicleKey+"&id="+actions['id']
                        actionCallbackOutput = urllib2.urlopen(actionCallbackUrl).read()
                        if actionCallbackOutput.find("OK") != -1:
                            syslog.syslog('Marked action as performed')
                            inAction = 0
                    except:
                        syslog.syslog('Failed to submit completion of action.. trying again')
            except:
                syslog.syslog('Something failed in actions... will try again in a bit')
        except:
            syslog.syslog('No actions to perform')
        time.sleep(5)

def mainFunction():
    global engineStatus
    global portName
    while True:
      if inAction == 0:
        if debugOn is True:
            portName = '/dev/pts/17'
            connection = obd.Async('/dev/pts/17')
        else:
            scanPort = obd.scanSerial()
            while len(scanPort) == 0:
                syslog.syslog('No valid device found. Please ensure ELM327 is connected and on. Looping with 5 seconds pause')
                time.sleep(5)
                scanPort = obd.scanSerial()
            portName = scanPort[0] 
            connection = obd.Async()  # Auto connect to obd device

        syslog.syslog('Connected to '+portName+' successfully')
        weConnected = connection.is_connected()
        if weConnected is False:
            engineStatus = False
            syslog.syslog('Engine not started. Checking again in 5...')
        else:
            engineStatus = True
        if engineStatus is True:
            syslog.syslog('Engine is started. Kicking off metrics loop..')
            for metrics in metricsArray:
                if metrics != 'time':
                    obdWatch(connection, metrics)  # Watch all metrics

            connection.start()  # Start async calls now that we're watching PID's
            time.sleep(5)  # Wait for first metrics to come in.

        # FIX: NEED TO MAKE THIS HIS 01 TO DETERMINE SUPPORTED PID'S
        while engineStatus is True:
            if os.path.isfile('/opt/influxback'):  # Check for backup file and push it into the queue for upload.
                syslog.syslog('Old metric data file found... Processing')
                try:
                    with open('/opt/influxback') as f:
                        lines = f.readlines()
                    for line in lines:
                        syslog.syslog('Save data found importing...')
                        syslog.syslog(line)
                        influxQueue.put(line)
                    os.remove('/opt/influxback')  # Kill file after we've dumped them all in the backup. 
                    syslog.syslog('Imported old metric data.')
                except:
                    syslog.syslog('Failed while importing old queue')
            tempValues = []
            timeValue = time.time()
            for metrics in metricsArray:
                try:
                    if metrics == 'time':  # Grab current time if metric is asking to provide the time.
                        value = int(timeValue)
                    else:
                        value = connection.query(obd.commands[metrics])
                        value = value.value
                    if metrics == 'RPM' and value is None:  # Dump if RPM is none
                        dumpObd(connection, 1)
                        valuesList = str(int(timeValue))+",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"  # Push empty values so that gauges reset back to zero on auto-mated.com
                        influxQueue.put(metricsList+':'+valuesList)
                        engineStatus = False  # Kill while above
                        if influxQueue.qsize() > 0 and networkStatus == False:
                            syslog.syslog('Engine off and network down. Saving queue to file.')
                            try:
                                backupFile = open('/opt/influxback', 'w')
                                while influxQueue.qsize():
                                    backupFile.write(influxQueue.get()+"\r\n")
                                    influxQueue.task_done()
                            except:
                                syslog.syslog('Failed writing queue to file.')
                        break  # break from FOR if engine is no longer running
                    else: 
                        tempValues.append(value)
                        engineStatus = True  # Stay in While
                except:
                    dumpObd(connection, 1)
                    valuesList = str(int(timeValue))+",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"  # Push empty values so that gauges reset back to zero on auto-mated.com
                    influxQueue.put(metricsList+':'+valuesList)
                    engineStatus = False  # Kill while above
                    if influxQueue.qsize() > 0 and networkStatus == False:
                        syslog.syslog('Engine off and network down. Saving queue to file.')
                        try:
                            backupFile = open('/opt/influxback', 'w')
                            while influxQueue.qsize():
                                backupFile.write(influxQueue.get()+"\r\n")
                                influxQueue.task_done()
                        except:
                            syslog.syslog('Failed writing queue to file.')
                    break  # break from for if engine is no longer running
            valuesList = ','.join([str(x) for x in tempValues])
            influxQueue.put(metricsList+':'+valuesList)  # Dump metrics to influx queue
            time.sleep(1)
      else:
        syslog.syslog("Skipping metrics and engine check because an action is running")
        time.sleep(5)    

# Kick off influx threads
for i in range(num_threads):
    influxThread = Thread(target=pushInflux, args=(influxQueue,))
    influxThread.setDaemon(True)
    influxThread.start()

# Kick off callback thread
callbackThread = Thread(target=callBack)
callbackThread.setDaemon(True)
callbackThread.start()

# Kick off actions thread
getActionsThread = Thread(target=getActions)
getActionsThread.setDaemon(True)
getActionsThread.start()

mainFunction()  # Lets kick this stuff off
