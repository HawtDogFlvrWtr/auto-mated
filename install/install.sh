#!/bin/bash

cat <<EOT >> /etc/motd
   _____          __                      _____          __             .___
  /  _  \  __ ___/  |_  ____             /     \ _____ _/  |_  ____   __| _/
 /  /_\  \|  |  \   __\/  _ \   ______  /  \ /  \\\__  \\\   __\/ __ \ / __ | 
/    |    \  |  /|  | (  <_> ) /_____/ /    Y    \/ __ \|  | \  ___// /_/ | 
\____|__  /____/ |__|  \____/          \____|__  (____  /__|  \___  >____ | 
        \/                                     \/     \/          \/     \/ 
EOT

sudo apt-get install tightvncserver -y
tightvncserver
service lightdm stop
cat <<EOT >> /etc/init.d/vncboot
#! /bin/sh
# /etc/init.d/vncboot

### BEGIN INIT INFO
# Provides: vncboot
# Required-Start: $remote_fs $syslog
# Required-Stop: $remote_fs $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Start VNC Server at boot time
# Description: Start VNC Server at boot time.
### END INIT INFO

USER=root
HOME=/root

export USER HOME

case "\$1" in
 start)
  echo "Starting VNC Server"
  #Insert your favoured settings for a VNC session
  su - \$USER -c "/usr/bin/vncserver :1 -geometry 800x600 -depth 16"
  ;;

 stop)
  echo "Stopping VNC Server"
  /usr/bin/vncserver -kill :1
  ;;

 *)
  echo "Usage: /etc/init.d/vncboot {start|stop}"
  exit 1
  ;;
esac

exit 0
EOT
chmod 755 /etc/init.d/vncboot
update-rc.d -f lightdm remove
update-rc.d vncboot defaults
sed -i -e '$i \/opt/auto-mated/automated-metric.py &\n' /etc/rc.local
{ crontab -l -u root; echo '* * * * * /opt/auto-mated/bluetooth_search.sh'; } | crontab -u root -
sudo apt-get install git-core -y
sudo apt-get update -y
sudo apt-get upgrade -y
apt-get install --no-install-recommends bluetooth htop python-dev python-pip -y
service bluetooth start
service bluetooth status
hcitool scan
cd /opt
git clone git://git.drogon.net/wiringPi
cd wiringPi
git pull origin
./build
cd /opt/auto-mated/pcd8544/cpu_show/
chmod +x compile.sh
./compile.sh
pip install obd psutil netifaces
