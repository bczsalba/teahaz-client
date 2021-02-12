# :main= python3 %

# IMPORTS
import os
import sys
import json
import time
import getch
import base64
import requests
import pytermgui
import threading
import pyperclip as clip
from urllib.parse import urlparse
from pytermgui import WIDTH,HEIGHT
from pytermgui import clean_ansi,real_length,break_line
from pytermgui import italic,bold,underline,color,highlight
from pytermgui import Container,Prompt,Label,container_from_dict



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

## settings
### import settings from json
def import_json(name):
    with open(os.path.join(PATH,name+'.json'),'r') as f:
        globals()[name.upper()] = json.load(f)
        d = globals()[name.upper()]
        for key,item in d.items():
            globals()[key] = item

    if is_set('MODE'):
        switch_mode(MODE)

    if name == "settings":
        current_colorscheme = d['SELECTED_THEME']
        globals()['THEME'] = d['THEMES'][current_colorscheme]

## edit setting in json (needed because lambda cannot do assignments)
def edit_json(key,value,json_path,keys=[]):
    # get value if needed
    okey = key
    ovalue = value

    if isinstance(json_path,dict):
        data = json_path
    else:
        with open(os.path.join(PATH,json_path),'r') as f:
            data = json.load(f)

    if len(keys) == 0:
        keys = [key]

    setting = keys[-1]

    # eval value if needed
    if callable(value):
        value = value()

    # find root of current part of dict
    if len(keys) == 1:
        one = keys[0]
        root = data

    elif len(keys) == 2:
        one,two = keys
        root = data[one]

    elif len(keys) == 3:
        one,two,three = keys
        root = data[one][two]

    elif len(keys) == 4:
        one,two,three,four = keys
        root = data[one][two][three]
    
    # this shouldnt happen lol
    else:
        dbg('ERROR: invalid len(keys)',keys)
        return

    # apply change
    root[setting] = value

    # write to file
    if isinstance(json_path,str):
        with open(os.path.join(PATH,json_path),'w') as f:
            f.write(json.dumps(data,indent=4))

    # reimport settings
    import_json('settings')
    infield.pos = get_infield_pos()

def load_path(path,key=None):
    if isinstance(path,dict):
        return path

    with open(path,'r') as f:
        out = json.load(f)
        if key:
            out = out[key]
    return out


## miscellaneous
### send args to logfile
def dbg(*args):
    if not DO_DEBUG:
        return

    s = ' '.join([str(a) for a in args])

    method = sys._getframe().f_back.f_code.co_name
    obj = sys._getframe().f_back.f_locals.get('self')
    filename = sys._getframe().f_back.f_code.co_filename.split('/')[-1]
    lineno = sys._getframe().f_back.f_lineno

    get_caller = lambda: type(obj).__name__+'.'+method if obj else method

    with open(LOGFILE,'a') as f:
        f.write(f"{bold(color(filename,THEME.get('title')))}/{get_caller()}:{bold(color(lineno,THEME.get('value')))} : "+s+'\n')

### do `fun` after `ms` passes, nonblocking
def do_after(ms,fun,control='true',args={}):
    timed = lambda: (time.sleep(ms/1000),
                     fun(**args) if is_set(control) else 0)

    threading.Thread(target=timed).start()

### merge two dicts together, on conflict overwrite one's values
def merge(one,two):
    merged = one.copy()
    for key in two.keys():
        for subkey,value in two[key].items():
            merged[key][subkey] = value
    return merged

### look up key in dict by value
def reverse_dict_lookup(d,value):
    keys = list(d.keys())
    values = list(d.values())

    if value in values:
        index = values.index(value)
        return keys[index]
    else:
        return None

def ignore_input(*args):
    dbg('ignoring',args[0])


## variables
### check if variable is in scope
def is_set(var,scope=None):
    if scope == None:
        scope = globals()
    return (var in scope and scope[var])

def toggle_option(options,current):
    current_index = options.index(current)
    return options[len(options)-1-current_index]

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
    x,y = get_infield_pos()
    x -= 1
    y += 1
    if infield.line_offset:
        y += infield.line_offset

    if target == "ESCAPE":
        xstart = x
        for x in range(xstart,real_length(repr(MODE_LABEL))+2):
            sys.stdout.write(f'\033[{y};{x}H ')
        sys.stdout.flush()

    elif not PIPE_OUTPUT:
        MODE_LABEL.value = bold('-- '+target.upper()+' --')
        print(f'\033[{y};{x}H'+repr(MODE_LABEL))

    VALID_KEYS = [v for k,v in BINDS[MODE].items() if not k.startswith('ui__')]

### add caller of ui element to ui trace
def add_to_trace(arr):
    global UI_TRACE

    frame = sys._getframe().f_back
    lineno = frame.f_lineno
    _class = type(frame.f_locals['self']).__name__

    if not frame == None:
        _method = frame.f_code.co_name
        func = getattr(globals()[_class],_method)
        arr[0]['self'] = frame.f_locals['self']
    else:
        func = _method

    arr.insert(0,func)
    old = UI_TRACE[-1]
    oldfun,oldargs,_ = old
    newfun,newargs = func,arr[1]

    if not (oldfun == newfun and oldargs == newargs):# and oldargs == newargs):
        UI_TRACE.append(arr)

