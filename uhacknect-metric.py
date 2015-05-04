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


def obdQuery(connection,metric):
    connection.watch(obd.commands[metric])
    connection.start()
    connection.stop()
    

def pushInflux(mainHost, metricsList, valuesList, connection):
    # Attempt to push, loop over if no network connection
    try:
        output = urllib2.urlopen(mainHost+metricsList+"&values="+valuesList).read()
    except:
        # If we have no network connection, just loop through the entry until we get a connection again. FIX: NEED TO HAVE THIS WRITE TO A FILE AND UPLOAD WHEN AVAILABLE
        mainLoop(connection)
    syslog.syslog('Influxdb Web Return: '+output)
    time.sleep(5)
    

def mainLoop(connection):
    # FIX: NEED TO MAKE THIS HIS 01 TO DETERMINE SUPPORTED PID'S
    while 1:
        tempValues = []
        for metrics in metricsArray:
            # Loop until engine is shut off then wait
            obdQuery(connection,metrics)
            value = connection.query(obd.commands[metrics])
            # Dump if RPM is none
            if metrics == 'RPM' and value.value is None:
                connection.unwatch_all()
                checkEngineOn(connection)
                valuesList = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
                # Push empty values so that gauges reset back to zero on uhacknect.com
                pushInflux(mainHost, metricsList, valuesList, connection)
            tempValues.append(value.value)
        valuesList = ','.join([str(x) for x in tempValues])
        # Check if we've been disconnected
        syslog.syslog('Influx Metrics List: '+metricsList)
        syslog.syslog('Influx Values List: '+valuesList)
        pushInflux(mainHost, metricsList, valuesList, connection)

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

def checkEngineOn(connection):
    # Once connected, check if engine is running
    obdQuery(connection,'RPM')
    checkEngineOn = connection.query(obd.commands.RPM)
    while checkEngineOn.value is None:
        syslog.syslog('Engine is not started. Looping until the vehicle is turned on.')
        time.sleep(5)
        obdQuery(connection,'RPM')
        checkEngineOn = connection.query(obd.commands.RPM)
    syslog.syslog('Engine is started..')
 
    try:
        mainLoop(connection)
    except:
        syslog.syslog('Caught escape key... exiting')
        valuesList = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
        # Push empty values so that gauges reset back to zero on uhacknect.com
        pushInflux(mainHost, metricsList, valuesList, connection)

def getActions():
    print "Test"

def kickOff():
    # Auto connect to obd device
    syslog.syslog('Testing dev interface before real interface')
    connection = obd.Async('/dev/pts/0')
    # Check if connected and continue, else loop
    while not connection.is_connected():
        syslog.syslog('No valid device found. Please ensure ELM327 is on and connected. Looping with 5 seconds pause')
        connection = obd.Async()
        time.sleep(5)
    syslog.syslog('Connected to '+connection.get_port_name()+' successfully')
    getVehicleInfo(connection)
    checkCodes(connection)
    checkEngineOn(connection)

kickOff()

