ErgServer
=========

Utility for getting workout data from a Concept 2 rowing machine and sending it via websockets to connected clients on multiple devices.


Requirements:
-------------

+ Python 2.7.6+
+ Python library 'pyusb'
+ Python library 'pyrow' (included)
+ Python library 'SimpleWebSockets' (included)

pyrow is Copyright (c) 2011, Sam Gambrell. Licensed under the simplified BSD license.<br>
SimpleWebSockets is Copyright (c) 2013, Dave P. Licensed under the MIT license.

Installation:
-------------
1. Get Python 2.7.6 or above and install it. Most Linux distros and MacOS should already have it installed, but Windows does not come with it by default, so head over to http://www.python.org/
2. Make sure libusb is installed. It is installed by default in many linux distros, but you need to install on MacOS and Windows. (http://www.libusb.org/)
3. Install pyusb 1.0+. (http://walac.github.io/pyusb/)
4. From a terminal, move into the directory containing 'ergserver.py' and run it with a Concept 2 erg connected. If you use the erg with the program running, you should see messages at the console.

By default, running ergserver.py with no command line arguments will start a websocket server with your machines ip address on port 8000. This can be changed by running with options:<br>
--host '127.0.0.1' - set the host ip manually
--port 8000 - set the port manually

NOTE:
-----
You may not be able to read from the USB due to insufficient permissions. To fix this you can either:

1. run as root 'sudo python ergserver.py'
2. set up permission to read from the concept 2 erg using udev rules.<br>
Create a file in /etc/udev/rules.d/ named 'c2erg.rules' containing the following:<br>
SUBSYSTEM=="usb", ATTR{idProduct}=="000?", ATTR{idVendor}=="17a4", MODE="0666", GROUP="all"

To list connected usb devices and check the vendor and product codes, type 'lsusb' at the terminal.
'lsusb -v' prints verbose information.
To reload the udev rules, enter 'udevadm control --reload-rules' at the terminal.