### redirect getch_loop to `fun` with `args`
def set_pipe(fun,arg,keep=1):
    global PIPE_OUTPUT, KEEP_PIPE

    PIPE_OUTPUT = fun,arg
    if not keep == None:
        KEEP_PIPE = keep

### set current ui file, accepts file paths and dicts
def set_current_file(value):
    globals()['CURRENT_FILE'] = value

### return current index of object
def get_index(obj):
    return obj.selected_index


## server
### set new chatroom, make transition to it
def set_chatroom(url,index):
    if index == 'invalid' or index == 'register':
        return

    globals()['URL'] = url
    chatrooms = SERVERS[url]
    globals()['CURRENT_CHATROOM'] = url,index

    edit_json('CURRENT_CHATROOM',[url,index],'usercfg.json')

def add_new_server(values):
    d = {}
    for key,value in values.items():
        if not key.startswith('ui__'):
            d[key] = value

    address = values.get('address')
    chatroom = values.get('chatroom')
    if SERVERS.get(address):
        SERVERS[address].append(chatroom)
    else:
        SERVERS[address] = [chatroom]

    
    with open(os.path.join(PATH,'usercfg.json'),'w') as f:
        f.write(json.dumps(SERVERS,indent=4))
    import_json('usercfg')

    return address,SERVERS[address].index(chatroom)


## editing
### split `s` by delimiters defined in `DELIMITERS`, return array of words
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

### return True if the given `index` is part of the last word in the strong
def is_in_last_word(index,string):
    wordlist = split_by_delimiters(string)
    last_word_index = len(string)-len(wordlist[-1])
    return (last_word_index <= index)




# UI FUNCTIONS #

## get what position infield should be at
def get_infield_pos():
    if 'infield' in globals().keys() and len(infield.value):
        offset = (len(infield.value)+1)//WIDTH

        if not infield.line_offset == offset:
            infield.wipe()

        infield.line_offset = offset

    else:
        offset = 0

    return [3,HEIGHT-2-offset]

## return to normal input
def return_to_infield(*args,**kwargs):
    global PIPE_OUTPUT,KEEP_PIPE
    
    #os.system('cls' if os.name == 'nt' else 'clear')
    infield.print()
    PIPE_OUTPUT = None
    KEEP_PIPE = False





# NETWORK FUNCTIONS #

# start threaded connection, TODO: ignore input
def start_connection(contype,menu=None,**kwargs):
    def _connect(*args,**kwargs):
        # decide function to use
        dbg('started')
        contype = args[0]
        if contype  == 'post':
            fun = SESSION.post
        elif contype == 'get':
            fun = SESSION.get
        else:
            dbg('implement',contype,'pls')
            raise NotImplementedError

        # try to get return value
        try:
            ret = fun(**kwargs)

        # connection timeout message
        except requests.exceptions.ConnectTimeout:
            ret = ["Connection timed out.",408]

        # connection error message
        except requests.exceptions.ConnectionError as e:
            dbg('Exception during',contype+': ',e)
            ret = ["Error happened during connection. Check log for more info.",-1]

        # unimplemented errors
        except Exception as e:
            dbg('implement',type(e).__name__,'pls')
            raise NotImplementedError

        return ret
    
    
    t = ThreadWithReturnValue(target=_connect,args=(contype,),kwargs=kwargs)
    t.start()
    ret_val = t.join()

    # NOTE to self: error button handler needs to have a handle_menu("ESC") at the end.
    #if not menu == None:
    #    handler = lambda prev,_: {
    #        prev.wipe(),
    #        handle_menu_actions(
    #            'menu_'+str(menu),
    #            pytermgui.get_object_by_id(str(menu)+"-button_submit").parent.dict_path)}
    #else:
    #    handler = lambda prev,_: {
    #        prev.wipe(),
    #        handle_menu('ESC',prev)}

    if isinstance(ret_val,list):
        ui.create_error_dialog(ret_val[0],'try again')
        return False

    elif not 200 <= ret_val.status_code < 300:
        ui.create_error_dialog(ret_val.text.strip(),'try again')
        return False

    else:
        return ret_val
        
