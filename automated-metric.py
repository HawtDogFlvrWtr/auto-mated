#!/usr/bin/python
# OBD2 Loop routine for metrics
# Created by Christopher Phipps (hawtdogflvrwtr@gmail.com)
# 5/1/2015
#

debugOn = False 

from Queue import Queue
from threading import Thread
import obd
import sys
if debugOn is not True:
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
import requests
from datetime import datetime
from netifaces import interfaces, ifaddresses, AF_INET

obd.debug.console = False 

 
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
inAction = False

def outLog(logLine):
  if debugOn is True:
    print(logLine)
  else:
    print(logLine)

# Checking if a config file exists, if it doesn't, then create one and fill it.
configFile = '/etc/uhacknect.conf'
if os.path.isfile(configFile):
    Config = ConfigParser.ConfigParser()
    Config.read(configFile)
    vehicleKey = Config.get('config', 'vehiclekey')
else:
    outLog('First startup... generating config file')
    vehicleKey = ''.join(random.SystemRandom().choice(string.uppercase + string.digits) for _ in xrange(10))
    cfgFile = open(configFile, 'w')
    Config = ConfigParser.ConfigParser()
    Config.read(configFile)
    Config.add_section('config')
    Config.set('config', 'vehiclekey', vehicleKey)
    try:
        Config.write(cfgFile)
    except:
        outLog("Failed writing config to "+configFile+".")
    cfgFile.close()

acceptedMetrics = {'03': 'FUEL_STATUS', '04': 'ENGINE_LOAD', '05': 'COOLANT_TEMP', '06': 'SHORT_FUEL_TRIM_1',
                   '07': 'LONG_FUEL_TRIM_1', '08': 'SHORT_FUEL_TRIM_2', '09': 'LONG_FUEL_TRIM_2', '0A': 'FUEL_PRESSURE',
                   '0B': 'INTAKE_PRESSURE', '0C': 'RPM', '0D': 'SPEED', '0E': 'TIMING_ADVANCE', '0F': 'INTAKE_TEMP',
                   '10': 'MAF', '11': 'THROTTLE_POS', '12': 'AIR_STATUS', '13': 'O2_SENSORS', '14': 'O2_B1S1',
                   '15': 'O2_B1S2', '16': 'O2_B1S3', '17': 'O2_B1S4', '18': 'O2_B2S1', '19': 'O2_B2S2', '1A': 'O2_B2S3',
                   '1B': 'O2_B2S4', '1D': 'O2_SENSORS_ALT', '21': 'DISTANCE_W_MIL', '22': 'FUEL_RAIL_PRESSURE_VAC',
                   '23': 'FUEL_RAIL_PRESSURE_DIRECT', '24': 'O2_S1_WR_VOLTAGE', '25': 'O2_S2_WR_VOLTAGE',
                   '26': 'O2_S3_WR_VOLTAGE', '27': 'O2_S4_WR_VOLTAGE', '28': 'O2_S5_WR_VOLTAGE', '29': 'O2_S6_WR_VOLTAGE',
                   '2A': 'O2_S7_WR_VOLTAGE', '2B': 'O2_S8_WR_VOLTAGE', '2F': 'FUEL_LEVEL', '31': 'DISTANCE_SINCE_DTC_CLEAR',
                   '33': 'BAROMETRIC_PRESSURE', '34': 'O2_S1_WR_CURRENT', '35': 'O2_S2_WR_CURRENT',
                   '36': 'O2_S3_WR_CURRENT', '37': 'O2_S4_WR_CURRENT', '38': 'O2_S5_WR_CURRENT', '39': 'O2_S6_WR_CURRENT',
                   '3A': 'O2_S7_WR_CURRENT', '3B': 'O2_S8_WR_CURRENT', '3C': 'CATALYST_TEMP_B1S1', '3D': 'CATALYST_TEMP_B2S1',
                   '3E': 'CATALYST_TEMP_B1S2', '3F': 'CATALYST_TEMP_B2S2', '41': 'STATUS_DRIVE_CYCLE', '42': 'CONTROL_MODULE_VOLTAGE',
                   '43': 'ABSOLUTE_LOAD', '44': 'COMMAND_EQUIV_RATIO', '45': 'RELATIVE_THROTTLE_POS', '46': 'AMBIANT_AIR_TEMP',
                   '4B': 'ACCELERATOR_POS_F', '4C': 'THROTTLE_ACTUATOR', '4D': 'RUN_TIME_MIL', '4E': 'TIME_SINCE_DTC_CLEARED',
                   '52': 'ETHANOL_PERCENT', '53': 'EVAP_VAPOR_PRESSURE_ABS', '54': 'EVAP_VAPOR_PRESSURE_ALT',
                   '55': 'SHORT_O2_TRIM_B1', '56': 'LONG_O2_TRIM_B1', '57': 'SHORT_O2_TRIM_B2', '58': 'LONG_O2_TRIM_B2',
                   '59': 'FUEL_RAIL_PRESSURE_ABS', '5A': 'RELATIVE_ACCEL_POS', '5B': 'HYBRID_BATTERY_REMAINING',
                   '5C': 'OIL_TEMP', '5D': 'FUEL_INJECT_TIMING', '5E': 'FUEL_RATE', '5F': 'EMISSION_REQ'
                  }

