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
    global PIPE_OUTPUT,PIPE_ARGS

    buff = ''
    while KEEP_GOING:
        key = getch.getch()

        # this lets other functions hijack the key output as parameters
        if PIPE_OUTPUT:
            PIPE_OUTPUT(key,**PIPE_ARGS)
            PIPE_OUTPUT = None
            PIPE_ARGS = {}
            continue
        
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
    global KEEP_GOING,PIPE_OUTPUT,PIPE_ARGS,infield

    printTo(WIDTH-len(action),2,action,clear=1)
    

    # mode switching
    if action.startswith('mode_'):
        # filter out start of string
        action = action.replace('mode_','')
        
        # if going into escape mode move cursor 
        if action == "escape" and len(infield.value):
            infield.cursor -= 1

        infield.print()

        # switch to mode
        switch_mode(action.upper())


    # input navigation
    elif action.startswith('goto_'):
        insert = True

        # filter out start of string
        action = action.replace('goto_','')


        # horizontal jumping
        if action == "line_start":
            infield.cursor = 0 

        elif action == "line_end":
            infield.cursor = len(infield.value)


        # horizontal movement
        elif action == "cursor_left":
            if len(infield.value):
                infield.cursor = max(0,infield.cursor-1)
                insert = False 

        elif action == "cursor_right":
            if len(infield.value):
                infield.cursor = min(len(infield.value)-1,infield.cursor+1)
                insert = False 

    
        # TODO: multiline support for infield
        elif action == "text_start":
            infield.linecursor = 0

        elif action == "text_end":
            infield.linecursor = len(infield.lines)


        # switch mode, print
        if insert:
            switch_mode('INSERT')
        infield.print()


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

    # vim-like change_in function
    elif action == "change_in":
        # hijack getch_loop output, send it to the change_in function
        PIPE_OUTPUT = change_in

    elif action == "character_delete":
        # convert value to list
        value = list(infield.value)

        if not len(value):
            return

        # pop cursor
        value.pop(infield.cursor)

        # convert back to str
        infield.value = ''.join(value)

        # adjust cursor pos
        if len(infield.value) == 0:
            infield.cursor == 0

        # set cursor to 0 if no text left
        elif infield.cursor > len(infield.value)-1:
            infield.cursor = len(infield.value)-1

        # print
        infield.print()

    elif action == "find":
        PIPE_OUTPUT = find

    elif action == "find_reverse":
        PIPE_OUTPUT = find
        PIPE_ARGS = {'reverse': True}
    
    elif action == "till":
        PIPE_OUTPUT = find
        PIPE_ARGS = {'offset': -1}

    elif action == "till_reverse":
        PIPE_OUTPUT = find
        PIPE_ARGS = {'offset': -1, 'reverse': True}



# ACTION HANDLER FUNCTIONS
## these are actions that require a parameter key
def change_in(param):
    global infield

    valid = ["w","'",'"','[]','{}','()','<>']

    # set up start, end pairs
    for pair in valid:
        if param in pair:
            # single length 
            if len(pair) == 1:
                end = param

            # double length, opener
            elif pair.index(param) == 0:
                end = pair[1]
            # double length, closer
            else:
                param = pair[0]
                end = pair[1]
            break

    # return if param isnt in valid
    else:
        return

    # return if param isnt in input value
    if not param == "w" and not param in infield.value:
        return

    # word
    if param == "w":
        # set up variables
        words = infield.value.split(' ')
        characters = 0

        # loop through words
        for wordindex,word in enumerate(words):

            # if the index is in word
            if characters+len(word+' ') >= infield.cursor+1:
                break

            # otherwise iterate characers
            characters += len(word+' ')

        # remove chosen word from words
        words.pop(wordindex)

        # clear current input
        infield.wipe()

        # update value
        infield.value = ' '.join(words)

        # get spaces in value for cursor
        spaces = [0]
        for i,c in enumerate(infield.value):
            if c == " ":
                spaces.append(i)
        spaces.append(len(infield.value))

        # set cursor, add space to the left
        infield.cursor = spaces[wordindex]
        if not infield.cursor == 0:

            # separate two sides
            left = infield.value[:infield.cursor]
            right = infield.value[infield.cursor:]
            
            # add space
            infield.value = left+' '+right
            infield.cursor += 1


    # others
    else:
        # find start
        startpos = infield.value.index(param)

        # find end
        endindex = infield.value[startpos+1:].index(end)
        endpos = startpos+endindex+1

        # set two sides up
        left = infield.value[:startpos+1]
        right = infield.value[endpos:]

        # update cursor
        infield.cursor = startpos+1

        # wipe previous
        infield.wipe()

        # update value
        infield.value = left+right

    # print, switch mode
    infield.print()
    switch_mode('INSERT')

def find(key,offset=0,reverse=False):
    global infield

    # set variables
    value = infield.value
    index = infield.cursor

    # apply reverse search setup
    if reverse:
        fromcursor = value[::-1][len(value)-index:]

    # apply normal search setup
    else:
        fromcursor = value[index+1:]

    # dont do anything if not found in infield
    if not key in fromcursor:
        return

    # set found
    found = fromcursor.index(key)

    # get cursor depending on reverse
    if reverse:
        infield.cursor -= found + 1 + offset
    else:
        infield.cursor = infield.cursor + offset + found + 1

    # print infield
    infield.print()
    



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
PIPE_ARGS = {}

# given by server
COOKIE = "flamingoestothestore"

# base data array to append to
BASE_DATA = {
    "username": USERNAME,
    "cookie": COOKIE,
    "chatroom": ROOMID,
}



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