def login_or_register(contype,url,data):
    dbg('logging in to',url)
    if contype == "login":
        d = {
                'username': data.get('username'),
                'password': data.get('password')
                }
    elif contype == "register":
        d = { 
                'username': data.get('username'),
                'password': data.get('password'),
                'email': data.get('email'),
                'nickname': data.get('nickname')
                }

    #handler = lambda prev,self: {
    #        prev.wipe(),
    #        handle_menu_actions('menu_'+contype,current_file=data) }
    
    if url == "":
        ui.create_error_dialog('Invalid value "'+url+'" for url.','choose other server')
        return 0 

    resp = start_connection('post',contype,url=url+'/'+contype,json=d,timeout=None)
    if not resp or not resp.status_code in range(200,299):
        dbg('bad response:',resp)
    else:
        text = "Successfully " + ("logged in" if contype == "login" else "registered")
        ui.create_success_dialog(text)
    

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
    global PIPE_OUTPUT,infield

    buff = ''
    while KEEP_GOING:
        key = getch.getch()

        infield.pos = get_infield_pos()

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
                #printTo(WIDTH-5,4,'multi',clear=1)

            # "reset" key
            else:
                buff = key
        
        # reset buffer
        else:
            buff = key


        # currently inactive
        if key == "SIGTERM":
            handle_action('quit')

        # shortcuts
        elif key in VALID_KEYS:   
            action = reverse_dict_lookup(BINDS[MODE],key)
            handle_action(action)

        # INSERT mode: inputs
        elif MODE == "INSERT":
            # ignore unrecognized ctrl keys
            if key.startswith('CTRL_'):
                continue

            # send key to inputfield to handle
            infield.send(key)

            x,y = infield.pos
            infield.pos = get_infield_pos()

            # print inputfield
            infield.print() 


## act on action
def handle_action(action):
    global KEEP_GOING,PIPE_OUTPUT,PIPE_ARGS,VISUAL_START,VISUAL_END,infield,CURRENT_FILE
    
    ## MENU ACTIONS
    if action.startswith('menu'):
        dbg('calling menu',action)
        handle_menu_actions(action)

    ## INLINE ACTIONS
    # quit program in a clean way
    if action == "quit":
        print('\033[?25h')
        KEEP_GOING = 0
        sys.exit()

    elif action == "reprint":
        fun,args,obj = UI_TRACE[-1]
        pytermgui.clr()
        fun(**args)
        return

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
        paste = clip.paste().replace('\n','') #TODO: this is temp

        offset = (1 if VIMMODE else 0)

        left = infield.value[:cursor+offset]
        right = infield.value[cursor+offset:]
      
        infield.set_value(left+paste+right,infield.cursor+len(paste))
        infield.pos = get_infield_pos()
        infield.print()




    ## CATEGORIES
    # mode switching
    if action.startswith('mode_'):
        # filter out start of string
        action = action.replace('mode_','')
        
        if action.upper() == MODE:
            return

        if action.endswith('+1'):
            infield.cursor += 1
            action = action[:-2]

        # if going into escape mode move cursor 
        if action == "escape" and len(infield.value) > 0 and MODE != "VISUAL" and infield.cursor > 0:
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

        if MODE == "VISUAL":
            cursor = VISUAL_END
        else:
            cursor = infield.cursor


        # horizontal jumping blank
        if action == "line_0th":
            cursor = 0 

        elif action == "line_-1st":
            cursor = len(infield.value)-1

        # horizontal jumping non-blank
        elif "line_start" in action:
            i = 0
            for i,c in enumerate(infield.value):
                if not c == " ":
                    break

            if action.endswith('_i'):
                insert = True

            cursor = i

        elif "line_end" in action:
            i = 0
            for i,c in enumerate(reversed(infield.value)):
                if not c == " ":
                    break

            if action.endswith('_i'):
                insert = True
            else:
                i += 1

            cursor = real_length(infield.value)-i

        elif "line_up" in action:
            startx,_ = infield.pos
            if len(infield.value) > WIDTH - startx:
                cursor -= WIDTH

        elif "line_down" in action:
            if len(infield.value) >= WIDTH+infield.cursor:
                cursor += WIDTH

        # horizontal movement
        elif action == "cursor_left":
            if len(infield.value):
                cursor = max(0,cursor-1)
                insert = False 

        elif action == "cursor_right":
            if len(infield.value):
                cursor = min(len(infield.value)-1,cursor+1)
                insert = False 

    
        # go to start of text
        elif action == "text_start":
            cursor = 0

        # go to end of text
        elif action == "text_end":
            cursor = len(infield.value)

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

                cursor = index+1

            # go to previous 
            elif action.endswith("_prev"):
                if i == 0:
                    return

                word = words[i-1]
                cursor = indices[i-1]-len(word)


        # switch mode, print
        if MODE == "VISUAL":
            VISUAL_END = cursor
            infield.visual(VISUAL_START,VISUAL_END)

            if not KEEP_CURSOR_AFTER_SELECT:
                infield.cursor = cursor
        else:
            infield.cursor = cursor
            infield.print()
        
        if insert:
            switch_mode('INSERT')


    # visual mode
    elif action.startswith('selection_') and not 'replace' in action:
        if action == "selection_right":
            VISUAL_END = min(VISUAL_END+1,len(infield.value)-1)

        elif action == "selection_left":
            VISUAL_END = max(VISUAL_END-1,0)

        elif action.endswith('delete') or action.endswith('change'):
            # split up value to not include selected
            if infield.selected_start == infield.selected_end:
                handle_action('character_delete')

                if action.endswith('change'):
                    switch_mode('ESCAPE')
                else:
                    switch_mode('INSERT')
                return

            else:
                left = infield.value[:infield.selected_start]
                right = infield.value[infield.selected_end:]

            # switch mode
            if action.endswith('delete'):
                switch_mode('ESCAPE')
            else:
                switch_mode('INSERT')

            # set value
            infield.set_value(left+right)

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

            if start == end:
                end += 1

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
        # selection
        if action.startswith('select'):
            if action == "select_line_end":
                VISUAL_END = len(infield.value)-1

            elif action == "select_word_end":
                 start,end = get_indices('w')
                 VISUAL_END = end-1
            infield.visual(VISUAL_START,VISUAL_END)

        # delete/change
        elif action.startswith('delete') or action.startswith('change'):
            if action == "delete_line_end" or action == "change_line_end":
                end = len(infield.value)
                selected = infield.value[infield.cursor:end]
                clip.copy(selected)

                if action.startswith('change'):
                    cursor = infield.cursor + 1
                    # TODO: this space should get removed with the next input
                    space = ' '
                    switch_mode('INSERT')
                else:
                    cursor = infield.cursor+1
                    space = ''

                infield.set_value(infield.value[:infield.cursor]+space,cursor)
                infield.line_offset = None

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
            infield.line_offset = 0 
            infield.wipe()
            infield.set_value('')

        elif action == "select_line":
            VISUAL_START = 0
            VISUAL_END = len(infield.value)

            infield.visual(VISUAL_START,VISUAL_END)
            switch_mode("VISUAL")


    
    ## PIPES
    ### action_in actions
    elif action.endswith("_in"):
        set_pipe(do_in,{'action': action},keep=1)
    
    ### find & till
    elif action == "find":
        set_pipe(find,{},keep=1)

    elif action == "find_reverse":
        set_pipe(find,{'reverse': True},keep=1)
    
    elif action == "till":
        set_pipe(find,{'offset': -1},keep=1)

    elif action == "till_reverse":
        set_pipe(find,{'offset': -1, 'reverse': True},keep=1)

    elif "replace" in action:
        if len(infield.value):
            set_pipe(replace,{'action': action},keep=1)


