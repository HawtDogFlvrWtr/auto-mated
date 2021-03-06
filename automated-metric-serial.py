#!/usr/bin/python
# OBD2 Loop routine for metrics
# Created by Christopher Phipps (hawtdogflvrwtr@gmail.com)
# 7/12/2016
#

debugOn = False

from Queue import Queue
from threading import Thread
import obd
import sys
import psutil
import time
import urllib2, ssl
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

#obd.logger.setLevel(obd.logging.DEBUG)
# Disable certificate checking
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Setup Influx Queue
influxQueue = Queue(maxsize=0)
num_threads = 5 

# Setting initial global variables
global engineStatus
engineStatus = False

global portName
portName = '/dev/ttyUSB0'

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
    syslog.syslog(logLine)

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

acceptedMetrics = {'04': 'ENGINE_LOAD', '05': 'COOLANT_TEMP', '06': 'SHORT_FUEL_TRIM_1',
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
                   '43': 'ABSOLUTE_LOAD', '45': 'RELATIVE_THROTTLE_POS', '46': 'AMBIANT_AIR_TEMP',
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
      val = null
  return ip_list

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
  connection.close()
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
      urllib2.urlopen("https://automated.wreckyour.net/api/callback.php?ping&key="+vehicleKey+"&enginestatus="+engineCallback+"&elmstatus="+elmCallback, context=ctx).read()
      outLog('Pinging wreckyour.net to let them know we are online')
      networkStatus = True
    except:  # Woops, we have no network connection. 
      outLog('Unable to ping wreckyour.net as the network appears to be down. Trying again')
      networkStatus = False
    time.sleep(30)

def pushInflux(influxQueue):
  while True:
    if networkStatus is True:
      global influxStatus
      global metricsSuccess
      influxQueueGet = influxQueue.get()
      # Attempt to push, loop over if no network connection
      try:
        outLog("Pushing to Influxdb")
        headers = {'Content-type': 'application/json'}
        req = requests.post('https://automated.wreckyour.net/api/influxPush.php?key='+vehicleKey, data=json.dumps(influxQueueGet), headers=headers, verify=False)
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
  s = serial.Serial(port=portName, timeout=1, baudrate=115200) 
  s.flushInput()
  for writeData in ['ATZ', 'ATE0', 'ATH1', 'ATL0', 'ATTP6', 'STP31', 'ATSH1C0', action]:
    s.write(writeData+'\r\n')
    #s.flush()
    time.sleep(0.30)
  raw = s.readline()
  outLog("Output: "+raw)
  s.close()
  if 'DATA' in raw:
    return True
  else:
    return False

def getActions():
  while True:
    if portName is not None:
      while networkStatus is True:
        try:
          actionURL = "https://automated.wreckyour.net/api/actionPull.php?key="+vehicleKey
          actionOutput = urllib2.urlopen(actionURL, context=ctx).read()
          data = json.loads(actionOutput)
          #var_dump(data)
          try:  # Attempt to push, loop over if no network connection
            for actions in data:
              global inAction
              inAction = True
              time.sleep(2)
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
              else:
                outLog('Cant perform action for one reason or another')
            if returnOut is True:
              try:
                actionCallbackUrl = "https://automated.wreckyour.net/api/actionPull.php?key="+vehicleKey+"&id="+actions['id']
                actionCallbackOutput = urllib2.urlopen(actionCallbackUrl, context=ctx).read()
                if actionCallbackOutput.find("OK") != -1:
                  outLog('Marked action as performed')
                  inAction = False 
              except:
                outLog('Failed to submit completion of action.. Network issue?')
            else:
              outLog('Action failed to perform. Trying again')
          except:
            outLog('Something failed in actions... will try again in a bit')
        except:
          outLog('No actions to perform')
        time.sleep(20)

def mainFunction():
  global engineStatus
  global portName
  scanPort = []
  scanPort = obd.scan_serial()
  while True:
    if inAction is False:
      connection = obd.Async(portstr=portName, fast=False, baudrate=115200, protocol="6")
      if obd.OBDStatus.CAR_CONNECTED == "Car Connected":
        dumpObd(connection, 1) 
        portName = portName
        outLog('Connected to '+portName+' successfully')
      elif obd.OBDStatus.CAR_CONNECTED != "Car Connected":
          outLog("Not connected to car yet")
          time.sleep(30)
      elif obd.OBDStatus.ELM_CONNECTED == "ELM Connected":
          outLog("Connected to ELM but not vehicle")
          time.sleep(30)
      else:
          outLog("Not connected to ELM or Car")
          time.sleep(30)
      
      while engineStatus is False:
        if inAction is False:
          connection = obd.OBD(portstr=portName, fast=False, baudrate=115200, protocol="6")
          time.sleep(2)
          outLog('Checking RPM to see if engine is running')
          checkEngineOn = connection.query(obd.commands.RPM)
          outLog('Engine RPM: '+str(checkEngineOn.value))
          if checkEngineOn.is_null():  # Check if we have an RPM value.. if not return false
            outLog('Engine is not running, checking again in 2 minutes') # HAVE TO CHECK SO LONG BECAUSE IT TURNS ON THE CAR LIGHTS BRIEFLY
            engineStatus = False
            connection.close()
            time.sleep(120)
          else:
            connection.close()
            engineStatus = True
      if engineStatus is True:
        connection = obd.Async(portstr=portName, fast=False, baudrate=115200, protocol="6")
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
            value = str(connection.query(obd.commands[metricName]))
            value = value.split(' ')
            metricDic.update({'time': currentTime})
            if value[0] is not None:
              metricDic.update({metricName: value[0]})
          print connection.query(obd.commands['RPM'])
          if connection.query(obd.commands['RPM']).is_null():  # Dump if RPM is none
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
