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
			echo "Nothing found.. sleeping and trying again"
			sleep 1
		else
			echo "Found OBDLink Device with Mac: "$findDevice" adding it to rfcomm.conf"
			yes 'yes' | bt-device --connect=$findDevice
			rfcomm connect /dev/rfcomm0 $findDevice 1 &
		fi
		connectDevices=$(bt-device -l | grep -c OBDLink)
	done
else
	echo "OBDLink device is already added... Checking if we're connected..."
	deviceMac=$(bt-device -l | grep OBDLink | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')
	if [ "$deviceMac" != "" ]; then
		rfcommConfirm=$(rfcomm -a | grep -c $deviceMac)
	else
		rfcommConfirm=0
	fi
	# Checking to see if we connected... if not, then we keep trying because we might be out of range
	if [ "$rfcommConfirm" != 1 ]; then
		echo "Not connected... trying to connect"
		while [ "$rfcommConfirm" != 1 ]; do
			rfcomm connect /dev/rfcomm0 $deviceMac 1 &
			sleep 5
			rfcommConfirm=$(rfcomm -a | grep -c $deviceMac)
			if [ "$rfcommConfirm" != 1 ]; then
				echo "Failed to connnect to device.. Going to sleep and try again"
				sleep 30
			else
				echo "Successfully connected $deviceMac to /dev/rfcomm0"
			fi
		done
	else
		echo "Device already connected on /dev/rfcomm0"
	fi
fi
