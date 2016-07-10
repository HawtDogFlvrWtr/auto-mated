#!/bin/bash

echo Please enter the WIFI SSID
read ssid
echo Please enter the WIFI Password
read passwd

cat <<EOT >> /etc/wpa_supplicant/wpa_supplicant.conf
network={
    ssid="$ssid"
    psk="$passwd"
}
EOT
sudo ifdown wlan0
sudo ifup wlan0
ifconfig -a | grep wlan0
