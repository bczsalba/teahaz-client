# :main= python3 %

# IMPORTS
import os
import sys
import json
import time
import getch
import base64
import requests
import threading
import pyperclip as clip
from ui import Container,Prompt,Label,italic,bold,underline,container_from_dict
from ui import clean_ansi,real_length,break_line,WIDTH,HEIGHT



# HELPERS #

### b64 encode
def encode(a):
    return base64.b64encode(a.encode('utf-8')).decode('utf-8')

### b64 encode into bytes
def encode_binary(a):
    return base64.b64encode(a).decode('utf-8')

### b64 decode
def decode(a):
    return base64.b64decode(a).decode('utf-8')




# INTERNAL #

## import settings from json
def import_settings():
    global SETTINGS

    with open(os.path.join(PATH,'settings.json'),'r') as f:
        SETTINGS = json.load(f)
        for key,item in SETTINGS.items():
            globals()[key] = item

    if is_set('MODE'):
        switch_mode(MODE)

## edit setting in json (needed because lambda cannot do assignments)
def edit_setting(key,value):
    global SETTINGS

    # get value if needed
    if callable(value):
        value = value()

    # change setting
    SETTINGS[key] = value

    # write to file
    with open(os.path.join(PATH,'settings.json'),'w') as f:
        f.write(json.dumps(SETTINGS,indent=4))

    # reimport settings
    import_settings()

## send args to logfile
def dbg(*args):
    if not DO_DEBUG:
        return

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

## merge two dicts together, on conflict overwrite one's values
def merge(one,two):
    merged = one.copy()
    for key in two.keys():
        for subkey,value in two[key].items():
            merged[key][subkey] = value
    return merged

## split `s` by delimiters defined in `DELIMITERS`, return array of words
def split_by_delimiters(s,return_indices=False):
    # set up variables
    wordlist = []
    indices = []
    buff = ""

    # create list separated by non-shitespace
    for i,c in enumerate(s):
        if c in DELIMITERS: 
            if return_indices:
                indices.append(i)

            wordlist.append(buff)
            buff = ""
        else:
            buff += c

    wordlist.append(buff)

    if return_indices:
        indices.append(i)
        return wordlist,indices
    else:
        return wordlist

## return True if the given `index` is part of the last word in the strong
def is_in_last_word(index,string):
    wordlist = split_by_delimiters(string)
    last_word_index = len(string)-len(wordlist[-1])
    return (last_word_index <= index)

## switch to input mode, set globals
def switch_mode(target):
    global MODE, VALID_KEYS, BINDS

    if VIMMODE:
        BINDS = VIMBINDS

    else:
        if target == "ESCAPE":
            target = "INSERT"
        BINDS  = BASEBINDS

    MODE = target
    VALID_KEYS = [key for key in BINDS[MODE].keys()]
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


## input dialog class
class InputDialog(Container):
    def __init__(self,options=None,label_value='',label_justify="center",label_underpad=0,field_value='',**kwargs):
        super().__init__(**kwargs)

        # set up label class
        self.label = Label(value=label_value,justify=label_justify)

        # set up field depending on options given
        self.options = options
        if isinstance(options,list):
            self.field = Prompt(options=options,width=20)
        else:
            self.field = InputDialogField(default=field_value,print_at_start=False)
        
        # add label
        self.add_elements([self.label])

        # add paddings under label
        for _ in range(label_underpad):
            self.add_elements(Label())

        # add field
        self.add_elements([self.field])
        
        # set xlimit of field
        self.field.xlimit = self.width-3

    def submit(self):
        self.value = self.field.submit()
        return self.value

    def __repr__(self):
        self.width = max(self.width,self.field.width)
        self.get_border()
        self.center()
        self.wipe()

        return super().__repr__()


## field class for input dialog
class InputDialogField(getch.InputField):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.width = len(self.value)
        self.height = 1
        self._is_selectable = False
        self.options = None

    # return text of self
    def __repr__(self):
        line = self.print(return_line=True)
        return line

    # return value
    def submit(self):
        return self.value
    
    # def send(self,*args,**kwargs):
    #    key = args[0]
    #    if key == "BACKSPACE" and len(self.value):
    #        self.width -= 1
    #    else:
    #        self.width += 1

    #    super().send(*args,**kwargs)




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




# INPUT #

