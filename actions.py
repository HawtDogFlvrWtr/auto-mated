#!/usr/bin/python
#
#  CONTAINS ACTION PULL AND PUSH INFORMATION
#
#
#
 
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
     
                if returnOut.find("OK") != -1:
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


# Kick off actions thread
getActionsThread = Thread(target=getActions)
getActionsThread.setDaemon(True)
getActionsThread.start()
