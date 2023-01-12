#!/usr/bin/env python

from ScoringResponse import ScoringResponse
from ScoringResponse import Payload
import websockets
import argparse
import json
import asyncio
import threading
import time
import simpleobsws

# Get the arguments from the command line.
parser = argparse.ArgumentParser(prog="pyswitcher.py", description="""Tool for automatically switching the livestreaming scene based on input from the scoring software. \n
                                                                   Scenes must be named \"Field 1\" and \"Field 2\" for this program to work correctly.""")
parser.add_argument("-scoring", "--scoring", metavar="scoringaddr", type=str, required=True,  action="store", help="Address of the scoring software on the network.")
parser.add_argument("-code", "--code",       metavar="eventcode",   type=str, required=True,  action="store", help="Event code from the scoring software.")
parser.add_argument("-obs", "--obs",         metavar="obsaddr",     type=str, required=True,  action="store", help="Address of the OBS websocket on the network.")
parser.add_argument("-port", "--port",       metavar="obsport",     type=int, required=False, action="store", help="Port the OBS websocket is running on.", default=4444)
parser.add_argument("-pw", "--pw",           metavar="obspw",       type=str, required=False, action="store", help="Password for the OBS websocket.")

# Parse the arguments from the command line.
args = parser.parse_args()

# Main loop.
async def run():

    # Connect to the scoring socket.
    scoringuri = "ws://" + args.scoring + "/api/v2/stream/?code=" + args.code
    print("Connecting to the scoring software at %s" % scoringuri)
    async with websockets.connect(scoringuri) as scoring:
        print("Connected to the scoring software")

        # Create the OBS socket.
        if(args.pw):
            obs = simpleobsws.obsws(host=args.obs, port=args.port,password=args.pw, loop=asyncio.get_event_loop())
        else:
            obs = simpleobsws.obsws(host=args.obs, port=args.port, loop=asyncio.get_event_loop())

        # Connect to the OBS socket.
        try:
            await obs.connect()
        except:
            print("Could not connect to OBS. Make sure you have the OBS websocket plugin installed and try again.")
            raise SystemExit(0)

        print("Connected to OBS.")

        while True:
            # Infinite loop waiting for WebSocket data, then modifies the OBS recording appropriately.
            print("\nWaiting for next message...")
            message = await scoring.recv()

            # Update from the scoring socket received
            print("Message received: " + message)

            # Convert the string into a ScoringResponse object
            d = json.loads(message)
            d["payload"] = Payload(**d['payload'])
            response = ScoringResponse(**d)

            # Wait untul the next socket message depending on what the payload's message is.

            # Match load (not the official start of match, or match preview)
            # Intended for the live audience
            if(response.updateType == "MATCH_LOAD"):
                print("Loading next match detected, skipping...")

                # # Set filename.
                # filename = "%YY-%MM-%DD " + args.code + " " + response.payload.shortName
                # print("  - Setting filename to " + filename)
                # data = {"filename-formatting": filename}
                # result = await obs.call("SetFilenameFormatting", data)
                # print("  - Result: " + str(result))

                # # Set the appropriate scene in OBS.
                # field = "Field " + str(response.payload.field)
                # print("  - Setting scene to " + field)
                # data = {"scene-name": field}
                # result = await obs.call("SetCurrentScene", data)
                # print("  - Result: " + str(result))

            # Match start (timer has begun)
            if(response.updateType == "MATCH_START"):
                # If the active match is not a test match, proceed.
                if(response.payload.shortName[0] != 'T'):
                    print("Start of official match detected")

                    # Set filename.
                    filename = "%YY-%MM-%DD " + args.code + " " + response.payload.shortName
                    print("  - Setting filename to " + filename)
                    data = {"filename-formatting": filename}
                    result = await obs.call("SetFilenameFormatting", data)
                    print("  - Result: " + str(result))

                    # Set the appropriate scene in OBS.
                    field = "Field " + str(response.payload.field)
                    print("  - Setting scene to " + field)
                    data = {"scene-name": field}
                    result = await obs.call("SetCurrentScene", data)
                    print("  - Result: " + str(result))

                    # Start recording.
                    print("  - Starting the recording (if not already started)")
                    result = await obs.call("StartRecording")
                    print("  - Result: " + str(result))
                else:
                    print("Test match detected; ignoring")
                

            # Match post or abort (match is over, grab the next couple of seconds.)
            if(response.updateType == "MATCH_POST" or response.updateType == "MATCH_ABORT"):
                print("End of official match detected")
                time.sleep(5)
                print("  - Stopping the recording")
                result = await obs.call("StopRecording")
                print("  - Result: " + str(result))

asyncio.run(run())