## key intercepter loop, separate thread
def getch_loop(): 
    global PIPE_OUTPUT

    buff = ''
    while KEEP_GOING:
        key = getch.getch()

        # this lets other functions hijack the key output as parameters
        if PIPE_OUTPUT:
            fun,args = PIPE_OUTPUT
            fun(key,**args)
            
            if not KEEP_PIPE:
                PIPE_OUTPUT = None
            continue
        
        # add key to buffer if key+buffer is in either key cluster
        elif MODE != "INSERT" and len(buff):
            for v in VALID_KEYS:
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

        # shortcuts
        elif key in VALID_KEYS:   
            action = BINDS[MODE][key]
            handle_action(action)

        # INSERT mode: inputs
        elif MODE == "INSERT":
            # ignore unrecognized ctrl keys
            if key.startswith('CTRL_'):
                continue

            # send key to inputfield to handle
            infield.send(key)

            # print inputfield
            infield.print() 

## act on action
def handle_action(action):
    global KEEP_GOING,PIPE_OUTPUT,PIPE_ARGS,VISUAL_START,VISUAL_END,infield

    printTo(WIDTH-len(action),2,action,clear=1)
    


    ## INLINE ACTIONS
    # quit program in a clean way
    if action == "quit":
        print('\033[?25h')
        KEEP_GOING = 0
        sys.exit()

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

    elif action == "paste":
        cursor = infield.cursor
        paste = clip.paste()

        offset = (1 if VIMMODE else 0)

        left = infield.value[:cursor+offset]
        right = infield.value[cursor+offset:]
      
        infield.set_value(left+paste+right,infield.cursor+len(paste))



    ## CATEGORIES
    # mode switching
    if action.startswith('mode_'):
        # filter out start of string
        action = action.replace('mode_','')
        
        if action.upper() == MODE:
            return

        # if going into escape mode move cursor 
        if action == "escape" and len(infield.value) and MODE != "VISUAL" and infield.cursor > 0:
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
        insert = False

        # filter out start of string
        action = action.replace('goto_','')


        # horizontal jumping
        if action == "line_start":
            insert = True
            infield.cursor = 0 

        elif action == "line_end":
            insert = True
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

    
        # go to start of text
        elif action == "text_start":
            infield.cursor = 0

        # go to end of text
        elif action == "text_end":
            infield.cursor = len(infield.value)

        # navigate in `word`-s and `WORD`-s
        elif action.startswith('word') or action.startswith('WORD'):
            # get words and indices using delimiters
            if action.startswith('word'):
                words,indices = split_by_delimiters(infield.value,return_indices=True)

            # get words and indices using whitespaces
            else:
                words = []
                indices = []
                buff = ''
                for i,c in enumerate(infield.value):
                    if c == ' ':
                        words.append(buff)
                        indices.append(i)
                        buff = ''
                    else:
                        buff += c
                words.append(buff)
                indices.append(i)

            # find the w/W the cursor is in
            buff = 0
            for i,index in enumerate(indices):
                if index >= infield.cursor:
                    break

            # go to next
            if action.endswith("_next"):
                if i == len(words)-1:
                    return

                infield.cursor = index+1

            # go to previous 
            elif action.endswith("_prev"):
                if i == 0:
                    return

                word = words[i-1]
                infield.cursor = indices[i-1]-len(word)

        # switch mode, print
        if insert:
            switch_mode('INSERT')
        infield.print()

    # visual mode
    elif action.startswith('selection_'):
        if action == "selection_right":
            VISUAL_END = min(VISUAL_END+1,len(infield.value)-1)

        elif action == "selection_left":
            VISUAL_END = max(VISUAL_END-1,0)

        elif action == "selection_delete":
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

        elif action.endswith("cut") or action.endswith("copy"):
            # get start and end values
            start = infield.selected_start
            end = infield.selected_end

            # store selected value
            selected = infield.value[start:end]
            clip.copy(selected)

            if action.endswith("cut"):
                # set new value
                left = infield.value[:start]
                right = infield.value[end:]
                infield.set_value(left+right,start)

            switch_mode("ESCAPE")
            return
        
        elif action.endswith("uppercase") or action.endswith("lowercase"):
            # get start,end
            start = infield.selected_start
            end = infield.selected_end

            # get sides to use
            selected = infield.value[start:end]
            left = infield.value[:start]
            right = infield.value[end:]

            # do upper/lowecase
            if action.endswith("uppercase"):
                selected = selected.upper()

            elif action.endswith("lowercase"):
                selected = selected.lower()

            # set new value
            infield.set_value(left+selected+right,infield.cursor)
            switch_mode("ESCAPE")
            return
            
        
        # update cursor
        infield.cursor = VISUAL_END
        infield.visual(VISUAL_START,VISUAL_END)

    # action done to end
    elif action.endswith('_end'):
        if action.startswith('select'):
            if action == "select_line_end":
                VISUAL_END = len(infield.value)-1

            elif action == "select_word_end":
                 start,end = get_indices('w')
                 VISUAL_END = end-1
            infield.visual(VISUAL_START,VISUAL_END)

        elif action.startswith('delete') or action.startswith('change'):
            if action == "delete_line_end":
                end = len(infield.value)
                selected = infield.value[infield.cursor:end]
                clip.copy(selected)

                infield.set_value(infield.value[:infield.cursor])

            elif action.endswith("_word_end"):
                indices = get_indices('w')
                if not indices or not len(indices) == 2:
                    return
                else:
                    start,end = indices

                value = infield.value[:infield.cursor]+infield.value[end:]

                infield.set_value(value,infield.cursor,force_cursor=1)

                if action.startswith("change"):
                    switch_mode("INSERT")

    # actions done on entire line
    elif action.endswith('_line'):
        if action == "delete_line":
            clip.copy(infield.value)
            infield.set_value('')       

        elif action == "select_line":
            VISUAL_START = 0
            VISUAL_END = len(infield.value)

            infield.visual(VISUAL_START,VISUAL_END)
            switch_mode("VISUAL")

    # menu actions
    elif action.startswith('menu_'):
        # call menu handler
        globals()[action]()


    
    ## PIPES
    ### action_in actions
    elif action.endswith("_in"):
        PIPE_OUTPUT = do_in,{'action': action}
    
    ### find & till
    elif action == "find":
        PIPE_OUTPUT = find,{}

    elif action == "find_reverse":
        PIPE_OUTPUT = find,{'reverse': True}
    
    elif action == "till":
        PIPE_OUTPUT = find,{'offset': -1}

    elif action == "till_reverse":
        PIPE_OUTPUT = find,{'offset': -1, 'reverse': True}


