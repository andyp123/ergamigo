#!/usr/bin/env python

import asyncio
import websockets

@asyncio.coroutine
def hello(websocket, path):
    name = yield from websocket.recv()
    print("< {}".format(name))
    greeting = "Hello {}!".format(name)
    yield from websocket.send(greeting)
    print("> {}".format(greeting))

    count = 0
    while True:
    	if not websocket.open:
    		break
    	yield from websocket.send("{}".format(count))
    	print("SENT: {}".format(count))
    	count += 1
    	
    print("Connection closed")


start_server = websockets.serve(hello, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()