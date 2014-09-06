#!/usr/bin/env python

# Simple console application that works with pyrow to send data retrieved from
# a connected Concept 2 rowing erg to a client via websockets.

# core
import pyrow # handles connection to ergs
import usb.core # for USBError
import time     # for sleep
import datetime # for getting date and time (write to logs)
import json     # for converting data into json strings
# server
import signal, sys, ssl, logging
from optparse import OptionParser
from SimpleWebSocketServer.SimpleWebSocketServer import SimpleWebSocketServer, WebSocket
from multiprocessing import Process

class ErgServer(WebSocket):

    process_map = {}

    def handleConnected(self):
        print("{}: connected".format(self.address))

        try:
            connected_ergs = pyrow.find()
            if len(connected_ergs) == 0:
                self.sendJSON("No ergs found.")
                self.sendClose()
            else:
                erg = pyrow.pyrow(connected_ergs[0])
                p = Process(target=self.doWorkout, args=(erg,))
                p.start()
                ErgServer.process_map[self.address] = p;

        except Exception as n:
            print(n)

    def handleClose(self):
        print("{}: closed".format(self.address))
        p = ErgServer.process_map[self.address]
        if p != None:
            p.terminate();

    def sendJSON(self, msg_content, msg_type="TXT", log=True):
        message = { 'type': msg_type, 'content':  msg_content }
        message_json = json.dumps(message)

        try:
            if log == True:
                if msg_type == "TXT":
                    print("[SEND] {}".format(str(msg_content)))
                else:
                    print("[SEND] {} ({} bytes)".format(msg_type, len(message_json)))
            self.sendMessage(message_json)
        except:
            print("[ERROR] SEND FAILED:\n----------\n{}\n----------\nClosing connection.".format(message_json))

    def doWorkout(self, erg):
        try:
            sleep_time = 1.0 / 2000.0 # 2ms sleep

            erg_info = pyrow.pyrow.getErg(erg)
            erg_status = pyrow.pyrow.getStatus(erg)
            erg_id = erg_info['serial']

            message = "Concept 2 erg connected (model {}, serial: {})".format(erg_info['model'], erg_id)
            self.sendJSON(message);

            # wait for workout to begin, then send stroke data
            self.sendJSON("{}: Waiting for workout to begin...".format(self.address))

            workout = erg.getWorkout()
            while workout['state'] == 0:
                time.sleep(sleep_time)
                workout = erg.getWorkout()

            # send workout start message
            monitor = erg.getMonitor()
            self.sendJSON({ 'erg_id' : erg_id, 'monitor' : monitor, 'workout' : workout }, msg_type="WORKOUT_START")

            # record workout
            stroke_id = 0
            forceplot = erg.getForcePlot()
            while workout['state'] == 1:
                # record force data during the drive
                force = forceplot['forceplot']  # start of pull (when strokestate first changed to 2)
                monitor = erg.getMonitor()

                # stroke start message
                self.sendJSON({ 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'monitor': monitor }, msg_type="STROKE_START", log=False)
                self.sendJSON({ 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'force' : forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
                
                # loop during drive (and make sure we get the end of the stroke)
                while True:
                    monitor = erg.getMonitor()
                    forceplot = erg.getForcePlot()
                    force.extend(forceplot['forceplot'])
                    self.sendJSON({ 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'time' : monitor['time'], 'forceplot' : forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
                    if forceplot['strokestate'] != 2:
                        break

                monitor = erg.getMonitor()      # get monitor data for end of stroke
                self.sendJSON({ 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'monitor' : monitor, 'forceplot' : force }, msg_type="STROKE_END", log=False)

                print("[{}] time: {}, distance: {}, pace: {}".format(stroke_id, monitor['time'], monitor['distance'], monitor['pace']))

                # wait for next stroke
                while forceplot['strokestate'] != 2 and workout['state'] == 1:
                    forceplot = erg.getForcePlot()
                    workout = erg.getWorkout()

                stroke_id += 1

            workout = erg.getWorkout()
            monitor = erg.getMonitor()
            self.sendJSON({ 'erg_id' : erg_id, 'monitor' : monitor, 'workout' : workout }, msg_type="WORKOUT_END")
            self.sendClose()

        except Exception as n:
            print(n)
            self.sendClose()

if __name__ == "__main__":
    parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
    parser.add_option("--host", default='', type='string', action="store", dest="host", help="hostname (localhost)")
    parser.add_option("--port", default=8000, type='int', action="store", dest="port", help="port (8000)")

    (options, args) = parser.parse_args()

    cls = ErgServer
    server = SimpleWebSocketServer(options.host, options.port, cls)

    def close_sig_handler(signal, frame):
        server.close()
        sys.exit()

    signal.signal(signal.SIGINT, close_sig_handler)

    server.serveforever()

# =============================================================================
# ONLINE FUNCTIONS
# =============================================================================
# @asyncio.coroutine
# def send_message(websocket, msg_content, msg_type="TXT", log=True):
#     """package a message and send it to a websocket client"""
#     message = { "type": msg_type, "content": msg_content }
#     message_json = json.dumps(message)

#     if log is True:
#         print("[SEND ({} bytes)] {}".format(len(message_json), message_json), end="")
#     yield from websocket.send(message_json)
#     if log is True:
#         print(" [OK]")

# # server version
# @asyncio.coroutine
# def server(websocket, path):
#     print("Client connected")      

#     yield from send_message(websocket, "Welcome to ErgAmigo Server!", log=False)

#     sleep_time = 1.0 / 1000.0 # 1 ms
#     connected_ergs = pyrow.find()
#     if len(connected_ergs) == 0:
#         message = "No ergs found."
#         yield from send_message(websocket, message)
#     else:
#         try:
#             erg = pyrow.pyrow(connected_ergs[0])
#             erg_info = pyrow.pyrow.getErg(erg)
#             erg_status = pyrow.pyrow.getStatus(erg)
#             erg_id = erg_info['serial']

#             message = "Concept 2 erg connected (model {}, serial: {})".format(erg_info['model'], erg_id)
#             yield from send_message(websocket, message)

#             # wait for workout to begin, then send stroke data
#             yield from send_message(websocket, "Waiting for workout to begin...")

#             workout = erg.getWorkout()
#             while workout['state'] == 0:
#                 time.sleep(sleep_time)
#                 workout = erg.getWorkout()

#             monitor = erg.getMonitor()
#             yield from send_message(websocket, { 'erg_id' : erg_id, 'monitor' : monitor, 'workout' : workout }, msg_type="WORKOUT_START")

#             # record workout
#             stroke_id = 0
#             forceplot = erg.getForcePlot()
#             while workout['state'] == 1:
#                 # record force data during the drive
#                 force = forceplot['forceplot']  # start of pull (when strokestate first changed to 2)
#                 monitor = erg.getMonitor()

#                 # stroke start message
#                 yield from send_message(websocket, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'monitor': monitor }, msg_type="STROKE_START", log=False)
#                 yield from send_message(websocket, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'force' : forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
                
#                 # loop during drive (and make sure we get the end of the stroke)
#                 while True:
#                     monitor = erg.getMonitor()
#                     forceplot = erg.getForcePlot()
#                     force.extend(forceplot['forceplot'])
#                     yield from send_message(websocket, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'time' : monitor['time'], 'forceplot' : forceplot['forceplot'] }, msg_type="STROKE_FORCE", log=False)
#                     if forceplot['strokestate'] != 2:
#                         break

#                 monitor = erg.getMonitor()      # get monitor data for end of stroke
#                 yield from send_message(websocket, { 'erg_id' : erg_id, 'stroke_id' : stroke_id, 'monitor' : monitor, 'forceplot' : force }, msg_type="STROKE_END", log=False)

#                 print("[{}] time: {}, distance: {}, pace: {}".format(stroke_id, monitor['time'], monitor['distance'], monitor['pace']))

#                 # wait for next stroke
#                 while forceplot['strokestate'] != 2 and workout['state'] == 1:
#                     forceplot = erg.getForcePlot()
#                     workout = erg.getWorkout()

#                 stroke_id += 1

#             workout = erg.getWorkout()
#             monitor = erg.getMonitor()
#             yield from send_message(websocket, { 'erg_id' : erg_id, 'monitor' : monitor, 'workout' : workout }, msg_type="WORKOUT_END")

#         except usb.core.USBError as e:
#             yield from send_message(websocket, "Error reading data from erg. Closing connection.")
#             websocket.close()
#             exit(e)

#     yield from send_message(websocket, "ErgAmigo Server closing. See you next time!", log=False)
#     websocket.close()
#     print("Client disconnected")