def handle_menu(key,menu,obj,prev=None):
    global PIPE_OUTPUT

    # settings menu related actions
    if menu == "settings":

        # choose a setting
        if key == "ENTER":

            # get selected child from obj
            selected = obj.selected[0]

            # decide if dialogue should be input or prompt type
            if isinstance(selected.real_value,dict):
                d = container_from_dict(selected.real_value,dbg('hi'),width=40)
                PIPE_OUTPUT = handle_menu,{"menu": "settings","obj": d, "prev": [menu,obj.selected_index]}
            
            else:
                value = selected.value
                if value in ["True","False"]:
                    options = [True, False]
                    width = 30
                else:
                    options = None
                    width = 40

                # create opject
                d = InputDialog(
                        label_value=bold(selected.label+':'),
                        label_underpad=1,
                        options=options,
                        field_value=selected.real_value,
                        width=40,
                )

                # select the current value in prompt
                if options:
                    index = [str(o) for o in options].index(value)
                    d.select(index)

                # overwrite submit function
                d.submit = lambda: edit_setting(selected.label,d.field.submit)


                # set new pipes
                PIPE_OUTPUT = handle_menu,{"menu": "input_dialog", "obj": d, "prev": [menu,obj.selected_index] }

            # clear previous container from screen
            obj.wipe()

            # center and print new container
            d.center()
            print(d)
            return 

    # input dialogue actions
    elif menu == "input_dialog":
        # submit input, go to previous menu by sending ESC
        if key == "ENTER":
            obj.submit()
            handle_menu("ESC",menu,obj,prev)

        # quit input
        elif key == "ESC":
            obj.wipe()
            
            # go to previous menu
            name, index = prev
            new = globals()["menu_"+name](index)

            # set new pipes
            PIPE_OUTPUT = handle_menu,{"menu": name,"obj": new}
            return

        else:
            if obj.options:
                if key in "jl":
                    obj.selected_index += 1

                elif key in "hk":
                    obj.selected_index -= 1

                obj.select()
                print(obj)

            else:
                obj.field.send(key)
                print(obj)

        return
            

    # universal to all menus
    if len(obj.selectables):
        selected = obj.selected_index
        if key == "j":
            obj.selected_index += 1
        elif key == "k":
            obj.selected_index -= 1

    if key == "ESC":
        PIPE_OUTPUT = None
        obj.wipe()
        infield.print()
        return
     
    PIPE_OUTPUT = handle_menu,{"menu": menu,"obj": obj}
    obj.select()
    print(obj)



