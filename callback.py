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
            networkStatus = "    Up"
        except:  # Woops, we have no network connection. 
            syslog.syslog('Unable to ping auto-mated.com as the network appears to be down. Trying again')
            networkStatus = "  Down"
        time.sleep(10)


# Kick off callback thread
callbackThread = Thread(target=callBack)
callbackThread.setDaemon(True)
callbackThread.start()
