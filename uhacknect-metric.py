#!/usr/bin/python
# 
# OBD2 Loop routine for metrics
# Created by Christopher Phipps (hawtdogflvrwtr@gmail.com)
# 5/1/2015
#

import obd
import time
import urllib2
import syslog
import ConfigParser
import os.path
import string
import random
import json
import serial

debugOn = False
#obd.debug.console = True
# Checking if a config file exists, if it doesn't, then create one and fill it.
configFile = '/etc/uhacknect.conf'
if os.path.isfile(configFile):
    Config = ConfigParser.ConfigParser()
    Config.read(configFile)
    vehicleKey = Config.get('config', 'vehiclekey')
else:
    syslog.syslog('First startup... generating config file')
    vehicleKey = ''.join(random.SystemRandom().choice(string.uppercase + string.digits) for _ in xrange(10))
    cfgFile = open(configFile,'w')
    Config = ConfigParser.ConfigParser()
    Config.read(configFile)
    Config.add_section('config')
    Config.set('config','vehiclekey',vehicleKey)
    try:
        Config.write(cfgFile)
    except:
        syslog.syslog("Failed writing config to "+configFile+".")
    cfgFile.close()

mainHost = "http://www.uhacknect.com/api/influxPush.php?key="+vehicleKey+"&metric="
metricsArray = ["RPM","SPEED","TIMING_ADVANCE","INTAKE_TEMP","THROTTLE_POS","MAF","RUN_TIME","FUEL_LEVEL","COOLANT_TEMP","ENGINE_LOAD","FUEL_PRESSURE","INTAKE_PRESSURE","AMBIANT_AIR_TEMP","OIL_TEMP","FUEL_RATE"]
metricsList = ','.join([str(x) for x in metricsArray])


def obdWatch(connection,metric):
    syslog.syslog('Watching: '+metric)
    connection.watch(obd.commands[metric]) #loop through each 

def dumpObd(connection):
    connection.stop()
    connection.unwatch_all()

def pushInflux(mainHost, metricsList, valuesList, connection):
    # Attempt to push, loop over if no network connection
    try:
        output = urllib2.urlopen(mainHost+metricsList+"&values="+valuesList).read()
    except: # If we have no network connection. FIX: NEED TO HAVE THIS WRITE TO A FILE AND UPLOAD WHEN AVAILABLE
        syslog.syslog('Network connection down, looping until its up')
    syslog.syslog('Influxdb Web Return: '+output)
    

def mainLoop(connection,portName):
    dumpObd(connection)
    for metrics in metricsArray:
      obdWatch(connection,metrics) # Watch all metrics

    connection.start() # Start async calls now that we're watching PID's
    time.sleep(5) #Wait for first metrics to come in.
    
    # FIX: NEED TO MAKE THIS HIS 01 TO DETERMINE SUPPORTED PID'S
    while 1:
        tempValues = []
        for metrics in metricsArray:
            value = connection.query(obd.commands[metrics])
            if metrics == 'RPM' and value.value is None: # Dump if RPM is none
                dumpObd(connection)
                valuesList = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0" # Push empty values so that gauges reset back to zero on uhacknect.com
                #pushInflux(mainHost, metricsList, valuesList, connection)
                break # jump from while if engine is no longer running
            tempValues.append(value.value)
        getActions(connection,portName,'on')
        valuesList = ','.join([str(x) for x in tempValues])
        syslog.syslog('Influx Metrics List: '+metricsList)
        syslog.syslog('Influx Values List: '+valuesList)
        #pushInflux(mainHost, metricsList, valuesList, connection)
        time.sleep(5)

def checkCodes(connection):
    syslog.syslog('Checking engine for error codes...')
    obdQuery(connection,'STATUS')
    errorCodes = connection.query(obd.commands.STATUS)
    obdQuery(connection,'GET_DTC')
    readCodes  = connection.query(obd.commands.GET_DTC)
    print errorCodes
    print readCodes

def getVehicleInfo(connection):
    syslog.syslog('Getting vehicle information')
    obdQuery(connection,'GET_VIN')
    vinNum = connection.query(obd.commands.GET_VIN)
    print vinNum

def checkEngineOn(connection,portName):
    # Once connected, check if engine is running
    dumpObd(connection)
    obdWatch(connection,'RPM') # Start watching RPM
    connection.start()
    time.sleep(5)
    checkEngineOn = connection.query(obd.commands.RPM)
    syslog.syslog('Engine is not started. Looping until the vehicle is turned on.')
    dumpObd(connection)
    if checkEngineOn.value == None: #Check if we have an RPM value.. if not return false
      return False
    else: 
      return True

def pushAction(action,portName):
    attempts = 2
    buffer = b''
    s = serial.Serial( portName, baudrate=38400 )
    s.write('STP31\r\n')
    s.write('ATSH1C0\r\n')
    s.write('STP31\r\n')
    s.write('ATSH1C0\r\n')
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

    raw = buffer.encode('ascii','ignore')
    return raw
    s.close()
    
def getActions(connection,portName,engineStatus):
  try:
    actionURL = "http://www.uhacknect.com/api/actionPull.php?key="+vehicleKey
    actionOutput = urllib2.urlopen(actionURL).read()
    data = json.loads(actionOutput)
    try: # Attempt to push, loop over if no network connection
        for actions in data:
          if actions['action'] == 'start' and engineStatus == 'off' :
              syslog.syslog('Remote action found... Starting vehicle')
              returnOut = pushAction('69AA37901100\r\n',portName)
          elif actions['action'] == 'stop' and engineStatus == 'on' :
              syslog.syslog('Remote action found... Stopping vehicle')
              returnOut = pushAction('6AAA37901100\r\n',portName)
          elif actions['action'] == 'unlock':
              syslog.syslog('Remote action found... Unlocking vehicle')
              returnOut = pushAction('24746C901100\r\n',portName)
          elif actions['action'] == 'lock':
              syslog.syslog('Remote action found... Locking vehicle')
              returnOut = pushAction('21746C901100\r\n',portName)

        if returnOut.find("OK") != -1:
          try:
            actionCallbackUrl = "http://www.uhacknect.com/api/actionPull.php?key="+vehicleKey+"&id="+actions['id']
            actionCallbackOutput = urllib2.urlopen(actionCallbackUrl).read()
            if actionCallbackOutput.find("OK") != -1:
              syslog.syslog('Marked action as performed')
          except:
            syslog.syslog('Failed to submit completion of action.. trying again')
    except:
          syslog.syslog('Something failed in actions... will try again in a bit')

  except:
      syslog.syslog('No actions to perform')
	

def mainFunction():
    while True:
      if debugOn == True:
        portName = '/dev/pts/17'
        connection = obd.Async('/dev/pts/17')
      else: 
        portScan = obd.scanSerial() # Check if connected and continue, else loop
        while len(portScan) == 0:
            syslog.syslog('No valid device found. Please ensure ELM327 is connected and on. Looping with 5 seconds pause')
            portScan = obd.scanSerial()
            time.sleep(5)
        connection = obd.Async() # Auto connect to obd device
        portName = portScan[0]

      syslog.syslog('Connected to '+portName+' successfully')
      #getVehicleInfo(connection)
      #checkCodes(connection)
      engineStatus = checkEngineOn(connection,portName)
      while engineStatus == False:
        syslog.syslog('Engine is not running, checking again in 5 seconds...')
        engineStatus = checkEngineOn(connection,portName)
        getActions(connection,portName,'off')
      syslog.syslog('Engine is started. Kicking off metrics loop..')
      mainLoop(connection,portName)

mainFunction()# Lets kick this stuff off