## handle action but for menus
def handle_menu(key,obj,attributes={},page=0):
    global PIPE_OUTPUT,UI_TRACE

    if isinstance(obj,list):
        objects = obj
        obj = obj[page]
        # this isnt working yet, TODO
        pytermgui.set_listener('window_size_changed', lambda *args: (d.center() for d in objects))

    # go up one menu using trace 
    if key == "ESC":
        obj.wipe()

        # go up the trace
        old = UI_TRACE[-1][2]
        removed = UI_TRACE.pop(-1)
        #dbg('removed',removed,'from trace.')

        fun,args,new = UI_TRACE[-1]
        #for e in UI_TRACE:
        #    dbg(e[0])
        #dbg()

        # create copy so the original dict isnt overwritten
        kwargs = args.copy()

        # execute trace
        d = fun(**kwargs) 
        if hasattr(old,'__ui_keys') and not d == None:
            setattr(d,'__ui_keys',old.__ui_keys)

        if hasattr(obj,'__ui_keys'):
            if len(obj.__ui_keys):
                obj.__ui_keys.pop(-1)

        return

    # get if horizontal navigation between prompt options should be used
    if not obj.selected == None:
        selected = obj.selected[0]
        options = selected.__dict__.get('options')
        _do_horizontal_nav = options and len(options) > 1
    else:
        _do_horizontal_nav = False


    # do actions specific to input dialog
    if isinstance(obj,InputDialog):
        # send key to field
        if hasattr(obj,'field') and isinstance(obj.field,InputDialogField) and (len(key) < 2 or key == 'BACKSPACE'):
            obj.field.send(key)
            print(obj)
            return

        # navigate prompt
        elif key == "ENTER":
            # edit setting
            new = obj.submit()
            edit_json(json_path=CURRENT_FILE,keys=obj.__ui_keys,key=obj.setting,value=new)

            # edit previous ui to show changes
            fun,kwargs,newobj = UI_TRACE[-2]
            if not type(kwargs.get('source')) in [None,list]:
                # set new value
                kwargs['source'].value = new

                # set new real_value
                kwargs['source'].real_value[obj.setting] = new

            # go back
            handle_menu("ESC",obj,attributes={'__ui_keys': obj.__ui_keys})
            #print(obj)
            return


    if key == "ENTER":
        if obj.selected == None:
            return

        # get obj and index
        selected,_,index = obj.selected
        
        if hasattr(selected,'handler'):
            selected.handler(obj,selected)
            return
        
        obj.wipe()

        # set previous trace element index
        UI_TRACE[-1][1]['index'] = index
        dbg(UI_TRACE[-1][:1])

        # add to depth
        obj.__ui_keys.append(selected.real_label)

        # create menu
        d = ui.create_submenu(selected)

        # select current option if possible
        if hasattr(d,'options') and d.options:
            d.selected_index = [o for o in d.options].index(selected.real_value)
            d.select()

        d.__ui_keys = obj.__ui_keys

        # print
        d.select()
        print(d)
        return
      
    elif key == " ":
        selected,_,index = obj.selected
        dbg(selected.__ui_options)
        if selected.__ui_options and len(selected.__ui_options) == 2:
            #if not globals().get(selected.real_label) == None:
            # add to depth
            selected.__ui_keys.append(selected.real_label)

            edit_json(
                    json_path=CURRENT_FILE,
                    keys=[selected.real_label],
                    key=selected.real_label,
                    value=toggle_option(selected.__ui_options, selected.real_value)
            )

            fun,args,obj = UI_TRACE[-1]
            args['index'] = index

            kwargs = args.copy()
            fun(**kwargs)
            selected.__ui_keys.pop(-1)
            return

    elif key == "CTRL_L":
        handle_action('reprint')

    elif key in "hjkl" or key.startswith("ARROW"):
        if isinstance(obj,InputDialog) or _do_horizontal_nav:
            if key in ["h","ARROW_LEFT"]:
                obj.selected_index -= 1
            elif key in ["l","ARROW_RIGHT"]:
                obj.selected_index += 1
            obj.select()

        if key in ["j","ARROW_DOWN"]:
            obj.selected_index += 1

        elif key in ["k","ARROW_UP"]:
            obj.selected_index -= 1

        elif len(objects) > 1:
            obj.wipe()
            if key in ["h","ARROW_LEFT"]:
                new = max(0,page-1)

            elif key in ["l","ARROW_RIGHT"]:
                new = min(len(objects)-1,page+1)

            obj = objects[new]
            set_pipe(handle_menu,{"obj": objects, "page": new})
            UI_TRACE[-1][1]['dict_index'] = new

    elif key == "SIGTERM":
        handle_action("quit")

    #if hasattr(obj,'__ui_keys'):
    #    value = ''
    #    dbg(obj.__ui_keys)
    #    for o in obj.__ui_keys:
    #        value += '/'+o
    #    dbg(value)

    #    pathbar = Label(value=value,justify="center",width=obj.width)
    #    x,y = obj.pos
    #    pathbar.pos = [0,y+obj.real_height+2]
    #    print(pathbar)



    obj.select()
    print(obj)


