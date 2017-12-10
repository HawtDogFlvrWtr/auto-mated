#!/bin/bash

cat <<EOT >> /etc/motd
   _____          __                      _____          __             .___
  /  _  \  __ ___/  |_  ____             /     \ _____ _/  |_  ____   __| _/
 /  /_\  \|  |  \   __\/  _ \   ______  /  \ /  \\\__  \\\   __\/ __ \ / __ | 
/    |    \  |  /|  | (  <_> ) /_____/ /    Y    \/ __ \|  | \  ___// /_/ | 
\____|__  /____/ |__|  \____/          \____|__  (____  /__|  \___  >____ | 
        \/                                     \/     \/          \/     \/ 
EOT

sed -i -e '$i \/opt/auto-mated/automated-metric.py &\n' /etc/rc.local
sudo apt-get install git-core -y
sudo apt-get update -y
sudo apt-get upgrade -y
apt-get install --no-install-recommends htop python-dev python-pip -y
cd /opt
pip install setuptools obd psutil netifaces
