ergamigo
========

Utility for logging and analysing data from Concept 2 rowers using linux and python.

Update: This is being converted to a small application that runs a server and sends messages containing information about connected ergs and data being logged by ergs to connected clients. The idea is that I can then use javascript and websockets to create a client and present a more interesting way of looking at the data.

Requirements:
-------------
+ Python 3.4 or greater (for websockets library)
+ Python library 'websockets'
+ Python library 'asyncio' (required by websockets)
+ Python library 'pyusb'
+ Python library 'pyrow' (included)

Installation:
-------------
1. make sure libusb is installed. It is installed by default in many linux distros, but you need to install on osx and windows
2. install pyusb 1.0+
3. now you can run using 'python ergamigo.py'

NOTE:
-----
You may not be able to read from the USB due to insufficient permissions. To fix this you can either:

1. run as root 'sudo python ergamigo.py'
2. set up permission to read from the concept 2 erg using udev rules.<br>
Create a file in /etc/udev/rules.d/ named '50-erg.rules' containing the following:<br>
SUBSYSTEM=="usb", ATTR{idProduct}=="000?", ATTR{idVendor}=="17a4", MODE="0660", GROUP="wheel"

To list connected usb devices and check the vendor and product codes, type 'lsusb' at the terminal.
'lsusb -v' prints verbose information.
To reload the udev rules, enter 'udevadm control --reload-rules' at the terminal.

TODO:
-----
+ create message format for sending data between client and server
  - TYPE : CONTENT , where TYPE is the type of content (e.g. TEXT, STROKE_DATA, FORCE_PLOT etc.)
+ create a function to generate correctly formatted messages on the server
+ create a function to handle messages on the client
+ think about client sending messages to server to request different content etc.
+ do a simple implementation of a power graph in canvas