## call menu creation
def handle_menu_actions(action,current_file=None):#*args,**kwargs):#    
    menu = action.replace('menu_','')
    corners = [v for k,v in THEME['corners'].items()]
    dbg(corners)
    attrs = {}

    if menu == "settings":
        corners[1] = "settings"
        source = os.path.join(PATH,'settings.json')
    
    elif menu == "login_type":
        pytermgui.set_attribute_for_id('login_type-prompt','handler',lambda prev,self: {
                prev.wipe(), handle_action("menu_"+self.submit())})

        source = {
            "ui__title": "choose login type",
            "ui__padding": 0,
            "ui__id": "login_type-prompt",
            "ui__prompt": ["login","register"]
        }

    elif menu == "login":
        address,chatindex = CURRENT_CHATROOM
        chatid = SERVERS[address][chatindex]

        name = chatid+' @ '+address
        corners[1] = "login"
        pytermgui.set_attribute_for_id('login-button_submit','address',address)
        pytermgui.set_attribute_for_id('login-button_submit','handler',
                lambda prev,self: login_or_register('login',self.address,self.parent.dict_path))

        if current_file == None:
            source = {
                "ui__title": "Log into server",
                "ui__padding0": 0,
                "username": "",
                "password": "",
                "ui__padding1": 1,
                "ui__button": {
                    "id": "login-button_submit",
                    "value": "submit!"
                }
            }
        else:
            source = current_file
        
        attrs["address"] = URL

    elif menu == "register":
        address,chatindex = CURRENT_CHATROOM
        chatid = SERVERS[address][chatindex]

        pytermgui.set_attribute_for_id('register-button_submit','address',address)
        pytermgui.set_attribute_for_id('register-button_submit','handler',
                lambda prev,self: login_or_register('register',self.address,self.parent.dict_path))

        if current_file == None:
            source = {
                "ui__title": "Register onto server",
                "ui__padding0": 0,
                "username": "",
                "password": "",
                "email": "",
                "nickname": "",
                "ui__padding1": 1,
                "ui__button": {
                    "id": "register-button_submit",
                    "value": "submit!"
                }
            }

        else:
            source = current_file

        #attrs["address"] = URL

    elif menu == "server_new":
        pytermgui.set_attribute_for_id('server_new-button_add','handler',
                lambda prev,self: add_new_server(prev.dict_path))

        source = {
                "ui__title": "Add new connection",
                "ui__padding0": 0,
                "address": "",
                "chatroom": "",
                "ui__padding1": 1,
                "ui__button": {
                    "id": "server_new-button_add",
                    "value": "add!"
                }
            }


    elif menu == "picker":
        ui.create_menu_picker()
        return
    
    else:
        return True

    #globals()['CURRENT_FILE'] = path
    set_current_file(source)

    # call menu handler
    d = ui.create_menu(source=[load_path,{'path': source}],corners=corners)

    for key,value in attrs.items():
        if key == "id":
            pytermgui.set_element_id(d,value)
        else:
            setattr(d,key,value)





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
    global infield,VISUAL_END

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
    if MODE == "VISUAL":
        VISUAL_END = infield.cursor
        infield.visual(infield.selected_start,infield.cursor)
    else:
        infield.print()
    
