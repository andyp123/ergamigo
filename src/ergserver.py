#!/usr/bin/env python

# Simple console application that works with pyrow to send data retrieved from
# a connected Concept 2 rowing erg to a client via websockets.

# ==============================================================================
# IMPORTS
# ==============================================================================

# core
import pyrow    # handles connection to ergs
import usb.core # for USBError
import time     # for sleep
import datetime # for getting date and time (write to logs)
import json     # for converting data into json strings
# server
import signal, sys, ssl, logging
from optparse import OptionParser
from SimpleWebSocketServer.SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from multiprocessing import Process

# ==============================================================================
# CLIENT CONNECTION CLASS
# ==============================================================================

class ErgSocket(WebSocket):

    erg_server = None

    # receive message from client
    def handleMessage(self):
        if self.data is None:
            self.data = ''

        print("{}: got message: {}".format(self.address, self.data))

    # client connected
    def handleConnected(self):
        print("{}: connected".format(self.address))

    # client disconnected
    def handleClose(self):
        print("{}: closed".format(self.address))


# ==============================================================================
# ERG MONITORING PROCESS FUNCTIONS
# ==============================================================================

# send JSON message to all connected clients
def sendJSON(server, msg_content, msg_type="TXT", log=True):
    message = { 'type': msg_type, 'content':  msg_content }
    message_json = json.dumps(message)

    if log == True:
        if msg_type == "TXT":
            print("[SEND] {}".format(str(msg_content)))
        else:
            print("[SEND] {} ({} bytes)".format(msg_type, len(message_json)))

    clients = server.connections.values()
    # print("Sending to {} clients.".format(len(clients)))
    for client in clients:
        try:
            client.sendMessage(message_json)
        except:
            print("[ERROR] Send failed to client: {}\n----------\n{}\n----------\nClosing connection.".format(client.address, message_json))
            client.sendClose()

# monitor a connected erg and send messages to clients connected to the server
def monitor_erg(erg, server):
    try:
        server = ErgSocket.erg_server

        sleep_time_ms = 3
        sleep_time = 1.0 / float(sleep_time_ms)

        erg_info = pyrow.pyrow.getErg(erg)
        erg_status = pyrow.pyrow.getStatus(erg)
        erg_id = erg_info['serial']

        message = "Concept 2 erg connected (model {}, serial: {})".format(erg_info['model'], erg_id)
        # print(message)
        sendJSON(server, message);

        # wait for workout to begin, then send stroke data
        sendJSON(server, "Waiting for workout to begin...")

        # keep monitoring indefinitely
        while True:
            workout = erg.getWorkout()
            while workout['state'] == 0:
                time.sleep(sleep_time)
                workout = erg.getWorkout()

            # send workout start message
            monitor = erg.getMonitor()
            sendJSON(server, { 'erg_id' : erg_id, 'monitor' : monitor, 'workout' : workout }, msg_type="WORKOUT_START")

            # record workout
            stroke_id = 0
            forceplot = erg.getForcePlot()
            while workout['state'] == 1:
                # record force data during the drive
                force = forceplot['forceplot']  # start of pull (when strokestate first changed to 2)
                monitor = erg.getMonitor()

                # stroke start message
                sendJSON(server, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'monitor': monitor }, msg_type="STROKE_START", log=False)
                sendJSON(server, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'force' : forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
                
                # loop during drive (and make sure we get the end of the stroke)
                while True:
                    monitor = erg.getMonitor()
                    forceplot = erg.getForcePlot()
                    force.extend(forceplot['forceplot'])
                    sendJSON(server, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'time' : monitor['time'], 'forceplot' : forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
                    if forceplot['strokestate'] != 2:
                        break

                monitor = erg.getMonitor()      # get monitor data for end of stroke
                sendJSON(server, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'monitor' : monitor, 'forceplot' : force }, msg_type="STROKE_END", log=False)

                print("[{}] time: {}, distance: {}, pace: {}".format(stroke_id, monitor['time'], monitor['distance'], monitor['pace']))

                # wait for next stroke
                while forceplot['strokestate'] != 2 and workout['state'] == 1:
                    forceplot = erg.getForcePlot()
                    workout = erg.getWorkout()

                stroke_id += 1

            workout = erg.getWorkout()
            monitor = erg.getMonitor()
            sendJSON(server, { 'erg_id' : erg_id, 'monitor' : monitor, 'workout' : workout }, msg_type="WORKOUT_END")

    except Exception as n:
        print(n)
        sys.exit(0)


# ==============================================================================
# SYSTEM INITIALIZATION AND ERG CONNECTION
# ==============================================================================

erg_server = None

if __name__ == "__main__":
    # handle command line options
    parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
    parser.add_option("--host", default='', type='string', action="store", dest="host", help="hostname (localhost)")
    parser.add_option("--port", default=8000, type='int', action="store", dest="port", help="port (8000)")
    (options, args) = parser.parse_args()

    print("Welcome to ErgServer!")

    # initialize connection to erg
    connected_ergs = pyrow.find()
    if len(connected_ergs) == 0:
        print("No ergs found.")
        sys.exit(0);
    else:
        # start the websocket server to accept client connections
        ErgSocket.erg_server = SimpleWebSocketServer(options.host, options.port, ErgSocket)

        # connect to erg and monitor it using a new process
        print("{} erg(s) found. Starting monitoring process.".format(len(connected_ergs)))
        erg = pyrow.pyrow(connected_ergs[0])
        erg_process = Process(target=monitor_erg, args=(erg,ErgSocket.erg_server,))
        erg_process.start()

        # set up the quit callback and start the server
        def close_sig_handler(signal, frame):
            print("Exiting system.")
            if erg_process != None:
                erg_process.terminate()
            ErgSocket.erg_server.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, close_sig_handler)
        ErgSocket.erg_server.serveforever()
