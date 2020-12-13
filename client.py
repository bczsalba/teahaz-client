# IMPORTS
import os
import sys
import json
import time
import getch
import base64
import requests
import threading



# HELPERS
def encode(a):
    return base64.b64encode(a.encode('utf-8')).decode('utf-8')
def encode_binary(a):
    return base64.b64encode(a).decode('utf-8')
def switch_mode(target):
    global MODE, VALID_KEYS

    MODE = target
    VALID_KEYS = [key for key in BINDS[target].keys()]


# GLOBALS
WIDTH,HEIGHT = os.get_terminal_size()
KEEP_GOING = True
SESSION = requests.Session()

## set by user
URL = "http://localhost:5000/api/v0/"
ROOMID = "conv1"
USERNAME = "pink"
MESSAGE_BREAKLEN = 25

# given by server
COOKIE = "flamingosareblue"

# base data array to append to
BASE_DATA = {
    "username": USERNAME,
    "cookie": COOKIE,
    "chatroom": ROOMID,
}

BINDS = {
    "NORMAL": {
        "i": "insert",
        "ESC": "escape",
        "j": "navigate_down",
        "k": "navigate_up",
        "a": "menu_add",
        "r": "menu_react",
        "m": "menu_message"
    },
    "INSERT": {
        "ESC": "escape"
    },
    "MESSAGE": {
        "s": "message_send",
        "ENTER": "message_newline",
        "c": "message_clear",
    },
}

INPUT = ""
INPUT_CURSOR = 0

# set default mode
switch_mode("INSERT")



# NETWORK FUNCTIONS
## receiving method
def get(parameter,mode="message"):
    data = BASE_DATA
    
    # set endpoint
    endpoint = mode+"/"

    # set parameter based on mode
    if mode == "message":
        data["time"] = str(parameter)
    elif mode == "file":
        data["filename"] = str(parameter)
    else:
        return "Client Error: Invalid get mode '"+str(mode)+"'"

    # return response
    response = SESSION.get(url=URL+endpoint,headers=BASE_DATA)
    return json.loads(response.text)

## sending method
def send(message,mType='text'):
    # base data gets appended to
    data = BASE_DATA
    
    # handle specificities
    if mType == 'text':
        # set text-specific fields
        data["message"] = encode(message)
        data['type'] = "text"

        endpoint = "message/"

    elif mType == 'file':
        # get file contents
        with open(message, 'rb') as infile:
            contents = encode_binary(infile.read())

        # get file extension bc mimetype sucks sometimes
        extension = message.split(".")[-1]

        # set file-specific fields
        data['type'] = "file"
        data['extension'] = extension
        data['data'] = contents

        endpoint = "file/"

    else:
        return "Client Error: Invalid message type '"+str(mType)+"'"

    # return response
    response = SESSION.post(url=URL+endpoint, json=data)
    return response.text



# INPUT 
## key intercepter loop, separate thread
def getch_loop(): 
    global KEEP_GOING

    while KEEP_GOING:
        key = getch.getch()

        # ^C behavior: will likely be properly binded
        if key == "SIGTERM":
            KEEP_GOING = 0
            print('\033[?25h')
            break

        # NORMAL mode: shortcuts
        if MODE == "NORMAL":
            if key in VALID_KEYS:   
                action = BINDS[key]
        
        # INSERT mode: text input
        elif MODE == "INSERT":
            # send key to inputfield to handle
            infield.send(key)

        # print inputfield
        infield.print()



# UI
## test function to get messages
## TODO: the goal of this is to set up a storage of all messages that can be handled line by line
"""
messages = [
    {
        "sender": "me",
        "time": "178929287",
        "contents": [
            "line 1", 
            "line 2",
            "line 3"
        ]
    }
]
# this needs to use the given structure, and expand with the line by line data
"""
def get_lines():
    # TODO: this will probably be way too much and needs to be looked at later
    messages_raw = get(0)
    messages_sorted = sorted(messages_raw,key=lambda x: x["time"])
    messages_encoded = [m for m in messages_sorted if m["message"] != None and m["type"] == "text"]
    messages = []
    for m in messages_encoded:
        m["message"] = base64.b64decode(m["message"]).decode('utf-8')
        messages.append(m)

    for m in messages:
        print(m["message"]+'\n')


# TEMP MAIN

if __name__ == "__main__":
    ##  TODO: add x, y limit
    infield = getch.InputField()

    ## clear screen
    print('\033[2J')

    # input thread
    threading.Thread(target=getch_loop).start()

    # main loop
    while KEEP_GOING:
        get_lines()
        time.sleep(1)
