"""
This file is part of SSE Auto Translator
by Cutleast and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import sys

import zmq


def handle():
    context = zmq.Context()
    client = context.socket(zmq.REQ)
    client.connect("tcp://127.0.0.1:1248")

    sys.argv.pop(0)

    client.send_string(sys.argv[0])

    if (client.poll(1000) & zmq.POLLIN) != 0:
        reply = client.recv_string()
        if reply == "SUCCESS":
            print("Request successful")
            sys.exit()
        else:
            print("Unknown reply from server:", reply)
            sys.exit(1)

    print("No response from server")
    sys.exit(1)
