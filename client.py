# :main= python3 %

# IMPORTS
import os
import sys
import json
import time
import types
import getch
import base64
import pickle
import binascii
import requests
import importlib
import pytermgui
import threading
import pyperclip as clip
from fuzzywuzzy import fuzz as fw
from urllib.parse import urlparse
from pytermgui import WIDTH,HEIGHT
from pytermgui import clean_ansi,real_length,break_line
from pytermgui import Color,Regex
italic         =  Color.italic
bold           =  Color.bold
underline      =  Color.underline
strikethrough  =  Color.strikethrough
color          =  Color.color
highlight      =  Color.highlight
gradient       =  Color.gradient
get_gradient   =  Color.get_gradient
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
def import_json(name) -> None:
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

def import_path(path):
    module_name = os.path.basename(path).replace('-', '_')
    spec = importlib.util.spec_from_loader(
        module_name,
        importlib.machinery.SourceFileLoader(module_name, path)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module

## edit setting in json (needed because lambda cannot do assignments)
def edit_json(json_path,key,value) -> None:
    dbg(key)
    # get value if needed
    okey = key
    ovalue = value

    if isinstance(json_path,dict):
        data = json_path
    else:
        with open(os.path.join(PATH,json_path),'r') as f:
            data = json.load(f)

    if isinstance(key,str):
        keys = key.split('/')
        setting = keys[-1]
    else:
        keys = key
        setting = keys[-1]


    if len(keys) == 0:
        keys = [setting]

    # eval value if needed
    if callable(value):
        value = value()

    # find root of current part of dict
    if len(keys) == 1:
        one = keys[0]
        root = data

    elif len(keys) == 2:
        one,_ = keys
        root = data[one]

    elif len(keys) == 3:
        one,two,_ = keys
        root = data[one][two]

    elif len(keys) == 4:
        one,two,three,_ = keys
        root = data[one][two][three]
    
    # this shouldnt happen lol
    else:
        dbg('ERROR: invalid len(keys)',keys)
        #return

    # apply change
    #dbg(root,setting,value)
    root[setting] = value

    # write to file
    if isinstance(json_path,str):
        with open(os.path.join(PATH,json_path),'w') as f:
            f.write(json.dumps(data,indent=4))

    # reimport settings
    import_json('settings')
    infield.pos = get_infield_pos()

def load_path(path,key=None) -> dict:
    if isinstance(path,dict): return path

    with open(path,'r') as f:
        out = json.load(f)
        if key:
            out = out[key]
    return out

def handle_config() -> None:
    if not is_set("CONFIG"):
        return
    
    else:
        for key,value in vars(CONFIG).items():
            if not Regex.dunder.search(key):
                globals()[key] = value

## miscellaneous
### send args to logfile
def dbg(*args,do_color=True) -> None:
    if not DO_DEBUG:
        return

    if args == tuple():
        args = (get_caller(2),)

    s = ' '.join([str(a) for a in args])

    method    = sys._getframe().f_back.f_code.co_name
    obj       = sys._getframe().f_back.f_locals.get('self')
    filename  = sys._getframe().f_back.f_code.co_filename.split('/')[-1]
    lineno    = sys._getframe().f_back.f_lineno

    if do_color:
        filename = parse_color(THEME['title'],filename)
        lineno = parse_color(THEME['value'],lineno)

    _get_caller = lambda: type(obj).__name__+'.'+method if obj else method

    with open(LOGFILE,'a') as f:
        f.write(f"{bold(filename)}/{_get_caller()}:{bold(lineno)} : "+s+'\n')

def get_caller(depth=1):
    frame = sys._getframe()
    for _ in range(depth+1):
        frame = getattr(frame,'f_back')

    method    = frame.f_code.co_name
    obj       = frame.f_locals.get('self')
    lineno    = frame.f_lineno

    return type(obj).__name__+'.'+method if obj else method


### do `fun` after `ms` passes, nonblocking
def do_after(ms,fun,control='true',args={}) -> None:
    timed = lambda: (time.sleep(ms/1000),
                     fun(**args) if is_set(control) else 0)

    threading.Thread(target=timed).start()

### merge two dicts together, on conflict overwrite one's values
def merge(one,two) -> dict:
    merged = one.copy()
    for key in two.keys():
        for subkey,value in two[key].items():
            merged[key][subkey] = value
    return merged

### look up key in dict by value
def reverse_dict_lookup(d,value) -> [dict,None]:
    keys = list(d.keys())
    values = list(d.values())

    if value in values:
        index = values.index(value)
        return keys[index]
    else:
        return None


## variables
### check if variable is in scope
def is_set(var,scope=None) -> bool:
    if scope == None:
        scope = globals()
    return (var in scope and scope[var])

def toggle_option(options,current) -> any:
    current_index = options.index(current)
    return options[len(options)-1-current_index]

## switch to input mode, set globals
def switch_mode(target) -> None:
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
        MODE_LABEL.wipe()

    elif not KEEP_PIPE:
        MODE_LABEL.value = bold('-- '+target.upper()+' --')
        print(MODE_LABEL)

    VALID_KEYS = [v for k,v in BINDS[MODE].items() if not k.startswith('ui__')]

### add caller of ui element to ui trace
def add_to_trace(arr) -> None:
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
def set_pipe(fun,arg,keep=1) -> None:
    global PIPE_OUTPUT, KEEP_PIPE

    PIPE_OUTPUT = fun,arg
    if not keep == None:
        KEEP_PIPE = keep

### set current ui file, accepts file paths and dicts
def set_current_file(value) -> None:
    globals()['CURRENT_FILE'] = value

def add_new_colorscheme(name="new") -> dict:
    global SETTINGS

    def empty_dict(d) -> dict:
        for k,v in d.items():
            if k.startswith('ui__'):
                continue

            if isinstance(v,dict):
                d[k] = empty_dict(v)
            else:
                d[k] = type(k)()
        return d

    base = THEMES[list(THEMES.keys())[0]].copy()
    skeleton = empty_dict(base)

    #padder = SETTINGS['THEMES']['ui__padding']
    button = SETTINGS['THEMES']['ui__button']

    #del SETTINGS['THEMES']['ui__padding']
    del SETTINGS['THEMES']['ui__button']

    with open('settings.json','w') as f:
        f.write(json.dumps(SETTINGS,indent=4))
    import_json('settings')
    
    edit_json('settings.json',f"THEMES/{name}",skeleton)
    edit_json('settings.json',"THEMES/ui__button",button)

    themes = list(SETTINGS["ui__prompt_options__colorscheme"])
    edit_json('settings.json',"ui__prompt_options__colorscheme",themes+[name])

### return current index of object
def get_index(obj) -> int:
    return obj.selected_index

def ignore_input(*args):
    dbg('fixme')

# def handle_arguments():
    # if len(sys.argv) > 1:
        # args = sys.argv[1:]
        # if '--invite' in args and len(args) > args.index('--invite')+2:
            # handle_action('menu_login/register')
            # base = args.index('--invite')
            # url = args[base+1]
            # key = args[base+2]
# 
            # d = {
                # "username": input('username: '),
                # "email": input('email: '),
                # "password": input('password: '),
                # "nickname": input('nickname: ')
            # }
            # resp = requests.post(url=url+'/register/',json=d)
            # print(url+'/register/')
            # print('Register:',resp.text)
            # resp = requests.post(url=url+'/api/v0/invite/',json={'username': d.get('username'), 'inviteId': key})
            # print('Invite:',resp.text)
            # sys.exit()



## editing
### split `s` by delimiters defined in `DELIMITERS`, return array of words
def split_by_delimiters(s,return_indices=False) -> list:
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
        #if is_set('i',locals()):
        #    indices.append(i)
        return wordlist,indices
    else:
        return wordlist

### return True if the given `index` is part of the last word in the strong
def is_in_last_word(index,string,mode='delimiters') -> bool:
    if mode == 'delimiters':
        wordlist = split_by_delimiters(string)
    else:
        wordlist = string.split(' ')

    last_word_index = len(string)-len(wordlist[-1])
    return (last_word_index <= index)




# UI FUNCTIONS #

## get what position infield should be at
def get_infield_pos(update_modelabel=True) -> list:
    if 'infield' in globals().keys() and len(infield.value):
        offset = (len(infield.value)+1)//WIDTH

        if not infield.line_offset == offset and offset:
            infield.wipe()

            # print top bar
            if not CONV_HEADER.hidden:
                print(CONV_HEADER)

            if update_modelabel:
                MODE_LABEL.wipe(yoffset=1)
                print(MODE_LABEL)


        infield.line_offset = offset

    else:
        offset = 0

    x,y = 3,HEIGHT-2-offset
    return x,y

## return to normal input
def return_to_infield(*args,**kwargs) -> None:
    global PIPE_OUTPUT,KEEP_PIPE
    
    PIPE_OUTPUT = None
    KEEP_PIPE = False

    th.print_messages(reprint=True)
    infield.print()

def parse_color(_color,s,level=0) -> types.FunctionType:
    output = []
    if _color.isdigit():
        if level == 0:
            return color(s,_color)
        else:
            return _color

    elements = _color.split('+')

    # go through all +-d elements
    for e in elements:
        # handle simple color calls
        if e.isdigit():
            output.append(e)#color(s,e))
            continue
        
        # find inner start & end
        inner_start = e.find('(')
        if inner_start == -1:
            inner_start = real_length(e)
        inner_end = min(real_length(e)-e[::-1].find(')'),real_length(e))

        # check if outer is callable
        outer_s = e[:inner_start]
        if outer_s in globals().keys() and callable(globals()[outer_s]):
            outer = globals()[outer_s]
        else:
            output.append(outer_s)
            continue

        # get inner value recursively
        inner_stripped = e[inner_start:inner_end].strip('(').strip(')')
        inner = parse_color(inner_stripped,s,level+1)
        if inner == "":
            inner = s
        
        # get value to be added
        # dbg(outer.__name__+'('+str(inner)+')',do_color=0)
        # dbg('inner_stripped',inner_stripped,do_color=0)
        try:
            # dbg(f'{outer.__name__}({s},{inner})',do_color=0)
            out = outer(s,inner)
        except TypeError as e:
            # dbg(f'{outer.__name__}({inner})',do_color=0)
            out = outer(inner)

        # add value
        output.append(out)

    return ''.join(output)

def parse_emoji(text) -> str:
    found = Regex.emoji.findall(text)

    for s in found:
        new = EMOJI_KEYS.get(s)
        if new:
            text = text.replace(s,new)

    return text
    

def parse_inline_codes(s) -> str:
    # TODO: add support for multiple codes/str
    for i,(c,func) in enumerate(reversed(THEME['message_styles'].items())):
        indices = []
        doubles = []
        offset = 0
        current = s
        while 1:
            new = current.find(c)
            # # dbg(new)

            if new == -1:
                # # dbg('c','end',new,indices)
                break
            new += real_length(c)

            doubles.append(offset+new)
            if len(doubles) == 2:
                doubles[1] -= real_length(c)
                indices.append(doubles)
                doubles = []

            offset += new
            current = current[offset:]
            # dbg(current)

        if not len(indices):
            continue

        for start,end in indices:
            text = s[start:end]
            # dbg(func,text,start,end)
            s = s[:start-real_length(c)]+parse_color(func,text)+s[end+real_length(c):]
            # dbg(s)
        
        continue
    return s
 
# this is run at every single color call which is probably not good
def minimal_or_custom_highlight(item):
    if THEME['prompt_highlight'] == 'minimal':
        return "> "+parse_color('bold()',item)
    else:
        return parse_color(THEME['custom_prompt_highlight'],item)

        



# NETWORK FUNCTIONS #

# start threaded connection, TODO: this is the worst use of Thread humanity has ever witnessed.
# TODO TODO TODO
# also this should be under TeahazHelper
def start_connection(contype,menu=None,**kwargs) -> int:
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

    if isinstance(ret_val,list):
        ui.create_error_dialog(ret_val[0],'try again')
        return False

    elif not 200 <= ret_val.status_code < 300:
        ui.create_error_dialog(ret_val.text.strip(),'try again')
        return 0

    else:
        return ret_val
        
def login_or_register(contype,url,data) -> None:
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

    if url == "":
        ui.create_error_dialog('Invalid value "'+url+'" for url.','choose other server')
        return 0 

    resp = start_connection('post',contype,url=url+'/'+contype+'/',json=d,timeout=None)
    if not resp or not resp.status_code in range(200,299):
        dbg('bad response:',resp)
    else:
        text = "Successfully " + ("logged in" if contype == "login" else "registered")
        BASE_DATA['username'] = d.get('username')
        edit_json('usercfg.json',['SERVERS',url,'username'],d.get('username'))
         
        if contype == "register":
            dbg('logging in to new user')
            login_or_register("login",URL,data)
            return

        else:
            ui.wipe()
            ui.create_success_dialog(text) 




# INPUT #

## key intercepter loop, separate thread
def getch_loop() -> None: 
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
            # send key to inputfield to handle
            infield.send(key)

            x,y = infield.pos
            infield.pos = get_infield_pos()

            # print inputfield
            infield.print() 


## act on action
def handle_action(action) -> None:
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
        with open(SESSIONLOCATION,'wb') as f:
            pickle.dump(SESSION,f)

        sys.exit()

    elif action == "reprint":
        fun,args,obj = UI_TRACE[-1]
        pytermgui.clr()
        if not PIPE_OUTPUT:
            th.print_messages(reprint=True)

        fun(**args)
        return

    elif action == "toggle_header":
        CONV_HEADER.hidden = not CONV_HEADER.hidden

        if CONV_HEADER.hidden:
            handle_action('reprint')
        else:
            print(CONV_HEADER)

    elif action == "invisible_ping":
        data = BASE_DATA.copy()
        data['message'] = '@ this cannot be decoded @'
        data['type'] = 'text'
        dbg('ping_resp:',SESSION.post(url=URL+'/api/v0/message/',json=data).text)

    # message binds
    elif action == "message_send":
        msg = infield.value
        if msg == '':
            return

        if is_set('hook__message_send'):
            msg = hook__message_send(msg)

        th.send(msg,'message')
        infield.clear_value()

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

    elif action == "scroll_reset":
        th.offset = 0
        th.print_messages(reprint=True)
        switch_mode('ESCAPE')




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

        elif "scroll_up" in action:
            th.offset += 1
            th.print_messages(reprint=True)

        elif "scroll_down" in action:
            th.offset -= 1
            th.print_messages(reprint=True)

        elif "conv_start" in action:
            th.offset = len(MESSAGES)-25
            th.print_messages(reprint=True)

        elif "conv_end" in action:
            th.offset = 0
            th.print_messages(reprint=True)

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
            if not len(indices):
                return

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
            get_infield_pos()
            completer.reset('')

            infield.set_value('')

        elif action == "select_line":
            VISUAL_START = 0
            VISUAL_END = len(infield.value)

            infield.visual(VISUAL_START,VISUAL_END)
            switch_mode("VISUAL")


    
    ## PIPES
    ### action_in actions
    elif action.endswith("_in"):
        set_pipe(do_in,{'action': action},keep=0)
    
    ### find & till
    elif action == "find":
        set_pipe(find,{},keep=0)

    elif action == "find_reverse":
        set_pipe(find,{'reverse': True},keep=0)
    
    elif action == "till":
        set_pipe(find,{'offset': -1},keep=0)

    elif action == "till_reverse":
        set_pipe(find,{'offset': -1, 'reverse': True},keep=0)

    elif "replace" in action:
        if len(infield.value):
            set_pipe(replace,{'action': action},keep=0)


## handle action but for menus
def handle_menu(key,obj,attributes={},page=0) -> None:
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
            #dbg(obj.__ui_keys+[obj.setting])
            edit_json(json_path=CURRENT_FILE,key=obj.__ui_keys,value=new)

            # edit previous ui to show changes
            fun,kwargs,newobj = UI_TRACE[-2]
            s = kwargs.get('source')
            if s and not isinstance(s,list):
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

        # add to depth
        obj.__ui_keys.append(selected.real_label)

        # create menu
        d = ui.create_submenu(selected)

        # select current option if possible
        if hasattr(d,'options') and d.options:
            d.selected_index = [o for o in d.options].index(selected.real_value)
            d.select()

        # add path to all new objects
        newobjects = PIPE_OUTPUT[1]['obj']
        if isinstance(newobjects,list):
            for new in newobjects:
                new.__ui_keys = obj.__ui_keys

        # print
        d.select()
        print(d)
        return
    
    elif key == " ":
        selected,_,index = obj.selected
        if selected.__ui_options and len(selected.__ui_options) == 2:
            #if not globals().get(selected.real_label) == None:
            # add to depth
            selected.__ui_keys.append(selected.real_label)

            edit_json(
                    json_path=CURRENT_FILE,
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
def handle_menu_actions(action,current_file=None) -> int: 
    ui.wipe()
    if PIPE_OUTPUT == None:
        pytermgui.clr()

    menu = action.replace('menu_','')
    corners = [v for k,v in THEME['corners'].items()]
    attrs = {}

    if menu == "settings":
        corners[3] = "settings"
        source = os.path.join(PATH,'settings.json')
        pytermgui.set_attribute_for_id('settings-themes_showcolors','handler',
                lambda prev,self: (prev.wipe(),ui.create_colormenu()))

        pytermgui.set_attribute_for_id('colorschemes-button_add','handler',
                lambda prev,self: (add_new_colorscheme('test'),handle_action('reprint')))
    
    elif menu == "login/register":
        pytermgui.set_attribute_for_id('login_type-prompt','handler',lambda prev,self: {
                prev.wipe(), handle_action("menu_"+self.submit())})

        source = {
            "ui__title": "choose login type",
            "ui__padding": 0,
            "ui__id": "login_type-prompt",
            "ui__prompt": ["login","register"]
        }

    elif menu in ["login","register"]:
        address,chatindex = CURRENT_CHATROOM
        chatid = SERVERS[address]['chatrooms'][chatindex]

        name = chatid+' @ '+address
        corners[3] = menu
        pytermgui.set_attribute_for_id(menu+'-button_submit','address',address)
        pytermgui.set_attribute_for_id(menu+'-button_submit','handler',
                lambda prev,self: login_or_register(menu,self.address,self.parent.dict_path))

        if current_file == None:
            if menu == 'login':
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
        
        attrs["address"] = URL

    elif menu == "server_picker":
        ui.create_server_picker()
        return

    elif menu == "server_new":
        pytermgui.set_attribute_for_id('server_new-button_add','handler',
                lambda prev,self: {
                    prev.wipe(),
                    handle_menu('ESC',self.parent) if not th.add_new_server(prev.dict_path) else None})

        source = {
                "ui__title": "Add new connection",
                "ui__padding0": 0,
                "ui__id": "server_new-prompt_address",
                "address": "",
                "chatroom": "",
                "ui__padding1": 1,
                "ui__button": {
                    "id": "server_new-button_add",
                    "value": "add!"
                }
            }

    elif menu == "address_picker":
        ui.create_address_picker()
        return

    elif menu == "picker":
        ui.create_menu_picker()
        return
 
    else:
        return 1

    #globals()['CURRENT_FILE'] = path
    set_current_file(source)

    # call menu handler
    d = ui.create_menu(source=[load_path,{'path': source}])

    for key,value in attrs.items():
        if key == "id":
            pytermgui.set_element_id(d,value)
        else:
            setattr(d,key,value)

    return 0





# ACTION HANDLER FUNCTIONS #

## do `action` in infield.value, using get_indices for start/end
def do_in(param, action) -> None:
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
def get_indices(param) -> tuple:
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
def find(key,offset=0,reverse=False) -> None:
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
    
def replace(key,action) -> None:
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

class TeahazHelper:
    def __init__(self):
        self.prev_get = None

        self.offset   = 0
        
        # TODO
        self.extras   = []
        

    def remove_sent_message(self,clientid):
        for m in self.extras:
            if m.get('clientid') == clientid:
                dbg('removed')
                self.extras.remove(m)
        
    def handle_operation(self,method,output,callback=None,callback_args={},*args,**kwargs):
        def _do_operation(*args,**kwargs):
            if method == "post":
                fun = SESSION.post
            elif method == "get":
                fun = SESSION.get
 
            try:
                setattr(self,output,fun(**kwargs))
            except Exception as e:
                dbg(e)

            if callback:
                callback(**callback_args)

        setattr(self,output,'incomplete')
        self.operation_thread = threading.Thread(target=_do_operation,args=args,kwargs=kwargs)
        self.operation_thread.start()

    def is_connected(self,url):
        for cookie in SESSION.cookies:
            if cookie.domain == urlparse(url).netloc.split(':')[0]:
                return True
        else:
            return False

    def set_chatroom(self,url,index):
        dbg('called')
        global BASE_DATA,CONV_HEADER,URL
            
        # return if certain values are passed
        if index == 'invalid' or index == 'register':
            return

        # set og data to restore in case of problems
        ogdata = BASE_DATA.copy()
        ogurl = URL

        # set global values
        globals()['URL'] = url
        globals()['CURRENT_CHATROOM'] = url,index

        # update header
        chatrooms = SERVERS[url]['chatrooms']
        if is_set('CONV_HEADER'):
            ogvalue = CONV_HEADER_LABEL.value
            CONV_HEADER_LABEL.value = f'{url}: {chatrooms[index]}'

        # set BASE_DATA
        BASE_DATA['username'] = SERVERS[url]['username']
        BASE_DATA['chatroom'] = chatrooms[index]
        
        # update json
        edit_json('usercfg.json','CURRENT_CHATROOM',[url,index])

        # get login or register 
        if not th.is_connected(url):
            handle_action('menu_login/register')
            return "login"

        # set new globals
        else:
            # test if server works
            error = False
            ret = th.get(0,'message')

            # try to convert ret into json
            try:
                m = json.loads(ret)

                # type needs to be list
                if not isinstance(m,list):
                    error = True

            except ValueError:
                error = True

            if error:
                # create error box
                ui.create_error_dialog('Error while switching servers: '+ret,'try again')
                dbg(ret)

                # restore values
                BASE_DATA = ogdata
                URL = ogurl
                if is_set('ogvalue',locals()):
                    CONV_HEADER_LABEL.value = ogvalue

                # return non-0
                return ret


        dbg('chatroom set to',url,'/',chatrooms[index])

    def add_new_server(self,values):
        d = {}
        for key,value in values.items():
            if not key.startswith('ui__'):
                d[key] = value

        address = values.get('address')
        globals()['URL'] = address

        chatroom = values.get('chatroom')
        if SERVERS.get(address):
            SERVERS[address]['chatrooms'].append(chatroom)
        else:
            SERVERS[address] = {}
            SERVERS[address]['username'] = None
            SERVERS[address]['chatrooms'] = [chatroom]

        edit_json('usercfg.json','SERVERS',SERVERS)
        import_json('usercfg')

        self.set_chatroom(address,len(SERVERS[address]['chatrooms'])-1)
        if not th.is_connected(address):
            handle_action('menu_login/register')
            return 'not connected'
        else:
            handle_menu('ESC',UI_TRACE[-1][2])


        return address,SERVERS[address]['chatrooms'].index(chatroom)

    def get(self,parameter,mode="message"):
        data = BASE_DATA
        
        # set endpoint
        endpoint = "/"+mode+"/"

        # set parameter based on mode
        if mode == "message":
            data["time"] = str(parameter)
        elif mode == "file":
            data["filename"] = str(parameter)
        else:
            return "Client Error: Invalid get mode '"+str(mode)+"'"

        # return response
        # dbg('sending',URL+'/api/v0'+endpoint,BASE_DATA) 
        response = SESSION.get(url=URL+'/api/v0'+endpoint,headers=BASE_DATA)
        return response.text

    ## sending method
    def send(self,message,endpoint='message'):
        data = BASE_DATA

        # handle specificities
        if endpoint == 'message':
            # set text-specific fields
            data["message"] = encode(message)
            data['type'] = "text"

        elif endpoint == 'file':
            # get file contents
            with open(message, 'rb') as infile:
                contents = encode_binary(infile.read())

            # get file extension bc mimetype sucks sometimes
            extension = message.split(".")[-1]

            # set file-specific fields
            data['type'] = "file"
            data['extension'] = extension
            data['data'] = contents

        else:
            return "Client Error: Invalid message type '"+str(endpoint)+"'"
        
        endpoint = f'/{endpoint}/'

        temp = MESSAGE_TEMPLATE.copy()

        clientid = time.time()#+random.randint(0,9999)

        temp['time'] = time.time()
        temp['clientid'] = clientid
        temp['username'] = BASE_DATA.get('username')
        temp['nickname'] = temp['username']
        temp['message'] = message
        
        # TODO: extras should be printed until they deliver
        self.handle_operation(
                method        = 'post',
                output        = 'message_send_return',
                url           = URL+'/api/v0'+endpoint,
                # callback      = self.remove_sent_message,
                # callback_args = {'clientid': clientid},
                json     = data
        )

        infield.clear_value()
        self.print_messages(extras=[temp])

    def print_messages(self,messages=[],extras=[],reprint=False,dont_ignore=False,do_print=True):
        # get positions
        leftx = infield.pos[0]

        # print same messages
        if reprint:
            messagelist = MESSAGES.copy()

        # add given messages to global and print all
        elif len(messages):
            messagelist = messages.copy()+self.extras.copy()

        # only print extra messages
        elif len(extras):
            messagelist = MESSAGES.copy()+self.extras.copy()+extras.copy()
            # self.extras += extras

        # return if there's nothing to print
        else:
            return 

        # messages are printed in reverse order
        messagelist.reverse()

        # get starting y coord
        starty = infield.pos[1]-2
        if completer._has_printed:
            starty -= len(completer.rows)
        y = starty

        # normalize offset
        self.offset = max(self.offset,0)
        y += self.offset


        buff = ''
        for i,m in enumerate(messagelist):
            # TODO: messages not matching offset should be ignored too
            if not dont_ignore and y < 0:
                continue

            # set up values
            username     = m.get('username')
            nickname     = m.get('nickname')
            m_time       = m.get('time')
            current_time = int(m_time)
            sendtime     = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(m_time))
            content      = m.get('message')


            # handle message content
            if content:
                if m in extras or m in self.extras:
                    decoded = content
                else:
                    try:
                        decoded = decode(content)
                    except:
                        continue

                emojid = parse_emoji(decoded)
                inline = parse_inline_codes(emojid)
                content = emojid
                if inline == decoded:
                    do_subdivision = True
                else:
                    content = inline
                    do_subdivision = False

                lines = pytermgui.break_line(content,MAX_MESSAGE_WIDTH(),do_subdivision=do_subdivision)
                if FADE_SENDING:
                    if m in extras:
                        for j,l in enumerate(lines):
                            lines[j] = parse_color(THEME['fade'],l)
            else:
                content = '< '+m.get('filename')+' >'


            # test if the current message is the start of a chunk
            chunk_start = True
            if len(messagelist) > i+1 and not i == len(messagelist)-1:
                prev_msg = messagelist[i+1]
            else:
                prev_msg = None

            if prev_msg:
                prev_time = int(prev_msg.get('time'))

                if prev_msg.get('username') == username:
                    if current_time-prev_time < int(MESSAGE_SEPARATE_TIME):
                        chunk_start = False         


            # test if current message is the end of a chunk 
            chunk_end = True
            if 0 <= i-1:
                next_msg = messagelist[i-1]
            else:
                next_msg = None

            if next_msg:
                next_time = int(next_msg.get('time'))
                if next_msg.get('username') == username:
                    if next_time-current_time < int(MESSAGE_SEPARATE_TIME):
                        chunk_end = False
 
            
            # add extra elements as needed
            if chunk_start:
                # TODO: this color will eventually be given by the server
                lines.insert(0,parse_color(THEME['title'],nickname))

            if chunk_end:
                lines.append(parse_color(THEME['fade'],sendtime))
                lines.append('')

            
            # print lines:
            for i,l in enumerate(reversed(lines)):
                if dont_ignore or 0 < y <= starty:
                    # set cursor location
                    if username == BASE_DATA.get('username'):
                        buff += f'\033[{y};{WIDTH-real_length(l)}H'
                    else:
                        buff += f'\033[{y};{leftx}H'
                    buff += l

                    y -= 1
            y -= 1

        if not do_print:
            return

        # clear affected rows
        endpoint = (HEIGHT if self.offset else starty+(len(completer.rows) if completer._has_printed else 0))
        for cleany in range(0,endpoint+1):
            buff = f'\033[{cleany};H'+'\033[K' + buff
        sys.stdout.write(buff)


        # print mode label
        if MODE != 'ESCAPE':
            print(MODE_LABEL)
            
        # print top bar
        if not CONV_HEADER.hidden and not self.offset:
            print(CONV_HEADER)

        # print completer
        if completer._has_printed:
            print(completer)

    def get_loop(self):
        global WIDTH,HEIGHT,MESSAGES

        while KEEP_GOING:
            if not PIPE_OUTPUT:
                WIDTH,HEIGHT = os.get_terminal_size()

                if not is_set('messages_get_return',self.__dict__):
                    get_time = SESSION.last_get
                    SESSION.last_get = time.time()
                    data = BASE_DATA
                    data['time'] = str(get_time)
                    self.handle_operation(method='get',output='messages_get_return',url=URL+'/api/v0/message/',headers=data)

                elif not self.messages_get_return == 'incomplete':
                    if self.messages_get_return == self.prev_get:
                        continue

                    try:
                        messages = json.loads(self.messages_get_return.text)
                    except ValueError as e:
                        dbg('can\'t convert messages: '+str(e))
                        continue

                    self.prev_get = self.messages_get_return
                    self.messages_get_return = None
                    if not messages == []:
                        if is_set('hook__message_get'):
                            same_user = messages[-1].get('username') == BASE_DATA.get('username')
                            threading.Thread(target=hook__message_get,args=(messages,same_user)).start()

                        MESSAGES += messages
                        self.print_messages(MESSAGES)

            time.sleep(1)

class UIGenerator:
    """
    Object used for organizing UI generator functions
    into one place. May also have some values stored
    in the future.

    *Almost* all calls to this object are done from
    handle_menu_actions.
    """

    # wipe most recent ui element
    def wipe(self):
        obj = UI_TRACE[-1][2]
        if hasattr(obj,'wipe'):
            obj.wipe()

    # create menu from a dictionary source
    def create_menu(self,source,corners=[None]*4,width=None,index=None,dict_index=0,**container_args):
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

            # set theme corners
            for i,c in enumerate([v for k,v in THEME['corners'].items()]):
                if not c == None:
                    o.set_corner(i,c)
            
            # set overwrite corners
            for i,c in enumerate(corners):
                if c:
                    o.set_corner(i,c)

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
            if isinstance(source.__dict__.get('__ui_options'),list):
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
        if not fun == ignore_input:
            set_pipe(handle_menu,{'obj': dicts, 'page': dict_index})
        if index == None:
            add_to_trace([{'source': source, 'index': index, 'dict_index': dict_index}, d])

        return d
 

            
    # create menu picker menu, likely only for dbg
    def create_menu_picker(self):
        d = Container(width=50)

        title = Label(value="pick your menu",justify='center',padding=0)
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

    def create_server_picker(self):
        # create container
        d = Container(width=50)

        # set container corners
        for i,c in enumerate([v for k,v in THEME['corners'].items()]):
            if not c == None:
                d.set_corner(i,c)

        # create, add title
        title = Label('choose chatroom',justify='center')
        title.set_style('value',pytermgui.CONTAINER_TITLE_STYLE)
        d.add_elements([title,Label()])

        # go through servers
        for url_long,data in SERVERS.items():
            # convert url to a nicer form
            url = urlparse(url_long).netloc
            if url == "":
                url = url_long
            url_col = color(url,THEME['value'])

            # go through chatrooms
            for chatroom in data['chatrooms']:
                chat_col = color(chatroom,THEME['title'])

                # create, add prompt
                p = Prompt(options=[chat_col+'@'+url_col],justify_options='center')
                p.url = url_long
                p.chatroom = chatroom

                p.handler = lambda prev,self: {
                        handle_menu('ESC',prev)
                        if not th.set_chatroom(self.url,SERVERS[self.url]['chatrooms'].index(self.chatroom)) else None}

                d.add_elements(p)

        # create, add button
        button = Prompt(options=['add new'])
        button.set_style('value',pytermgui.CONTAINER_VALUE_STYLE)
        pytermgui.set_element_id(button,'server_picker-button_add')

        pytermgui.set_attribute_for_id(button.id,'handler',lambda prev,self: {
            prev.wipe(),
            handle_action('menu_server_new')})

        d.add_elements([Label(),button])


        set_pipe(handle_menu,{'obj': [d]})
        add_to_trace([{},d])

        d.center()
        d.select()
        print(d)

        return d

    # TODO: make button work here
    def create_address_picker(self,caller_prompt):
        f = caller_prompt.parent.dict_path 

        d = Container(width=50)

        # set container corners
        for i,c in enumerate([v for k,v in THEME['corners'].items()]):
            if not c == None:
                d.set_corner(i,c)

        title = Label(value="choose or add address",justify="center")
        padding = Label()
        d.add_elements([title,padding])

        for url in SERVERS.keys():
            p = Prompt(options=[url],justify_options="center")
            p.file = f
            p.handler = lambda _,self: {
                    edit_json(self.file,'address',self.real_value),handle_menu('ESC',self.parent)}

            d.add_elements(p)

        #button = Prompt(options=['add new'],justify_options="center")
        #button.__ui_options = []
        #button.real_label = 'new address'
        #dbg(button.__ui_options),
        #button.__ui_keys = ['address']
        #button.handler = lambda _,self: {
        #        ui.wipe(),
        #        setattr(ui.create_submenu(self),'submit',[])}
                    

        d.add_elements([padding,button])

        # set styles
        d.set_style(Prompt,'value',pytermgui.CONTAINER_VALUE_STYLE)
        d.set_style(Label,'value',pytermgui.CONTAINER_TITLE_STYLE)
        padding.set_style('value',lambda item: item)
    
            
        set_pipe(handle_menu,{'obj': [d]})
        add_to_trace([{'caller_prompt': caller_prompt},d])

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

        if handler == None:
            handler = lambda _,self: handle_menu("ESC",self.parent)

        pytermgui.set_attribute_for_id('error-button_'+button,'handler',handler)

        d = self.create_menu(source)
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

        pytermgui.set_attribute_for_id('success-button_'+button,'handler',
                lambda prev,self: { handle_menu('ESC',prev), handle_menu('ESC',UI_TRACE[-1][2])})
        d = self.create_menu(source,width=25)
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

    def create_completer_tester(self):
        print('\033[2J')

        field = InputField()
        completer = InputFieldCompleter()

class ModeLabel(Label):
    """
    Simple Label extension providing a wipe()
    method and a position system
    """
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        x,y = get_infield_pos(update_modelabel=0)
        self.pos = [x-1,y+1]
        #x,y = get_infield_pos(update_modelabel=0)

    def __repr__(self):
        x,y = self.pos

        return f"\033[{y};{x}H"+super().__repr__()
    
    def wipe(self,yoffset=0):
        if self.pos:
            x,y = self.pos
            print(f"\033[{y+yoffset};{x}H"+real_length(super().__repr__())*' ')

class InputFieldCompleter(Container):
    def __init__(self,options,icon_callback=None,completion_callback=None,field=None,height=5,trigger=None,**kwargs):
        super().__init__(**kwargs)
        self._is_selectable = False

        # set up base variables
        self.rows = []
        self.options = options
        self.trigger = trigger
        
        # get or create field, set position
        if field:
            self.field = field
        else:
            self.field = InputDialogField()
        self.target_pos = self.field.pos

        # create rows
        for i in range(height):
            p = Prompt(label='',justify_options="left")
            self.add_elements(p)
            self.rows.append(p)
        
        # store and overwrite field functions
        self.field.og_send = self.field.send
        self.field.og_set_value = self.field.set_value
        self.field.send = self.field_send

        # set style stuff
        self.set_borders([''*4])

        if callable(self.options):
            options = self.options()
        else:
            options = self.options

        # self.width = max(len(l)+5 for l in options.keys())
        self.match_highlight_style = lambda char: bold(underline(char))
        self.set_style(Prompt,'highlight',lambda item: bold('> ')+item)


        # set callbacks
        self.completion_callback = completion_callback
        self.icon_callback = icon_callback


        # set flags
        self._has_printed = False
        self._has_padded_messages = False
        self._is_enabled = lambda: True
        self._show_icons = lambda: False


    # complete `word` into field.value[start:end]
    def do_completion(self,word,start,end):
        # set up sides of string
        left = self.field.value[:start]
        right = self.field.value[end:]
        current = self.field.value[start:end]

        # set field variables
        # this doesn't use the standard .set_value method as it would recurse
        self.field.value = left+word+right
        self.field.cursor = end + real_length(word)-real_length(current)-1

        # adjust cursor by trigger length
        if self.trigger:
            self.field.cursor += real_length(self.trigger)
        self.wipe()

    
    def reset(self,key,**kwargs):
        self.field.og_send(key,**kwargs)

        if self._has_printed:
            self.wipe()
            self._has_printed = False
            th.print_messages(reprint=True) 

    def wipe(self,*args,**kwargs):
        x = self.pos[0] + 1
        y = self.pos[1] + 2
        buff = ''
        for i,row in enumerate(self.rows):
            if row.label:
                buff += f'\033[{y+i};{x}H'+'\033[K'

        print(buff)



    # intercept field.send
    def field_send(self,key,**kwargs):
        if not self._is_enabled():
            self.field.og_send(key,**kwargs)
            return

        word_start,word_end = get_indices('w')

        # make sure it doesnt include the triggerlength
        word_start -= real_length(self.trigger)
        word_end   += real_length(self.trigger)

        # get word
        word = self.field.value[word_start:word_end]

        # get if trigger is opening or closing
        opener = False
        for c in self.field.value[:self.field.cursor]:
            if c == self.trigger:
                opener = not opener

        # return if any conditions are met
        current_length = real_length(self.field.value)
        if not opener \
            or not current_length \
            or current_length == 1 and key == "BACKSPACE":

            self.reset(key,**kwargs)
            return
                
        if not self.handle_bindings(key) == "handled":
            # complete
            if key == "TAB":
                selected = self.selectables[self.selected_index][0]
                newword = selected.real_label
                self.do_completion(newword,word_start,word_end)
                self.reset('',**kwargs)
                return

            # go up
            elif key in ["ARROW_UP","CTRL_P"]:
                self.selected_index = max(0,self.selected_index-1)
                key = ''

            # go down
            elif key in ["ARROW_DOWN","CTRL_N"]:
                self.selected_index = min(len(self.selectables),self.selected_index+1)
                key = ''


        # update things
        self.field.og_send(key,**kwargs)
        self.eval_options(word_start,word_end+len(key))
        self.select()

        print(self)
        self._has_printed = True


    # get viable options
    def eval_options(self,start,end):
        ratios = []
        target = self.field.value[start:end]
        if callable(self.options):
            options = self.options()
        else:
            options = self.options

        for e in options:
            ratio = fw.ratio(target,e)
            if ratio > 30:
                ratios.append([e,ratio])

        # sort options
        ratios.sort(reverse=True,key=lambda e: e[1])
        output = [e for e,_ in ratios]

        # assign options to labels in rows
        for i,row in enumerate(reversed(self.rows)):
            if len(output) > i:
                # get icon character
                value = output[i]
                if self.icon_callback and self._show_icons():
                    icon = self.icon_callback(value)+' '
                else:
                    icon = ''

                
                # highlight matching characters
                buff = list(target)
                value_list = list(value)
                for j,c in enumerate(value):
                    if c == self.trigger:
                        continue

                    if c in buff:
                        value_list[j] = self.match_highlight_style(c)
                        buff.remove(c)

                value = ''.join(value_list)

                row.real_label = output[i]
                row.label = icon+value

                if not row in self.elements:
                    self.add_elements(row)
            else:
                row.label = ''
                if row in self.elements:
                    self.elements.remove(row)

        # update width
        self.width = max(self.width,max([real_length(e.label) for e in self.rows]))

        # update position
        x,y = self.target_pos
        x -= 3
        y -= len(self.elements)+2
        if not [x,y] == self.pos:
            self.move([x,y])

        if not self._has_printed:
            self.selected_index = len(self.elements)-1
            
    def handle_bindings(self,key):
        return
    
    # ignore long elements
    def _handle_long_element(self,e):
        return

class FileManager(Container):
    """
    Container derivative that would show and let users interact
    with files.

    - main methods (other than Container's):
        * cd : change directory
        * search(term) : search for `term` in files
        * open(opt: index) : open selected file with the global 
                             filetype handlers
        * execute(cmd,*maybe regex to match files*) : execute given command
                             in bash on the file
    """
    def __init__(self,path=None,completer=None,filetype_highlight=True,**kwargs):
        super().__init__(**kwargs)
        if path:
            if os.path.exists(path):
                self.path = path

        if not hasattr(self,'path'):
            self.path = PATH

        if completer:
            self.completer = completer
        else:
            self.completer = InputFieldCompleter(height=8,options=lambda: os.listdir(self.path))

        self.height = 13
        self.width = 40
        self.add_elements([self.completer])







# GLOBALS #
PATH = os.path.abspath(os.path.dirname(__file__))
HOME = os.path.expanduser('~')

LOGFILE = os.path.join(PATH,'log')
# TODO: support windows
CONFIG_DIR = os.path.join(HOME,'.config/teahaz')
CONFIG_FILE = os.path.join(CONFIG_DIR,'thconf.py')

if os.path.exists(os.path.join(PATH,'settings.json')):
    import_json("settings")

if os.path.exists(os.path.join(PATH,'usercfg.json')):
    import_json("usercfg")
else:
    with open(os.path.join(PATH,'usercfg.json'),'w') as f:
        f.write('{}')


import_json('emoji')

DELIMITERS = "!@#$%^&*()[]{}|\\;':\",.<>/? \t"
MAX_MESSAGE_WIDTH = lambda: int(WIDTH*4/10)


# menus for handle_menu_actions
MENUS = [
    "menu_server_picker",
    # "menu_address_picker",
    "menu_server_new",
    # "menu_serverregister",
    "menu_login/register",
    # "menu_login",
    # "menu_settings",
    # "menu_picker"
]

KEEP_GOING = True

INPUT = ""
INPUT_CURSOR = 0

VISUAL_START = 0
VISUAL_END = 0

PIPE_OUTPUT = None
PIPE_ARGS = {}
KEEP_PIPE = False
PREV_GET = None

UI_TRACE = [[return_to_infield,{},'']]
CURRENT_FILE = None

SENDING = []
MESSAGES = []
PREV_MESSAGE = None
PREV_MESSAGES = []
MESSAGE_TEMPLATE = {
    "time": 0,
    "username": "",
    "nickname": "",
    "chatroom": "",
    "type": "text",
    "message": "",
    "filename": None,
    "extension": None
}

# base data array to append to
URL = None
BASE_DATA = {
    "username": None,
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

    if os.path.exists(CONFIG_FILE):
        CONFIG = import_path(CONFIG_FILE)
    else:
        if not os.path.exists(CONFIG_DIR):
            try:
                dbg(f'couldn\'t create config directory "{CONFIG_FILE}": {e}')
            except Exception as e:
                os.makedirs(CONFIG_DIR)
    handle_config()


    if WIDTH < 37:
        w = Container(height=3)
        w.add_elements(Label(value=bold(color('Window width too low!','38;5;196')),justify='center'))
        w.add_elements(Label(value=italic(color('A minimum of 37 columns are required for teahaz.','38;5;244')),justify='left'))
        print(w)
        for _ in range(HEIGHT-w.height):
            print()
        sys.exit(1)


    # load session.obj
    SESSIONLOCATION = os.path.join(PATH,'session.obj')
    if os.path.exists(SESSIONLOCATION):
        with open(SESSIONLOCATION,'rb') as f:
            SESSION = pickle.load(f)
            if not hasattr(SESSION,'last_get'):
                SESSION.last_get = 0
    else:
        SESSION = requests.session()
        SESSION.last_get = 0


    ## set pytermgui styles
    pytermgui.set_style('container_title',lambda item: parse_color(THEME['title'],item).replace('_',' '))
    pytermgui.set_style('container_error',lambda item: parse_color(THEME['error'],item.upper())),
    pytermgui.set_style('container_success',lambda item: parse_color(THEME['success'],item.upper()))
    pytermgui.set_style('container_label',lambda item: parse_color(THEME['label'],item.lower()))
    pytermgui.set_style('container_value',lambda item: parse_color(THEME['value'],item))
    pytermgui.set_style('container_border',lambda item: parse_color(THEME['border'],item))
    pytermgui.set_style('container_corner',pytermgui.CONTAINER_BORDER_STYLE)

    
    pytermgui.set_style('prompt_highlight',lambda item: minimal_or_custom_highlight(item))
    pytermgui.set_style('tabbar_highlight',lambda item: parse_color(THEME['title'],item))

    pytermgui.set_style('container_border_chars',lambda: [bold(v) for v in THEME['border_chars']])
    pytermgui.set_style('prompt_delimiter_style',lambda: THEME['prompt_delimiters'])
 

    # set default mode
    infield = InputDialogField(pos=get_infield_pos())
    infield.line_offset = None
    infield.visual_color = lambda text: parse_color(THEME['field_highlight'],text)

    completer = InputFieldCompleter(options=EMOJI_KEYS,field=infield,trigger=':',icon_callback=parse_emoji)
    completer._is_enabled = lambda: COMPLETER_ENABLED
    completer._show_icons = lambda: COMPLETER_ICONS

    ui = UIGenerator()
    th = TeahazHelper()

    # set up defaults
    if is_set('CURRENT_CHATROOM'):
        url,chatroom = CURRENT_CHATROOM
        th.set_chatroom(url,chatroom)
    else:
        SERVERS = {}
        CURRENT_CHATROOM = None
        handle_action('menu_server_new')
    
    # set up bottom mode label
    MODE_LABEL = ModeLabel(value='-- ESCAPE --',justify='left')
    MODE_LABEL.set_style('value',lambda item: color(item,THEME['mode_indicator']))

    # set up top bar to indicate current conv
    CONV_HEADER = Container(width=int(WIDTH*0.75),dynamic_size=False)
    for i,c in enumerate([v for k,v in THEME['corners'].items()]):
        if not c == None:
            CONV_HEADER.set_corner(i,c)

    # wipe all lines fully before repr
    CONV_HEADER.center(axes='x')
    CONV_HEADER._repr_pre = CONV_HEADER.wipe_all_containing
    CONV_HEADER_LABEL = Label(justify='center')
    CONV_HEADER_LABEL.set_style('value',pytermgui.CONTAINER_VALUE_STYLE)
    if CURRENT_CHATROOM:
        url,index = CURRENT_CHATROOM
        value = f"{url}: {SERVERS[url]['chatrooms'][index]}"
    else:
        value = ''
        SESSION = requests.session()

    # set header values
    CONV_HEADER_LABEL.value = value
    CONV_HEADER.add_elements(CONV_HEADER_LABEL)
    CONV_HEADER.hidden = False
    
    # set up starting mode
    switch_mode("ESCAPE")

    # start get loop
    get_loop = threading.Thread(target=th.get_loop,name='get_loop')
    get_loop.start()

    # main input loop
    getch_loop()        
