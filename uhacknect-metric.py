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

#obd.debug.console = True

def loopMetrics(connection):
    metricsArray = ["RPM","SPEED","TIMING_ADVANCE","INTAKE_TEMP","THROTTLE_POS","MAF","RUN_TIME","FUEL_LEVEL","COOLANT_TEMP","ENGINE_LOAD","FUEL_PRESSURE","INTAKE_PRESSURE","AMBIANT_AIR_TEMP","OIL_TEMP","FUEL_RATE"]
    metricsList = ','.join([str(x) for x in metricsArray])
    while 1:
        tempValues = []
        for metrics in metricsArray:
            # Loop until engine is shut off then wait
            metricName = 'obd.commands.'+metrics
            connection.watch(obd.commands[metrics])
            connection.start()
            connection.stop()
            value = connection.query(obd.commands[metrics])
            # Dump if RPM is none
            if metrics == 'RPM' and value.value is None:
                connection.unwatch_all()
                kickOff()
            tempValues.append(value.value)
        mainHost = "http://www.uhacknect.com/api/influxPush.php?vin=3C4PDCGG4FT641185&api=6054-4220-2524-3963&metric="
        valuesList = ','.join([str(x) for x in tempValues])
        # Check if we've been disconnected
        syslog.syslog('Influx Metrics List: '+metricsList)
        syslog.syslog('Influx Values List: '+valuesList)
        # Attempt to push, loop over if no network connection
        try:
            output = urllib2.urlopen(mainHost+metricsList+"&values="+valuesList).read()
        except:
            loopMetrics(connection)
        syslog.syslog('Influxdb Web Return: '+output)
        time.sleep(5)


def kickOff():
    # Auto connect to obd device
    syslog.syslog('Testing dev interface before real interface')
    connection = obd.Async('/dev/pts/14')
    # Check if connected and continue, else loop
    while not connection.is_connected():
        syslog.syslog('No valid device found. Please ensure ELM327 is on and connected. Looping with 5 seconds pause')
        connection = obd.Async()
        time.sleep(5)
    syslog.syslog('Connected to '+connection.get_port_name()+'successfully')
    #supported = connection.supported_commands
    #print supported
    connection.watch(obd.commands.RPM)
    connection.start()
    connection.stop()

    # Once connected, check if engine is running
    checkEngineOn = connection.query(obd.commands.RPM)
    while checkEngineOn.value is None:
        syslog.syslog('Engine is not started. Looping until the vehicle is turned on.')
        time.sleep(5)
    print "Engine is started.. doing my thing!"
    try:
        loopMetrics(connection)
    except:
        print "Caught It"
kickOff()
