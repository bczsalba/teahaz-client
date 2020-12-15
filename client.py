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
from settings import *



# HELPERS
## API
def encode(a):
    return base64.b64encode(a.encode('utf-8')).decode('utf-8')

def encode_binary(a):
    return base64.b64encode(a).decode('utf-8')

def decode(a):
    return base64.b64decode(a).decode('utf-8')

## DEV
def dbg(*args):
    s = ' '.join([str(a) for a in args])
    with open(LOGFILE,'a') as f:
        f.write(s+'\n')

## BINDS
def switch_mode(target):
    global MODE, VALID_KEYS, VIMKEYS

    MODE = target
    VALID_KEYS = [key for key in BINDS[target].keys()]

    ## get vim valid binds
    VIMKEYS = [key for key in VIMBINDS[MODE].keys()]

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
    global PIPE_OUTPUT

    buff = ''
    while KEEP_GOING:
        key = getch.getch()

        # this lets other functions hijack the key output as parameters
        if PIPE_OUTPUT:
            PIPE_OUTPUT(key)
            PIPE_OUTPUT = None
        
        # add key to buffer if key+buffer is in either key cluster
        elif MODE != "INSERT" and len(buff):
            for v in VIMKEYS+VALID_KEYS:
                buffkeylen = len(buff+key)-1
                if buff+key in v:
                    _buffkey_valid = True
                    break

                # TODO: add wildstar char for ci
                #elif len(v) >= buffkeylen+1 and v[buffkeylen] == "*":
                #    _buffkey_valid = True
                #    break
            else:
                _buffkey_valid = False

            # add key 
            if _buffkey_valid:
                key = buff+key
                buff = key
                printTo(WIDTH-5,4,'multi',clear=1)

            # "reset" key
            else:
                buff = key
                printTo(WIDTH-6,4,'single',clear=1)
        
        # reset buffer
        else:
            buff = key


        printTo(WIDTH-len(key),3,key,clear=1)

        # currently inactive
        if key == "SIGTERM":
            handle_action('quit')

        # go to escape mode from any menu
        elif key == ESCAPE_KEY:
            handle_action("mode_escape")
            continue

        # check if key is a valid single key vimbind
        elif VIMMODE and key in VIMBINDS[MODE]:
            action = VIMBINDS[MODE][key]
            handle_action(action)   

        # shortcuts
        elif key in VALID_KEYS:   
            action = BINDS[MODE][key]
            handle_action(action)

        # INSERT mode: inputs
        elif MODE == "INSERT":
            # send key to inputfield to handle
            infield.send(key)

            # print inputfield
            infield.print() 



def handle_action(action):
    global KEEP_GOING,PIPE_OUTPUT

    printTo(WIDTH-len(action),2,action,clear=1)
    

    # mode switching
    if action.startswith('mode_'):
        # filter out start of string
        action = action.replace('mode_','')
        
        # print infield with highlight controlled by mode
        infield.print(highlight=(action=="insert"))

        # switch to mode
        switch_mode(action.upper())


    # input navigation
    elif action.startswith('goto_'):
        # filter out start of string
        action = action.replace('goto_','')

        if action == "line_start":
            infield.cursor = 0 

        elif action == "line_end":
            infield.cursor = len(infield.value)

        # TODO: multiline support for infield
        elif action == "text_start":
            infield.linecursor = 0

        elif action == "text_end":
            infield.linecursor = len(infield.lines)

        switch_mode('INSERT')
        infield.print()


    # vim-like change_in function
    elif action == "change_in":
        # hijack getch_loop output, send it to the change_in function
        PIPE_OUTPUT = dbg

    # quit program in a clean way
    elif action == "quit":
        print('\033[?25h')
        KEEP_GOING = 0

    # message binds
    elif action == "message_send":
        # TODO: add command interface option here
        msg = infield.value
        send(msg,'text')

    # TODO
    elif action == "insert_newline":
        infield.send('\n')



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



# GLOBALS
PATH = os.path.abspath(os.path.dirname(__file__))
LOGFILE = os.path.join(PATH,'log')
WIDTH,HEIGHT = os.get_terminal_size()
KEEP_GOING = True
SESSION = requests.Session()
INPUT = ""
INPUT_CURSOR = 0
PIPE_OUTPUT = None

# given by server
COOKIE = "flamingoestothestore"

# base data array to append to
BASE_DATA = {
    "username": USERNAME,
    "cookie": COOKIE,
    "chatroom": ROOMID,
}

#VIMVALID = []
#_vimbind_maxlen = max([len(bind) for bind in VIMBINDS.keys()])
#for _ in range(_vimbind_maxlen):
#    VIMVALID.append([])



# TEMP MAIN
if __name__ == "__main__":
    ##  TODO: add x, y limit
    infield = getch.InputField()

    ## clear screen
    print('\033[2J')

    # input thread
    threading.Thread(target=getch_loop).start()

    # set default mode
    switch_mode("ESCAPE")

    # main loop
    while KEEP_GOING:
        with open('test.json','w') as f:
            f.write(json.dumps(get_lines(),indent=4))
        time.sleep(1)