def ip4_addresses():
  ip_list = []
  for interface in interfaces():
    try:
      for link in ifaddresses(interface)[AF_INET]:
        if link['addr'] != '127.0.0.1':
          ip_list.append(link['addr'])
    except:
      outLog("Interface: "+interface+" issue")
  return ip_list

def uDisplay():
  if debugOn is not True:
    initDisplay()
    lcdSetContrast(50)  # Universal contrast value for most lcd's
    lcdShowLogo()
    time.sleep(2)
    while True:
      cpuload = psutil.cpu_percent()
      memused = psutil.virtual_memory()
      rootused = psutil.disk_usage('/')
      queueSize = influxQueue.qsize()
      # Setting up network/metric stuff
      if networkStatus is False:
        network = "  Down"
      else:
        network = "    Up"
      # Setting up Engine text
      if engineStatus is False:
        engineText = "   Down"
      else:
        engineText = "     Up"
  
      # Setting up BT Text
      if portName is None:
        btStatus = "      Down"
      else:
        btStatus = "        Up"

      # Setup debug
      if debugOn is True:
        debugMsg = " DEBUG"
      else:
        debugMsg = ""
      if networkStatus is True:
        lcdDisplayText(0, 0, "              ")
        try:
          lcdDisplayText(0, 0, ip4_addresses()[0])
        except:
          lcdDisplayText(0, 0, "NO IP")
      else:
        lcdDisplayText(0, 0, "Key:"+vehicleKey)
      lcdDisplayText(0, 8, "OBD:"+btStatus)
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

def obdWatch(connection, acceptedMetrics):
  metricsArray = []
  for supported in connection.supported_commands:
    supported = str(supported)
    if supported[:2] == "01":
      supported = supported.split(":")[0][2:]
      if acceptedMetrics.get(supported, None) is not None:
        metricsArray.append(acceptedMetrics.get(supported, None))
  for metric in metricsArray:
    outLog("Adding: "+str(metric))
    connection.watch(obd.commands[metric])
  return metricsArray

def dumpObd(connection, sleepTime):
  connection.stop()
  connection.unwatch_all()
  time.sleep(sleepTime)

def callBack():
  while True:
    if engineStatus is True:
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
      outLog('Pinging auto-mated.com to let them know we are online')
      networkStatus = True
    except:  # Woops, we have no network connection. 
      outLog('Unable to ping auto-mated.com as the network appears to be down. Trying again')
      networkStatus = False
    time.sleep(10)

def pushInflux(influxQueue):
  while True:
    if networkStatus is True:
      global influxStatus
      global metricsSuccess
      influxQueueGet = influxQueue.get()
      # Attempt to push, loop over if no network connection
      try:
        #outLog("Pushing to Influxdb")
        headers = {'Content-type': 'application/json'}
        req = requests.post('http://www.auto-mated.com/api/influxPush.php?key='+vehicleKey, data=json.dumps(influxQueueGet), headers=headers)
        influxQueue.task_done()  # If success, skim that off the top of the queue
        influxStatus = True
        metricsSuccess += 1
      except:  # If we have no network connection. FIX: NEED TO HAVE THIS WRITE TO A FILE AND UPLOAD WHEN AVAILABLE
        influxQueue.put(influxQueueGet)
        influxQueue.task_done()  # Have to mark it as done anyway, but we roll it back into the Queue. 
        outLog('Failed sending metric, Tossing record back into queue and trying again.')
        influxStatus = False
      time.sleep(0.25)

def checkCodes(connection):
  outLog('Checking engine for error codes...')
  obdQuery(connection, 'GET_DTC')
  readCodes = connection.query(obd.commands.GET_DTC)
  print readCodes

def getVehicleInfo(connection):
  outLog('Getting vehicle information')
  obdQuery(connection, 'GET_VIN')
  vinNum = connection.query(obd.commands.GET_VIN)
  print vinNum

def pushAction(action, portName):
  attempts = 2
  buffer = b''
  s = serial.Serial(portName, baudrate=9600)
  s.write('ATZ\r\n')
  time.sleep(1)
  for writeData in ['STP31', 'ATSH1C0', action]:
    s.write(writeData+'\r\n')
  s.flush()
  while True:
    c = s.read(1)
    # if nothing was received
    if not c:
      if attempts <= 0:
        outLog('never received prompt character')
        break
      outLog('found nothing')
      attempts -= 1
      continue
    # end on chevron (ELM prompt character)
    if c == b'>':
      break
    # skip null characters (ELM spec page 9)
    if c == b'\x00':
      continue
    buffer += c
    time.sleep(0.25)
  raw = buffer.encode('ascii', 'ignore')
  return raw
  s.close()

