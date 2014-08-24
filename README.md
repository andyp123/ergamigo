ergamigo
========

Utility for logging and analysing data from Concept 2 rowers using linux and python.

Requirements:
Python 3.4 or greater (for websockets library)
Python library 'websockets'
Python library 'asyncio' (required by websockets)
Python library 'pyusb'
Python library 'pyrow' (included)

Installation:
1. make sure libusb is installed. It is installed by default in many linux distros, but you need to install on osx and windows
2. install pyusb 1.0+
3. now you can run using 'python ergamigo.py'

NOTE:
You may not be able to read from the USB due to insufficient permissions. To fix this you can either:
1. run as root 'sudo python ergamigo.py'
2. set up permission to read from the concept 2 erg using udev rules.
Create a file in /etc/udev/rules.d/ named '50-erg.rules' containing the following:
SUBSYSTEM=="usb", ATTR{idProduct}=="000?", ATTR{idVendor}=="17a4", MODE="0660", GROUP="wheel"

To list connected usb devices and check the vendor and product codes, type 'lsusb' at the terminal.
'lsusb -v' prints verbose information.
To reload the udev rules, enter 'udevadm control --reload-rules' at the terminal.