# ACTION HANDLER FUNCTIONS #

## do `action` in infield.value, using get_indices for start/end
def do_in(param, action):
    global infield, VISUAL_START, VISUAL_END

    # react on error in indices
    indices = get_indices(param)
    if indices == None or len(indices) < 2:
        dbg("Indices is non-iterable:",indices)
        return
    else:
        start,end = indices

    # selection commands
    if action.startswith("select"):
        if action == "select_end":
            VISUAL_END = end

        elif action == "select_in":
            VISUAL_START = start
            VISUAL_END = end-1

        # update values
        infield.visual(VISUAL_START,VISUAL_END)
        if not KEEP_CURSOR_AFTER_SELECT:
            infield.cursor = VISUAL_END

    elif "copy" in action:
        # TODO add highlight here
        clip.copy(infield.value[start:end])

    elif any(o in action for o in ['change','delete']):
        # set up values
        left = infield.value[:start]
        right = infield.value[end:]
        cursor = start 

        # only do these if changing
        if action == "change_in":
            # add space if last word is edited
            if is_in_last_word(start,infield.value):
                left += ' '
                cursor += 1
            switch_mode("INSERT")  
            
        elif action == "delete_in":
            # store in clipboard
            clip.copy(infield.value[start:end])
        
        infield.set_value(left+right,cursor)
        
## find start,end indices for type `param` in infield
def get_indices(param):
    valid = ["w","W","'",'"','[]','{}','()','<>']

    # set up start, end pairs
    for pair in valid:
        if param in pair:
            # single length 
            if len(pair) == 1:
                end = param

            # double length
            ## opener
            elif pair.index(param) == 0:
                end = pair[1]

            ## closer
            else:
                param = pair[0]
                end = pair[1]
            break

    # return if both arent found
    else:
        return


    # find word
    if param in "wW":
        ## `word`-s are separated by characters in `DELIMITERS`
        if param == "w":
            wordlist = split_by_delimiters(infield.value)

        ## `WORD`-s are separated by whitespaces
        elif param == "W":
            wordlist = infield.value.split(' ')
        start = 0

        # loop through words to find start, wordindex
        for wordindex,word in enumerate(wordlist):
            # if the index is in word
            if start+len(word)+1 >= infield.cursor+1:
                break

            # otherwise iterate characers
            start += len(word)+1

        # get end
        end = start+len(wordlist[wordindex])



    # find in delimiters 
    else:
        # check if param, end in value
        tester = list(infield.value)
        param_found, end_found = 0,0

        # loop through tester, check for param and end
        for i,c in enumerate(tester):
            if not param_found and c == param:
                param_found = 1
                start = i+1
                tester.pop(i)

            elif not end_found and c == end:
                end_found = 1
                end = i+1
                tester.pop(i)


        # return if param, end not in string 
        if not all([param_found,end_found]):
            return None
        
    return start,end

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
    
def menu_settings(index=0):
    global PIPE_OUTPUT,KEEP_PIPE

    # open settings file
    with open('settings.json','r') as f:
        SETTINGS = json.load(f)
        c = container_from_dict(SETTINGS)

    # set pipes
    PIPE_OUTPUT = handle_menu,{"menu": "settings","obj": c}
    KEEP_PIPE = True

    # clear infield from screen
    infield.wipe()
    
    # do first selection
    c.selected_index = index
    c.select()

    # center
    c.center()

    # print
    print(c)
    
    return c





# GLOBALS
PATH = os.path.abspath(os.path.dirname(__file__))
import_settings()

LOGFILE = os.path.join(PATH,'log')
DELIMITERS = "!@#$%^&*()[]{}|\\;':\",.<>/? \t"

KEEP_GOING = True

SESSION = requests.Session()

INPUT = ""
INPUT_CURSOR = 0

VISUAL_START = 0
VISUAL_END = 0

PIPE_OUTPUT = None
PIPE_ARGS = {}
KEEP_PIPE = False

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
    if DO_DEBUG:
        open(LOGFILE,'w').close()

    ## clear screen
    print('\033[2J')

    # set default mode
    switch_mode("ESCAPE")
    infield = getch.InputField(pos=[0,HEIGHT-1])

    # main input loop
    getch_loop()
