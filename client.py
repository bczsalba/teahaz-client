# :main= python3 %

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
from getch import clean_ansi,real_length,break_line



# HELPERS

### b64 encode
def encode(a):
    return base64.b64encode(a.encode('utf-8')).decode('utf-8')

### b64 encode into bytes
def encode_binary(a):
    return base64.b64encode(a).decode('utf-8')

### b64 decode
def decode(a):
    return base64.b64decode(a).decode('utf-8')

# DEV

## send args to logfile
def dbg(*args):
    s = ' '.join([str(a) for a in args])
    with open(LOGFILE,'a') as f:
        f.write(s+'\n')

## check if variable is in scope
def is_set(var,scope=None):
    if scope == None:
        scope = globals()
    return (var in scope and scope[var])

## do `fun` after `ms` passes, nonblocking
def do_after(ms,fun,control='true',args={}):
    timed = lambda: (time.sleep(ms/1000),
                     fun(**args) if is_set(control) else 0)

    threading.Thread(target=timed).start()


# BINDS #

## switch to input mode, set globals
def switch_mode(target):
    global MODE, VALID_KEYS, VIMKEYS

    MODE = target
    VALID_KEYS = [key for key in BINDS[target].keys()]

    ## get vim valid binds
    VIMKEYS = [key for key in VIMBINDS[MODE].keys()]

    printTo(WIDTH-len(MODE),0,MODE,clear=1)


# UI #

## print s to coordinates, clear space for it if needed
def printTo(x=0,y=0,s='',clear=False):
    # clear the len of string with 1 margin on both sides
    if clear:
        print(f'\033[{y};0H'+'\033[K')
    else:
        print(f'\033[{y};{x-1}H'+(len(s)+2)*' ')

    # print
    print(f'\033[{y};{x}H'+s)



# NETWORK FUNCTIONS #

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

## act on action
def handle_action(action):
    global KEEP_GOING,PIPE_OUTPUT,PIPE_ARGS,VISUAL_START,VISUAL_END,infield

    printTo(WIDTH-len(action),2,action,clear=1)
    

    ## CATEGORIES
    # mode switching
    if action.startswith('mode_'):
        # filter out start of string
        action = action.replace('mode_','')
        
        if action.upper() == MODE:
            return

        # if going into escape mode move cursor 
        if action == "escape" and len(infield.value) and MODE != "VISUAL":
            infield.cursor -= 1

        elif action == "visual":
            VISUAL_START = infield.cursor
            VISUAL_END = infield.cursor

            infield.selected_start = VISUAL_START
            infield.selected_end = VISUAL_END

        infield.print()

        # switch to mode
        switch_mode(action.upper())

    # input navigation
    elif action.startswith('goto_'):
        # go to insert mode at the end
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

    # visual mode
    elif action.startswith('visual_'):
        action = action.replace('visual_','')

        if action == "selection_right":
            VISUAL_END = min(VISUAL_END+1,len(infield.value)-1)

        elif action == "selection_left":
            VISUAL_END = max(VISUAL_END-1,0)

        elif action == "selection_delete":
            dbg(infield.selected_start,infield.selected_end)

            # split up value to not include selected
            if infield.selected_start == infield.selected_end:
                handle_action('character_delete')
                switch_mode('ESCAPE')
                return
            else:
                left = infield.value[:infield.selected_start]
                right = infield.value[infield.selected_end:]

            # set value
            infield.set_value(left+right,infield.selected_start)

            # switch mode
            switch_mode('ESCAPE')
            return

        infield.cursor = VISUAL_END
        infield.select(VISUAL_START,VISUAL_END)



    ## INLINE ACTIONS
    # quit program in a clean way
    elif action == "quit":
        print('\033[?25h')
        KEEP_GOING = 0

    # message binds
    elif action == "message_send":
        msg = infield.value
        ret = send(msg,'text')
        dbg(ret)
        if 'OK' in ret:
            infield.clear_value()

    # TODO
    elif action == "insert_newline":
        infield.send('\n')

    elif action == "character_delete":
        # convert value to list
        value = list(infield.value)

        if not len(value) > 0:
            return

        # pop cursor
        value.pop(infield.cursor)

        # convert back to str
        value = ''.join(value)

        if infield.cursor >= len(value)-1:
            cursor = None
        else:
            cursor = infield.cursor
        infield.set_value(value,cursor=cursor)

    
    ## PIPES
    # vim-like change_in function
    elif action == "change_in":
        PIPE_OUTPUT = change_in

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

        # update value
        value = ' '.join(words)

        # get spaces in value for cursor
        spaces = [0]
        for i,c in enumerate(value):
            if c == " ":
                spaces.append(i)
        spaces.append(len(value))

        # set cursor, add space to the left
        infield.cursor = spaces[wordindex]

        if infield.cursor == 0:
            infield.set_value(value,False)

        else:
            # separate two sides
            left = value[:infield.cursor]
            right = value[infield.cursor:]

            # figure out amount of whitespace needed
            if len(right) and right[0] == ' ':
                if len(right) > 1:
                    whitespaces = 1
                else:
                    whitespaces = 2
            else:
                whitespaces = 2

            # add whitespace
            value = left+whitespaces*' '+right
            
            # set value
            infield.set_value(value,infield.cursor+1)

    # others
    else:
        # check if param, end in value
        tester = list(infield.value)
        param_found, end_found = 0,0

        for i,c in enumerate(tester):
            if not param_found and c == param:
                param_found = 1
                tester.pop(i)

            elif not end_found and c == end:
                end_found = 1
                tester.pop(i)

            dbg(tester)

        dbg(param_found,end_found)
        if not all([param_found,end_found]):
            return

        # find start
        startpos = infield.value.index(param)

        # find end
        endindex = infield.value[startpos+1:].index(end)
        endpos = startpos+endindex+1

        # set two sides up
        left = infield.value[:startpos+1]
        right = infield.value[endpos:]

        # set new value
        infield.set_value(left+right,startpos+1)

    # print, switch mode
    switch_mode('INSERT')

## find key, set cursor to index+offset
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

VISUAL_START = 0
VISUAL_END = 0

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
    infield = getch.InputField(pos=[0,HEIGHT-1],xlimit=5)

    ## clear screen
    print('\033[2J')

    # input thread
    threading.Thread(target=getch_loop).start()

    # set default mode
    switch_mode("ESCAPE")

    # main loop
    while KEEP_GOING:
        time.sleep(1)
