#!/usr/bin/python
#
# Influxdb push functions and thread
#
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
            influxStatus = "    Up"
            metricsSuccess += 1
            influxQueue.task_done()  # If success, skim that off the top of the queue
        except:  # If we have no network connection. FIX: NEED TO HAVE THIS WRITE TO A FILE AND UPLOAD WHEN AVAILABLE
            influxQueue.put(influxQueueGet)
            influxQueue.task_done()  # Have to mark it as done anyway, but we roll it back into the Queue. 
            syslog.syslog('Network connection down, Tossing record back into queue until network is back')
            influxStatus = "  Down"
        time.sleep(1)
    influxQueue.join()

# Kick off influx threads
influxThread = Thread(target=pushInflux, args=(influxQueue,))
influxThread.setDaemon(True)
influxThread.start()
