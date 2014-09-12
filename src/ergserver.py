#!/usr/bin/env python

# Simple console application that works with pyrow to send data retrieved from
# a connected Concept 2 rowing erg to a client via websockets.

# ==============================================================================
# IMPORTS
# ==============================================================================

# core
import pyrow.pyrow as pyrow # handles connection to ergs
import time     # for sleep
import json     # for converting data into json strings
import sys      # sys.exit

# server
import signal
from optparse import OptionParser
from SimpleWebSocketServer.SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from multiprocessing import Process, Queue

# ==============================================================================
# CLIENT CONNECTION CLASS
# ==============================================================================

class ErgSocket(WebSocket):

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
# CORE FUNCTIONS
# ==============================================================================

# take an object, create a formatted message and queue it
def queue_message(message_queue, msg_content, msg_type="TXT", log=True):
    message = { 'type': msg_type, 'content': msg_content, 'time': time.clock() }
    message_json = json.dumps(message)

    message_queue.put(message_json)

    if log == True:
        if msg_type == "TXT":
            print("[SEND] {}".format(str(msg_content)))
        else:
            print("[SEND] {} ({} bytes)".format(msg_type, len(message_json)))

# monitor a connected erg and send messages to clients connected to the server
def monitor_erg(message_queue, erg):
    try:
        sleep_time_ms = 5
        sleep_time = float(sleep_time_ms) / 1000.0

        erg_info = pyrow.pyrow.getErg(erg)
        erg_status = pyrow.pyrow.getStatus(erg)
        erg_id = erg_info['serial']

        message = "Concept 2 erg connected (model {}, serial: {})".format(erg_info['model'], erg_id)
        queue_message(message_queue, message);

        # wait for workout to begin, then send stroke data
        queue_message(message_queue, "Waiting for workout to begin...")

        # keep monitoring indefinitely
        while True:
            workout = erg.getWorkout()
            while workout['state'] == 0:
                time.sleep(sleep_time)
                workout = erg.getWorkout()

            # send workout start message
            monitor = erg.getMonitor()
            queue_message(message_queue, { 'erg_id' : erg_id, 'monitor' : monitor, 'workout' : workout }, msg_type="WORKOUT_START")

            # record workout
            stroke_id = 0
            forceplot = erg.getForcePlot()
            while workout['state'] == 1:
                # record force data during the drive
                force = forceplot['forceplot']  # start of pull (when strokestate first changed to 2)
                monitor = erg.getMonitor()

                # stroke start message
                queue_message(message_queue, { 'erg_id': erg_id, 'stroke_id': stroke_id, 'monitor': monitor }, msg_type="STROKE_START", log=False)
                queue_message(message_queue, { 'erg_id': erg_id, 'stroke_id': stroke_id, 'time': monitor['time'], 'force': forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
                
                # loop during drive (and make sure we get the end of the stroke)
                while True:
                    monitor = erg.getMonitor()
                    forceplot = erg.getForcePlot()
                    force.extend(forceplot['forceplot'])
                    queue_message(message_queue, { 'erg_id': erg_id, 'stroke_id': stroke_id, 'time': monitor['time'], 'forceplot': forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
                    if forceplot['strokestate'] != 2:
                        break

                monitor = erg.getMonitor()      # get monitor data for end of stroke
                queue_message(message_queue, { 'erg_id': erg_id, 'stroke_id': stroke_id, 'monitor': monitor, 'forceplot': force }, msg_type="STROKE_END", log=False)

                print("[{}] time: {}, distance: {}, pace: {}".format(stroke_id, monitor['time'], monitor['distance'], monitor['pace']))

                # wait for next stroke
                while forceplot['strokestate'] != 2 and workout['state'] == 1:
                    forceplot = erg.getForcePlot()
                    workout = erg.getWorkout()

                stroke_id += 1

            workout = erg.getWorkout()
            monitor = erg.getMonitor()
            queue_message(message_queue, { 'erg_id': erg_id, 'monitor': monitor, 'workout': workout }, msg_type="WORKOUT_END")

    except Exception as e:
        print(e)
        sys.exit(0)

def main():
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
    else:
        print("{} erg(s) found. Starting ErgServer.".format(len(connected_ergs)))
        print("(NOTE: This will run forever. Press ctrl+c to quit)")

        try:
            message_queue = Queue(20)

            # connect to erg and monitor it using a new process
            erg = pyrow.pyrow(connected_ergs[0])
            prc_monitor = Process(target=monitor_erg, args=(message_queue, erg))
            prc_monitor.start()

            # start the websocket server to accept client connections
            erg_server = SimpleWebSocketServer(options.host, options.port, ErgSocket, message_queue)

            def close_sig_handler(signal, frame):
                erg_server.close()
                sys.exit(0)

            signal.signal(signal.SIGINT, close_sig_handler)
            erg_server.serveforever()

        except:
            pass

    print("Closing ErgServer. See you next time!")
    try:
        prc_monitor.terminate()
    except:
        pass
    sys.exit(0)

if __name__ == "__main__":
    main()
