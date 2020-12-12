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



# GLOBALS
WIDTH,HEIGHT = os.get_terminal_size()
KEEP_GOING = True
SESSION = requests.Session()

## set by user
URL = "http://localhost:5000/api/v0/"
ROOMID = "conv1"
USERNAME = "pink"

# given by server
COOKIE = "flamingosareblue"

## base data array to append to
BASE_DATA = {
    "username": USERNAME,
    "cookie": COOKIE,
    "chatroom": ROOMID,
}

BINDS = {
        "NORMAL": {
            "i": "insert",
            "\x1b": "escape",
            "j": "navigate_down",
            "k": "navigate_up",
            "a": "menu_add",
            "r": "menu_react",
            "m": "menu_message"
        },
        "INSERT" {
            "\x1b": : "escape"
        }
}

VALID_KEYS = [key for key in BINDS.keys()]
MODE = "INSERT"
INPUT = ""



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
    global INPUT,KEEP_GOING

    while KEEP_GOING:
        key = getch.getch()

        # ^C behavior: will likely be properly binded
        if key == "\x03":
            KEEP_GOING = 0
            break

        # NORMAL mode: shortcuts
        if MODE == "NORMAL":
            if key in VALID_KEYS:   
                action = BINDS[key]
        
        # INSERT mode: text input
        elif MODE == "INSERT":

            INPUT += key


        print_input()





# UI
def print_input():
    sys.stdout.write(f'\033[{HEIGHT-1};0H'+INPUT)
    sys.stdout.flush()
    



threading.Thread(target=getch_loop).start()

if __name__ == "__main__":
    print('\033[2J')
    while KEEP_GOING:
        time.sleep(1)