def replace(key,action):
    dbg('action',action)
    val = infield.value

    if action == 'replace':
        # replace character at cursor
        val = list(val)
        val[infield.cursor] = key
        val = ''.join(val)

    elif action == "selection_replace":
        # replace characters in selected range
        length = infield.selected_end - infield.selected_start
        left = val[:infield.selected_start]
        right = val[infield.selected_end:]

        val = left+length*key+right
        switch_mode('ESCAPE')

    # set new value
    infield.set_value(val,infield.cursor)





# CLASSES # 
class ThreadWithReturnValue(threading.Thread):
    """
    Thread object that returns its value in the `join` method.
    taken from: https://stackoverflow.com/a/40344234
    """

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self,timeout=None):
        super().join(timeout=timeout)
        return self._return

class InputDialog(Container):
    """
    Class extending pytermgui.Container to add support 
    for more field types, a submit() method and to act
    as a prefab to the common dialog type Containers
    """
    def __init__(self,options=None,label_value='',label_justify="center",label_underpad=0,field_value='',dialog_type=None,**kwargs):
        super().__init__(**kwargs)
        gui = pytermgui.__dict__
        
        # set up label class
        self.label = Label(value=label_value,justify=label_justify)
        self.label.set_style('value',gui['CONTAINER_TITLE_STYLE'])

        # set up field depending on options given
        self.options = options
        self.dialog_type = dialog_type

        if self.dialog_type == None:
            if isinstance(options,list):
                self.dialog_type = "prompt"
            else:
                self.dialog_type = "field"

        if self.dialog_type == "prompt":
            self.field = Prompt(options=options,width=self.width)
            self.field.set_style('value',gui['CONTAINER_VALUE_STYLE'])
            self.field.set_style('label',gui['CONTAINER_LABEL_STYLE'])
        
        elif self.dialog_type == "field":
            self.field = InputDialogField(default=field_value,print_at_start=False)
            self.field.set_style('value',gui['CONTAINER_VALUE_STYLE'])
            self.field.field_color = '\033['+THEME['value']+'m'
            self.width = WIDTH
            borders = self.borders
            label_underpad += 2
            self.set_borders(['',borders[1],'',borders[3]])

        # add label
        self.add_elements(self.label)

        # add paddings under label
        for _ in range(label_underpad):
            self.add_elements(Label())

        # add field
        self.field.parent = self
        self.add_elements(self.field)
        
        # set xlimit of field
        self.field.xlimit = self.width-3

    def submit(self):
        self.value = self.field.submit()
        return self.value

    def __repr__(self):
        self.width = max(self.width,self.field.width)
        #self.get_border()
        #self.center()
        #self.wipe()

        return super().__repr__()

class InputDialogField(getch.InputField):
    """
    Class to extend getch's InputField to add compatibility
    for pytermgui Containers.
    """

    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.width = len(self.value)
        self.height = 1
        self._is_selectable = False
        self.options = None

        self.value_style = lambda item: item

    # return text of self
    def __repr__(self):
        value = self.print(return_line=True)
        line = self.value_style(value)
        return line
    
    def set_style(self,key,value):
        setattr(self,key+'_style',value)

    # return value
    def submit(self):
        return self.value

