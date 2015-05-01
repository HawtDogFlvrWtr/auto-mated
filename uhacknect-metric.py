#!/usr/bin/python
# 
# OBD2 Loop routine for metrics
# Created by Christopher Phipps (hawtdogflvrwtr@gmail.com)
# 5/1/2015
#

import obd
import time
import urllib2

#obd.debug.console = True

def loopMetrics(connection):
    metricsArray = ["RPM","SPEED","TIMING_ADVANCE","INTAKE_TEMP","THROTTLE_POS","MAF","RUN_TIME","FUEL_LEVEL"]
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
            tempValues.append(value.value)
        mainHost = "http://www.uhacknect.com/api/influxPush.php?vin=3C4PDCGG4FT641185&api=6054-4220-2524-3963&metric="
        valuesList = ','.join([str(x) for x in tempValues])
        # Check if we've been disconnected
        if all(x is None for x in valuesList):
            connection.unwatch_all()
            kickOff()
        print "metrics List: "+metricsList
        print "values List: "+valuesList
        # Attempt to push, loop over if no network connection
        try:
            output = urllib2.urlopen(mainHost+metricsList+"&values="+valuesList).read()
        except:
            loopMetrics(connection)
        print output
    time.sleep(5)


def kickOff():
    # Auto connect to obd device
    connection = obd.Async()
    # Check if connected and continue, else loop
    while not connection.is_connected():
        print "No valid device found. Please ensure ELM327 is on and connected. Looping with 5 seconds pause"
        connection = obd.Async('/dev/pts/14')
        time.sleep(5)
    print "Connected to "+connection.get_port_name()+" successfully"
    #supported = connection.supported_commands
    #print supported
    connection.watch(obd.commands.RPM)
    connection.start()
    connection.stop()

    # Once connected, check if engine is running
    checkEngineOn = connection.query(obd.commands.RPM)
    while checkEngineOn.value is None:
        print "Engine is not started. Looping until the vehicle is turned on."
        time.sleep(5)
    print "Engine is started.. doing my thing!"
    try:
        loopMetrics(connection)
    except:
        print "Caught It"
kickOff()
