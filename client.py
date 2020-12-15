# IMPORTS
import re
import os
import sys
import json
import time
import getch
import base64
import requests
import threading



# HELPERS
## API
def encode(a):
    return base64.b64encode(a.encode('utf-8')).decode('utf-8')

def encode_binary(a):
    return base64.b64encode(a).decode('utf-8')

def decode(a):
    return base64.b64decode(a).decode('utf-8')

## BINDS
def switch_mode(target):
    global MODE, VALID_KEYS

    MODE = target
    VALID_KEYS = [key for key in BINDS[target].keys()]
    printTo(WIDTH-len(MODE),0,MODE,clear=1)

## TEXT
def clean_ansi(s):
    return re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]').sub('', s)

def real_length(s):
    return len(clean_ansi(s))

def break_line(_inline,_len,_separator=' '):
    # check if line is over length provided
    if real_length(_inline) > _len:
        clean = clean_ansi(_inline)
        current = ''
        control = ''
        lines = []

        for i,(clen,real) in enumerate(zip(clean.split(_separator),_inline.split(_separator))):
            # dont add separator if no current
            sep = (_separator if len(current) else "") 

            # add string to line if not too long
            if len(control+_separator+clen) <= _len:
                current += sep + real
                control += sep + clen

            # add current to lines
            elif len(current):
                lines.append(current)

            # set new current and control values
            current = real
            control = clen

        # add leftover values
        if len(current):
            lines.append(current)

        return lines

    # return original line in array
    else:
        return _inline.split(_separator)

## UI
def printTo(x=0,y=0,s='',clear=False):
    # clear the len of string with 1 margin on both sides
    if clear:
        print(f'\033[{y};0H'+'\033[K')
    else:
        print(f'\033[{y};{x-1}H'+(len(s)+2)*' ')

    # print
    print(f'\033[{y};{x}H'+s)



# GLOBALS
WIDTH,HEIGHT = os.get_terminal_size()
KEEP_GOING = True
SESSION = requests.Session()

## set by user
URL = "http://localhost:5000/api/v0/"
ROOMID = "conv1"
USERNAME = "pink"
MESSAGE_BREAKLEN = 5

# given by server
COOKIE = "flamingosareblue"

# base data array to append to
BASE_DATA = {
    "username": USERNAME,
    "cookie": COOKIE,
    "chatroom": ROOMID,
}

BINDS = {
    "ESCAPE": {
        "i": "mode_insert",
        "j": "navigate_down",
        "k": "navigate_up",
        "a": "mode_add",
        "r": "mode_react",
        "m": "mode_message",
        "q": "quit"
    },
    "INSERT": {
        "ESC": "mode_escape"
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
switch_mode("ESCAPE")



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
        printTo(WIDTH-len(key),3,key,clear=1)

        # ^C behavior: will likely be properly binded
        # currently inactive
        if key == "SIGTERM":
            KEEP_GOING = 0
            print('\033[?25h')
            break

        # go to escape mode if escape pressed
        elif key == "ESC":
            handle_action("mode_escape")
            continue

        # INSERT mode: inputs
        if MODE == "INSERT":
            # send key to inputfield to handle
            infield.send(key)

            # print inputfield
            infield.print()

        # ESCAPE mode: shortcuts
        elif key in VALID_KEYS:   
            action = BINDS[MODE][key]
            handle_action(action)
        

def handle_action(action):
    global KEEP_GOING

    printTo(WIDTH-len(action),2,action,clear=1)
    
    if action.startswith('mode_'):
        action = action.replace('mode_','')
        infield.print(highlight=(action=="INSERT"))
        switch_mode(action.upper())


    if MODE == "ESCAPE":
        if action == "quit":
            print('\033[?25h')
            KEEP_GOING = 0


# UI
## get and sort messages, add lines attribute
def get_lines():
    # TODO: this 0 might be too much in the future
    messages_raw = get(0)
    messages = []

    # sort messages
    for m in sorted(messages_raw,key=lambda x: x['time']):
        # add representation of file 
        if m['type'] == 'file':
            m['message'] = f"`.{m['extension']}` file."

        # decode message
        elif m['type'] == 'text':
            m['message'] = decode(m['message'])

        # break message into lines
        m['lines'] = []
        #m['lines'].append(m['username'])
        m['lines'] += break_line(m['message'],MESSAGE_BREAKLEN)

        # add message to list
        messages.append(m)

    return messages


# TEMP MAIN
if __name__ == "__main__":
    ##  TODO: add x, y limit
    infield = getch.InputField()

    ## clear screen
    print('\033[2J')

    # input thread
    threading.Thread(target=getch_loop).start()
##
    # main loop
    while KEEP_GOING:
        #with open('test.json','w') as f:
        #    f.write(json.dumps(get_lines(),indent=4))
        #    break
        time.sleep(1)