def getActions():
  while True:
    if portName is not None and networkStatus is True:
      try:
        actionURL = "http://www.auto-mated.com/api/actionPull.php?key="+vehicleKey
        actionOutput = urllib2.urlopen(actionURL).read()
        data = json.loads(actionOutput)
        try:  # Attempt to push, loop over if no network connection
          for actions in data:
            global inAction
            inAction = True
            if actions['action'] == 'start' and engineStatus is False:
              outLog('Remote action found... Starting vehicle')
              returnOut = pushAction('69AA37901100', portName)
            elif actions['action'] == 'stop' and engineStatus is True:
              outLog('Remote action found... Stopping vehicle')
              returnOut = pushAction('6AAA37901100', portName)
            elif actions['action'] == 'unlock' and engineStatus is False:
              outLog('Remote action found... Unlocking vehicle')
              returnOut = pushAction('24746C901100', portName)
            elif actions['action'] == 'lock' and engineStatus is False:
              outLog('Remote action found... Locking vehicle')
              returnOut = pushAction('21746C901100', portName)
          while returnOut.find("OK") == -1:
            outLog("PUSH OUTPUT: "+returnOut)
            if returnOut.find("OK") != -1:
              outLog("PUSH OUTPUT: "+str(returnOut.find("OK")))
              try:
                actionCallbackUrl = "http://www.auto-mated.com/api/actionPull.php?key="+vehicleKey+"&id="+actions['id']
                actionCallbackOutput = urllib2.urlopen(actionCallbackUrl).read()
                if actionCallbackOutput.find("OK") != -1:
                  outLog('Marked action as performed')
                  inAction = False 
              except:
                outLog('Failed to submit completion of action.. trying again')
        except:
          outLog('Something failed in actions... will try again in a bit')
      except:
        outLog('No actions to perform')
    time.sleep(5)

def mainFunction():
  global engineStatus
  global portName
  scanPort = []
  while True:
    if inAction is False:
      if debugOn is True:
        portName = '/dev/pts/21'
        connection = obd.Async(portName)
      else:
        while len(scanPort) == 0:
          outLog('No valid device found. Please ensure ELM327 is connected and on. Looping with 5 seconds pause')
          scanPort = obd.scan_serial()
          time.sleep(5)
        portName = scanPort[0] 
        connection = obd.Async(portName)  # Auto connect to obd device
      time.sleep(2)
      outLog('Connected to '+portName+' successfully')
      
      while engineStatus is False:
        if inAction is False:
          connection.watch(obd.commands.RPM)
          connection.start()
          time.sleep(5)
          outLog('Watching RPM to see if engine is running')
          checkEngineOn = connection.query(obd.commands.RPM)
          outLog('Engine RPM: '+str(checkEngineOn.value))
          if checkEngineOn.is_null():  # Check if we have an RPM value.. if not return false
            outLog('Engine is not running, checking again')
            engineStatus = False
            if not connection.is_connected():
              break  # Break out of while and attempt to reconnect to the OBD port.. car is probably off!
            connection.unwatch_all()
            time.sleep(5)
          else:
            dumpObd(connection, 1)
            engineStatus = True
      if engineStatus is True:
        connection = obd.Async(portName)
        outLog('Engine is started. Kicking off metrics loop..')
        metricsArray = obdWatch(connection, acceptedMetrics)  # Watch all metrics
        connection.start()  # Start async calls now that we're watching PID's
        time.sleep(5)  # Wait for first metrics to come in.
        if os.path.isfile('/opt/influxback'):  # Check for backup file and push it into the queue for upload.
          outLog('Old metric data file found... Processing')
          try:
            with open('/opt/influxback') as f:
              lines = f.readlines()
            for line in lines:
              outLog('Save data found importing...')
              influxQueue.put(line)
            os.remove('/opt/influxback')  # Kill file after we've dumped them all in the backup. 
            outLog('Imported old metric data.')
          except:
            outLog('Failed while importing old queue')

        while engineStatus is True:
          metricDic = {}
          currentTime = time.time()
          for metricName in metricsArray:
            value = connection.query(obd.commands[metricName])
            metricDic.update({'time': currentTime})
            if value.value is not None:
              metricDic.update({metricName: value.value})
          if metricDic.get('RPM') is None:  # Dump if RPM is none
            outLog("Engine has stopped. Dropping update")
            dumpObd(connection, 1)
            for metric in metricDic:
              if metric != 'time':
                metricDic.update({metric: 0})
            influxQueue.put(json.dumps(metricDic))
            engineStatus = False  # Kill while above
            if influxQueue.qsize() > 0 and networkStatus is False:
              outLog('Engine off and network down. Saving queue to file.')
              try:
                backupFile = open('/opt/influxback', 'w')
                while influxQueue.qsize() > 0:
                  backupFile.write(influxQueue.get()+"\r\n")
                  influxQueue.task_done()
              except:
                outLog('Failed writing queue to file.')
            break  # break from FOR if engine is no longer running
          else: 
            engineStatus = True  # Stay in While
          influxQueue.put(metricDic)  # Dump metrics to influx queue
          time.sleep(5)
    else:
      if engineStatus is True:
        dumpObd(connection, 1)
      outLog("Skipping metrics and engine check because an action is running")
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
