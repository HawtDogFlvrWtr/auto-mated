#!/bin/bash
#
#
# Find OBDLink Device on startup, add and connect
# Created by Christopher Phipps HawtDogFlvrWtr@gmail.com
# Apr 28th 2014
#

process=$(/bin/ps -ef | /bin/grep -c bluetooth_simple.sh)
if [[ $process -gt 4 ]]; then
        logger Instance already running.. exiting... $process running
	exit 0
fi
pairedDevices=$(/usr/bin/bt-device --list | grep -c OBDLink)
if [ $pairedDevices == 1 ]; then

	# Get Mac address
	deviceMac=$(/usr/bin/bt-device --list | grep OBDLink | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')

	# Checking to see if we connected... if not, then we keep trying because we might be out of range
	rfcommConfirm=$(rfcomm -a | grep -c $deviceMac)

	if [ "$rfcommConfirm" != 1 ]; then
		logger Not connected... trying to connect
		while [ "$rfcommConfirm" != 1 ]; do
			rfcomm connect /dev/rfcomm0 $deviceMac 1 &
			sleep 5
			rfcommConfirm=$(rfcomm -a | grep -c $deviceMac)
			if [ "$rfcommConfirm" != 1 ]; then
				logger Failed to connnect to device.. Going to sleep and try again
				sleep 5 
			else
				logger Successfully connected $deviceMac to /dev/rfcomm0
			fi
		done
	else
		logger Device already connected on /dev/rfcomm0
	fi
fi
