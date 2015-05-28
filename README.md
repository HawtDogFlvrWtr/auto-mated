# uHacknect
An alternative to Dodges uconnect access, for us folks with remote start on our vehicle but no unconnect access capabilities in our headunits. We'll be able to remotely start/stop/unlock/lock and hopefully much, more from the web. This was tested on Ubuntu 14.04

# Requirements
*  ObdLink LX (Hardware)
*  Raspberry Pi b+/2
*  python 2+
*  pybluez - https://github.com/karulis/pybluez
*  rfcomm
*  python-dev
*  libbluetooth-dev
*  Wifi adapter for pi
*  Bluetooth adapter (2.1+)

# How-To
1.  Install python, python-dev, libbluetooth-dev
2.  Download and install pybluez (git clone https://github.com/karulis/pybluez, python setup.py install)
3.  Install rfcomm
4.  Attach to obdlink lx via bluetooth interface (or console)
5.  Edit uhacknect.py with the mac address of your obdlink lx device
6.  Run uhacknect.py (python uhacknet.py)

# Workarounds

*  If bluetooth in Ubuntu 14.04 turns off and back on again, run (rfkill block bluetooth) and try again. This is a known bug.
