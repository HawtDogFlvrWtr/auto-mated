#!/bin/bash
#
#
# Find OBDLink Device on startup, add and connect
# Created by Christopher Phipps HawtDogFlvrWtr@gmail.com
# Apr 28th 2014
#
#

connectDevices=$(bt-device -l | grep -c OBDLink)
if [ $connectDevices != 1 ]; then
	echo "No OBDLink device connected... trying to find it and add it..."
	while [ $connectDevices != 1 ]; do
		findDevice=$(hcitool scan | grep OBDLink | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')
		if [ "$findDevice" == "" ]; then
			echo "Nothing found.. sleeping 10 seconds and trying again"
			sleep 1
		else
			echo "Found OBDLink Device with Mac: "$findDevice
			yes 'yes' | bt-device --connect=$findDevice
		fi
		connectDevices=$(bt-device -l | grep -c OBDLink)		
	done
else
	echo "OBDLink device is already connected... connecting"
	
fi
