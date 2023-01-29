#!/usr/bin/env python3

import argparse
import json
import random
import re
import string
import time

from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--broker", required=True, type=str, help='BINANCE')
parser.add_argument("-t", "--ticke", required=True, type=str, help='BTCUSDT')
args = parser.parse_args()

GREEN = "#008000"
RED = "#FF0000"
WHITE = "#FFFFFF"
broker = args.broker.upper()
ticke = args.ticke.upper()
tickerSymbol = f'{broker}:{ticke}'

# "BINANCE:BTCUSDTPERP":0
priceOld = {
    # args.broker+":"+args.ticke : 0
    tickerSymbol:0
}

priceCurrent = {
    # args.broker+":"+args.ticke : 0
    tickerSymbol:0
}

def generateSession():
    stringLength = 12
    letters = string.ascii_lowercase
    random_string = "".join(random.choice(letters) for i in range(stringLength))
    return "qs_" + random_string

def prependHeader(st):
    return "~m~" + str(len(st)) + "~m~" + st

def constructMessage(func, paramList):
    return json.dumps({"m": func, "p": paramList}, separators=(",", ":"))

def createMessage(func, paramList):
    return prependHeader(constructMessage(func, paramList))

def sendMessage(ws, func, args):
    ws.send(createMessage(func, args))

def sendPingPacket(ws, result):
    pingStr = re.findall(".......(.*)", result)
    if len(pingStr) != 0:
        pingStr = pingStr[0]
        ws.send("~m~" + str(len(pingStr)) + "~m~" + pingStr)

def view(color, price):
    print("%{F"+color+"}"+price+"%{F-}")

def socketJob(ws):
    while True:
        try:
            result = ws.recv()
            if "session_id" in result:
                continue
            if "quote_completed" in result:
                # print("a")
                Res = re.findall("^.*?({.*)$", result)
                Res = Res[0].split("~m~69~m~")
                if len(Res) != 0:
                    jsonRes = json.loads(Res[0])

                if jsonRes["m"] == "qsd":
                    symbol = jsonRes["p"][1]["n"]
                    price = jsonRes["p"][1]["v"]["lp"]
                    # priceCurrent[symbol] = price
                    priceCurrent[symbol] = "{:.2f}".format(price)
                    view(WHITE,priceCurrent[symbol])
                    continue
            else:
                Res = re.findall("^.*?({.*)$", result)
                if len(Res) != 0:
                    jsonRes = json.loads(Res[0])

                    if jsonRes["m"] == "qsd":
                        symbol = jsonRes["p"][1]["n"]
                        price = jsonRes["p"][1]["v"]["lp"]
                        priceOld[symbol] = priceCurrent[symbol]
                        priceCurrent[symbol] = price
                else:
                    # ping packet
                    sendPingPacket(ws, result)

                priceCurrentTemp = "{:.2f}".format(priceCurrent[tickerSymbol])
                priceOldTemp = "{:.2f}".format(priceOld[tickerSymbol])
                if priceCurrentTemp > priceOldTemp:
                    view(GREEN,priceCurrentTemp)
                elif priceCurrentTemp < priceOldTemp:
                    view(RED,priceCurrentTemp)
                else:
                    view(WHITE,priceCurrentTemp)
                priceOld[tickerSymbol] = priceCurrent[tickerSymbol]
        except KeyboardInterrupt:
            ws.close()
            print("\nGoodbye!")
            exit(0)
        except WebSocketConnectionClosedException as a:
            break
        except Exception as e:
            continue

def main():
    while True:
        try:
            # create tunnel
            tradingViewSocket = "wss://data.tradingview.com/socket.io/websocket"
            headers = json.dumps({"Origin": "https://data.tradingview.com"})
            ws = create_connection(tradingViewSocket, headers=headers)
            session = generateSession()

            # Send messages
            sendMessage(ws, "quote_create_session", [session])
            sendMessage(ws, "quote_set_fields", [session, "lp"])

            # I trade in a specific broker and in futures, so I will add the ticket symbol manually.
            sendMessage(ws, "quote_add_symbols", [session, tickerSymbol])

            # Start job
            socketJob(ws)
        except Exception as e:
            # print(e)
            time.sleep(10)
            continue

if __name__ == "__main__":
    main()