class UIGenerator:
    """
    Object used for organizing UI generator functions
    into one place. May also have some values stored
    in the future.
    """

    # wipe most recent ui element
    def wipe(self):
        UI_TRACE[-1][2].wipe()

    # create menu from a dictionary source
    def create_menu(self,source,corners,width=None,index=None,dict_index=0,**container_args):
        source_arg = source

        if isinstance(source,list):
            fun,kwargs = source
            source = fun(**kwargs)
        else:
            source = source_arg

        if width:
            width = width
        else:
            width = max(40,int(WIDTH*1/2))

        objects = container_from_dict(source,**container_args,width=width)
            
        for o in objects:
            if not source_arg == source:
                o.dict_path = kwargs['path']

            for i,c in enumerate([v for k,v in THEME['corners'].items()]):
                dbg(i,c)
                if not c == None:
                    o.set_corner(i,c)

            #o.width = min(WIDTH-5,o.width)
            o.center()

        c = objects[dict_index]

        # clear infield from screen
        infield.wipe()
        
        # set pipes
        if PIPE_OUTPUT:
            fun,_ = PIPE_OUTPUT
        else:
            fun = None
        if not fun == ignore_input:
            set_pipe(handle_menu,{"obj": objects, 'page': dict_index})

        if index == None:
            add_to_trace([
                {
                    'source': source_arg,
                    'index': None,
                    'dict_index': dict_index,
                    'corners': corners
                },c
            ])

        # print
        c.selected_index = (0 if index==None else index) 
        c.select()
        print(c)
        
        return c

    # create menu from object source, used for sub-level objects
    def create_submenu(self,source,index=None,dict_index=0):
        if isinstance(source.real_value,dict):
            dicts = container_from_dict(source.real_value,width=max(40,int(WIDTH*(1/2))))

            for d in dicts:
                # add title object to 0 index
                title = Label(value=pytermgui.CONTAINER_TITLE_STYLE(source.real_label),justify='center')
                d.add_elements(title)
                l = d.elements.pop(-1)
                d.elements.insert(0,l)

            d = dicts[dict_index]
            d.source_index = (0 if index==None else index) 
            if len(d.selectables):
                d.select()

        else:
            if isinstance(getattr(source,'__ui_options'),list):
                options = getattr(source,'__ui_options')
            else:
                options = None

            d = InputDialog(
                        label_value=source.real_label,
                        label_underpad=1,
                        options=options,
                        field_value=str(source.real_value),
                        width=max(40,int(WIDTH*(1/2)))
            )

            d.setting = source.real_label
            d.real_value = source.real_value
            dicts = [d]

        for dic in dicts:
            dic.setting = source.real_label
            dic.real_value = source.real_value
            dic.center()
            for i,c in enumerate([v for k,v in THEME['corners'].items()]):
                dic.set_corner(i,c)

        d = dicts[dict_index]
        d.selected_index = (0 if index==None else index) 
        d.select()
        print(d)

        fun,args = PIPE_OUTPUT
        dbg(fun)
        if not fun == ignore_input:
            set_pipe(handle_menu,{'obj': dicts, 'page': dict_index})
        if index == None:
            add_to_trace([{'source': source, 'index': index, 'dict_index': dict_index}, d])

        return d
 

            
    # create menu picker menu, likely only for dbg
    def create_menu_picker(self):
        d = Container(width=40)
        title = Label(value="pick your menu")
        title.set_style("value",pytermgui.CONTAINER_TITLE_STYLE)
        d.add_elements([title,Label()])

        for m in MENUS:
            name = m[5:]
            p = Prompt(options=[name],justify_options="center")
            p.action = m
            p.set_style('value',pytermgui.CONTAINER_VALUE_STYLE)
            p.handler = lambda prev,self: {prev.wipe(),handle_action(self.action)}
            d.add_elements(p)

        set_pipe(handle_menu,{'obj': [d]})
        add_to_trace([{},d])

        d.center()
        d.select()
        print(d)

        return d

    # unified way to create error dialog
    def create_error_dialog(self,text,button="ignore",handler=None):
        source = {
                    "ui__error_title": "Error occured!",
                    "ui__padding": "",
                    "ui__label": {
                        "value": ''.join(text.split('"')),
                        "justify": "left",
                        "padding": 4
                    },
                    "ui__padding1": "",
                    "ui__button": {
                        "id": "error-button_"+button,
                        "value": button,
                    }
                }

        ui.wipe()

        #if True or handler == None:
        handler = lambda _,self: handle_menu("ESC",self.parent)

        pytermgui.set_attribute_for_id('error-button_'+button,'handler',handler)

        d = self.create_menu(source,corners=[[],[],[],"error"])
        return d

    # unified way to create success dialog
    def create_success_dialog(self,text,button="dismiss"):
        source = {
                "ui__success_title": text,
                "ui__padding": "",
                "ui__button": {
                    "id": "success-button_"+button,
                    "value": button
                    }
                }

        ui.wipe()

        pytermgui.set_attribute_for_id('success-button_'+button,'handler',lambda prev,self: { handle_menu('ESC',prev), handle_menu('ESC',UI_TRACE[-1][2])})
        d = self.create_menu(source,corners=[[],[],[],"success"],width=25)
        return d

    # color code menu for settings/themes
    def create_colormenu(self,dict_index=0):
        width = max(40,int(WIDTH*(2/3)))
        dicts = []
        line_length = min(width//5,14)

        for index,ground in enumerate(['fg','bg']):
            count = 0
            c = Container(width=width,border=lambda: ['','','',''])

            # create color line
            for i in range(256//line_length):
                line = []
                for j in range(line_length):
                    count += 1
                    num = str(count)
                    pad = 4-len(num)
                    line.append('\033[38;5;'+num+'m' + pad*' ' + num)

                bg = ('\033[7m' if ground == 'bg' else '\033[1m')

                c.add_elements(Label(value=bg+' '.join(line)+'\033[0m'))


            #set up tabbar
            tabbar = Prompt(options=['foreground','background'])
            tabbar._is_selectable = False
            tabbar.set_style('highlight',pytermgui.TABBAR_HIGHLIGHT_STYLE)
            tabbar.select(index)


            # finalize dict
            c.center()
            c.add_elements([Label(),tabbar])
            dicts.append(c)

            
        c = dicts[dict_index]
        set_pipe(handle_menu,{'obj': dicts, 'page': dict_index})
        if dict_index == 0:
            add_to_trace([{'dict_index': dict_index},c])
        print(c)
        return c

    # def create_server_picker(self,source):

    ## add new server
    # def create_menu_server_add(self,url='',chatroom=''):
    #    source = {
    #            "ui__title": "new connection",
    #            "server_name": "",
    #            "address": url,
    #            "chatroom": chatroom,

    #            "ui__id": "servernew-prompt_register",
    #            "ui__prompt_options_register": [True,False],
    #            "register": True,

    #            "ui__button": {
    #                "id": "servernew-button_add",
    #                "value": "add"
    #                }
    #            }

    #    pytermgui.set_attribute_for_id('servernew-prompt_register','handler',lambda _,self: {
    #            setattr(self,'value',toggle_option(getattr(self,'__ui_options',self.real_value))),
    #            setattr(self,'real_value',self.value),
    #            print(self.parent)})

    #    pytermgui.set_attribute_for_id('servernew-button_add','handler',lambda _,self: { 
    #                set_chatroom(
    #                    add_new_server(
    #                        self.parent.dict_path,
    #                        register=pytermgui.get_object_by_id('servernew-prompt_register').real_value))})

    #    d = self.create_menu(source=[load_path,{'path': source}],corners=[[],[],[],"add"])
    #    globals()['CURRENT_FILE'] = source
    #    return d




# GLOBALS #
PATH = os.path.abspath(os.path.dirname(__file__))
import_json("settings")
import_json("usercfg")

LOGFILE = os.path.join(PATH,'log')
DELIMITERS = "!@#$%^&*()[]{}|\\;':\",.<>/? \t"

# menus for handle_menu_actions
MENUS = [
    #"menu_serverpicker",
    "menu_server_new",
    #"menu_serverregister",
    "menu_login_type",
    #"menu_login",
    "menu_settings",
    #"menu_picker"
]

KEEP_GOING = True

SESSION = requests.session()

INPUT = ""
INPUT_CURSOR = 0

VISUAL_START = 0
VISUAL_END = 0

PIPE_OUTPUT = None
PIPE_ARGS = {}
KEEP_PIPE = False

UI_TRACE = [[return_to_infield,{},'']]
CURRENT_FILE = None

# given by server
COOKIE = "flamingoestothestore"

# base data array to append to
URL = None
BASE_DATA = {
    "username": None,
    "cookie": None,
    "chatroom": None,
}



# TEMP MAIN
if __name__ == "__main__":
    ## clear screen
    print('\033[2J')

    if DO_DEBUG:
        open(LOGFILE,'w').close()
    dbg('starting teahaz at size',str(WIDTH),str(HEIGHT))
    pytermgui.set_debugger(dbg)

    if WIDTH < 37:
        w = Container(height=3)
        w.add_elements(Label(value=bold(color('Window width too low!','38;5;196')),justify='center'))
        w.add_elements(Label(value=italic(color('A minimum of 37 columns are required for teahaz.','38;5;244')),justify='left'))
        print(w)
        for _ in range(HEIGHT-w.height):
            print()
        sys.exit(1)


    ui = UIGenerator()


    # set pytermgui styles
    pytermgui.set_style(
            'container_title',
            lambda item: bold(color(item.upper(),THEME['title'])+':').replace('_',' ')
    )
    pytermgui.set_style(
            'container_error',
            lambda item: bold(color(item.upper(),THEME['error']))
    ),
    pytermgui.set_style(
            'container_success',
            lambda item: bold(color(item.upper(),THEME['success']))
    )
    pytermgui.set_style(
            'container_label',
            lambda item: (color(item.lower(),THEME['label']))
    )
    pytermgui.set_style(
            'container_value',
            lambda item: (color(item,THEME['value']))
    )
    pytermgui.set_style(
            'container_border',
            lambda item: (color(item,THEME['border']))
    )
    pytermgui.set_style(
            'prompt_highlight',
            lambda item: highlight(item,THEME['value'])
    )
    pytermgui.set_style(
            'tabbar_highlight',
            #lambda item: highlight(item,THEME['title'])
            lambda item: color(item,THEME['title'])
    )
    pytermgui.set_style(
            'container_border_chars',
            lambda: [bold(v) for v in THEME['border_chars']]
    )
    pytermgui.set_style(
            'prompt_delimiter_style',
            lambda: THEME['prompt_delimiters']
    )

    pytermgui.set_attribute_for_id('settings-themes_showcolors','handler',lambda prev,self: (prev.wipe(),ui.create_colormenu()))
    

    # set default mode
    infield = getch.InputField(pos=get_infield_pos())
    infield.line_offset = None
    infield.visual_color = lambda: '\033['+THEME['field_highlight']+'m'

    urls = list(SERVERS.keys())
    set_chatroom(urls[0],0)
    
    MODE_LABEL = Label('-- ESCAPE --',justify='left')
    MODE_LABEL.set_style('value',lambda item: color(item,THEME['mode_indicator']))
    x,y = get_infield_pos()
    MODE_LABEL.pos = [x,y+5]
    
    switch_mode("ESCAPE")

    if not 'SERVERS' in globals():
        SERVERS = {}
        CURRENT_CHATROOM = None
        handle_action('menu_login')

    # main input loop
    getch_loop()
