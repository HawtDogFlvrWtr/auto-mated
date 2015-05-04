#!/bin/bash
#
#
# Find OBDLink Device on startup, add and connect
# Created by Christopher Phipps HawtDogFlvrWtr@gmail.com
# Apr 28th 2014
#
#

connectDevices=$(/usr/bin/bluez-test-device list | grep -c OBDLink)
if [ $connectDevices != 1 ]; then
	logger No OBDLink device connected... trying to find it and add it...
	while [ $connectDevices != 1 ]; do
		findDevice=$(hcitool scan | grep OBDLink | grep -o -E '([[:xdigit:]]{1,2}:){5}[[:xdigit:]]{1,2}')
		if [ "$findDevice" == "" ]; then
			logger Nothing found.. sleeping and trying again 
			sleep 1
		else
			logger Found OBDLink Device with Mac: "$findDevice".. Attempting to add and connect with rfcomm
			# Connect to the device without interaction, via bt-device
			yes 'yes' | /usr/bin/bluez-test-device create $findDevice
			connectDevices=$(/usr/bin/bluez-test-device list | grep -c OBDLink)
			# Check if we successfully paired to the device without interaction
			if [ $connectDevices != 0 ]; then
				rfcomm connect /dev/rfcomm0 $findDevice 1 &
				sleep 10
				# Checking if we successfully connected via rfcomm
				rfcommConfirm=$(rfcomm -a | grep -c $deviceMac)
				if [ "$rfcommConfirm" != "" ]; then
					logger Successfully connected via RFCOMM
				else
					logger Failed to connect via RFCOMM. Please restart and try again
				fi
			else
				logger Failed to add the device. Please restart and try again.
			fi
			
		fi
		connectDevices=$(/usr/bin/bluez-test-device list | grep -c OBDLink)
	done
else
	logger OBDLink device is already added... Checking if we\'re connected...
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
				logger Failed to connnect to device.. Going to sleep and try again
				sleep 30
			else
				logger Successfully connected $deviceMac to /dev/rfcomm0
			fi
		done
	else
		logger Device already connected on /dev/rfcomm0
	fi
fi
