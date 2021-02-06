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
def import_settings():
    global SETTINGS,THEME

    with open(os.path.join(PATH,'settings.json'),'r') as f:
        SETTINGS = json.load(f)
        for key,item in SETTINGS.items():
            globals()[key] = item

    if is_set('MODE'):
        switch_mode(MODE)

    current_colorscheme = SETTINGS['SELECTED_THEME']
    THEME = SETTINGS['THEMES'][current_colorscheme]

## edit setting in json (needed because lambda cannot do assignments)
def edit_json(key,value,json_path,keys=[]):
    # get value if needed
    okey = key
    ovalue = value

    with open(os.path.join(PATH,json_path),'r') as f:
        data = json.load(f)

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
        dbg(keys)

    # apply change
    root[setting] = value

    # write to file
    with open(os.path.join(PATH,json_path),'w') as f:
        f.write(json.dumps(data,indent=4))

    # reimport settings
    import_settings()
    infield.pos = get_infield_pos()

def load_path(path,key=None):
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

    caller = sys._getframe().f_back.f_code.co_name
    filename = sys._getframe().f_back.f_code.co_filename.split('/')[-1]
    lineno = sys._getframe().f_back.f_lineno

    with open(LOGFILE,'a') as f:
        f.write(f"{bold(color(filename,THEME.get('title')))}/{caller}:{bold(color(lineno,THEME.get('value')))} : "+s+'\n')

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

    index = values.index(value)
    return keys[index]


## variables
### check if variable is in scope
def is_set(var,scope=None):
    if scope == None:
        scope = globals()
    return (var in scope and scope[var])

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
    x,y = get_infield_pos(return_offset=1)
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
    func = globals()[sys._getframe().f_back.f_code.co_name]

    for o in UI_TRACE:
        if func == o[0]:
            found = True
    else:
        found = False

    if not found:
        arr.insert(0,func)
        UI_TRACE.append(arr)

### redirect getch_loop to `fun` with `args`
def set_pipe(fun,arg,keep=None):
    global PIPE_OUTPUT, KEEP_PIPE

    PIPE_OUTPUT = fun,arg
    if not keep == None:
        KEEP_PIPE = keep

### return current index of object
def get_index(obj):
    return obj.selected_index


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








# UI #

## input dialog class
class InputDialog(Container):
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


## field class for input dialog
class InputDialogField(getch.InputField):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.width = len(self.value)
        self.height = 1
        self._is_selectable = False
        self.options = None

        self.value_style = lambda item: item

    # return text of self
    def __repr__(self):
        line = self.value_style(self.print(return_line=True))
        return line
    
    def set_style(self,key,value):
        setattr(self,key+'_style',value)

    # return value
    def submit(self):
        return self.value



## print s to coordinates, clear space for it if needed
def printTo(x=0,y=0,s='',clear=False):
    # clear the len of string with 1 margin on both sides
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

def get_infield_pos(return_offset=False):
    if 'infield' in globals().keys() and len(infield.value):
        offset = (len(infield.value)+2)//WIDTH

        if not infield.line_offset == offset:
            infield.wipe()

        infield.line_offset = offset

    else:
        offset = 0

    return [3,HEIGHT-2-offset]

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
        UI_TRACE.pop(-1)

        fun,args,new = UI_TRACE[-1]
        for e in UI_TRACE:
            dbg(e[0])
        dbg()

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

    # do actions specific to input dialog
    if isinstance(obj,InputDialog):
        # submit input
        if key == "ENTER":
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
            return

        # send key to field
        elif isinstance(obj.field,InputDialogField):
            obj.field.send(key)

        # navigate prompt
        else:
            if key in ["h","ARROW_LEFT"]:
                obj.selected_index -= 1
            elif key in ["l","ARROW_RIGHT"]:
                obj.selected_index += 1
            obj.select()

        print(obj)
        return

    elif key == "ENTER":
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
        d = create_submenu(selected)

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
        if selected.__ui_options and len(selected.__ui_options) == 2:
            if not globals().get(selected.real_label) == None:
                # add to depth
                selected.__ui_keys.append(selected.real_label)
                old_index = selected.__ui_options.index(globals()[selected.real_label])
                if old_index == 0:
                    new_index = 1
                else:
                    new_index = 0

                edit_json(
                        json_path=CURRENT_FILE,
                        keys=[selected.real_label],
                        key=selected.real_label,
                        value=selected.__ui_options[new_index]
                )

                fun,args,obj = UI_TRACE[-1]
                args['index'] = index

                kwargs = args.copy()
                fun(**kwargs)
                selected.__ui_keys.pop(-1)
            return

    elif key in "hjkl" or key.startswith("ARROW"):
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


    obj.select()
    print(obj)

## return to normal input
def return_to_infield(*args,**kwargs):
    global PIPE_OUTPUT,KEEP_PIPE
    
    #os.system('cls' if os.name == 'nt' else 'clear')
    infield.print()
    PIPE_OUTPUT = None
    KEEP_PIPE = False
    
## create menu from `source` dict
def create_menu(source,corners,index=None,dict_index=0,**container_args):
    source_arg = source

    if isinstance(source,list):
        fun,kwargs = source
        source = fun(**kwargs)
    else:
        source = source_arg

    objects = container_from_dict(source,**container_args,width=max(40,int(WIDTH*(1/2))))
        
    for o in objects:
        if not source_arg == source:
            o.dict_path = kwargs['path']

        for i,c in enumerate([v for k,v in THEME['corners'].items()]):
            if not c == None:
                o.set_corner(i,c)

        #o.width = min(WIDTH-5,o.width)
        o.center()

    c = objects[dict_index]

    # clear infield from screen
    infield.wipe()
    
    # set pipes
    set_pipe(handle_menu,{"obj": objects, 'page': dict_index},keep=True)
    if index == None:
        add_to_trace([
            {
                'source': source_arg,
                'index': lambda obj: obj.selected_index,
                'dict_index': dict_index,
                'corners': corners
            },c
        ])

    # print
    c.selected_index = (0 if index==None else index) 
    c.select()
    dbg('returning')
    print(c)
    
    return c

## create submenu from `source` object
def create_submenu(source,index=None,dict_index=0):
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
        if isinstance(source.__ui_options,list):
            options = source.__ui_options
        else:
            options = None

        d = InputDialog(
                    label_value=source.real_label,
                    label_underpad=1,
                    options=options,
                    field_value=str(source.real_value),
                    width=max(40,int(WIDTH*(1/2)))
        )
        #d.height += 1
        dbg(d.height)

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

    set_pipe(handle_menu,{'obj': dicts, 'page': dict_index})
    if index == None:
        add_to_trace([{'source': source, 'index': index, 'dict_index': dict_index}, d])

    return d


# these two are dumb, redo needed.
def test_ui(dict_index=0):
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
        add_to_trace([{'dict_index':dict_index},c])
    print(c)
    return c

def create_server_picker(source):
    d = Container(width=max(30,int((1/2)*WIDTH)),center_elements=0)
    title = Label(value='Choose server',justify='center')
    title.set_style('value',pytermgui.CONTAINER_TITLE_STYLE)

    d.add_elements([title,Label()])

    for key,value in source.items():
        chatr = value.get('chatroom')
        addr = urlparse(value.get('address')).netloc
        if addr == '':
            addr = 'localhost'

        p = Prompt(options=[chatr+color(' @ ',THEME['title'])+addr],justify_options="center")
        p.handler = lambda _,self: dbg(self.submit())
        d.add_elements(p)

    add_to_trace([{'source': source},d])
    set_pipe(handle_menu,{'obj': [d]})

    d.select()
    d.center()
    print(d)
        


def __creatrejlkdfa(source):
    def pad(s,times):
        return "  "*times+s

    d = Container(width=max(30,int((1/2)*WIDTH)),center_elements=0)
    title = Label(value=pytermgui.CONTAINER_TITLE_STYLE('Server selection'),justify='left')
    d.add_elements(title)

    #for key,value in source.items():
    #    p = Prompt(label=pad(str(key),times=1),value='')
    #    p.real_value = value
    #    p.custom_repr = reveal_repr
    #    d.add_elements(p)
    #    d._selection_changed = reveal_select
    options = []
    for key,content in source.items():
        chatroom = content['chatroom']
        address = urlparse(content['address']).netloc
        if address == '':
            address = 'localhost'

        options.append(chatroom+' @ '+address)
        continue
    
    d.add_elements(Prompt(options=options,justify_options='center',padding=0))
    



    set_pipe(handle_menu,{'obj': d})
    for i,c in enumerate([v for k,v in THEME['corners'].items()]):
        d.set_corner(i,c)
    add_to_trace([{'source': source},d])

    d.select()


    #d.select(0)
    d.center()
    print(d)

        


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
    global PIPE_OUTPUT,infield

    buff = ''
    while KEEP_GOING:
        key = getch.getch()

        # TODO: `dd`+n*(`ESC`+`i`) is buggy as shit
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



    ## INLINE ACTIONS
    # quit program in a clean way
    if action == "quit":
        print('\033[?25h')
        KEEP_GOING = 0
        sys.exit()

    elif action == "test_ui":
        test_ui()

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
        paste = clip.paste()

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

    # menu actions
    elif action.startswith('menu_'):
        menu = action.replace('menu_','')
        corners = ["X","X","X","X"]

        if menu == "settings":
            corners[1] = "settings"
            path = os.path.join(PATH,'settings.json')

        elif menu == "login":
            corners[1] = "login"
            path = os.path.join(PATH,'usercfg.json')
            pytermgui.set_attribute_for_id('usercfg-button_connect','handler', lambda *args: dbg('connect button pressed'))
            pytermgui.set_attribute_for_id('usercfg-button_add','handler', lambda *args: dbg('add button pressed'))
            pytermgui.set_attribute_for_id('usercfg_serverlist','handler', lambda old,new: (old.wipe(),create_server_picker(new.real_value)))


        elif menu == "test":
            test_ui()
            dbg('hey')
            return

        CURRENT_FILE = path

        # call menu handler
        d = create_menu(source=[load_path,{'path': path}],corners=corners)


    
    ## PIPES
    ### action_in actions
    elif action.endswith("_in"):
        set_pipe(do_in,{'action': action})
    
    ### find & till
    elif action == "find":
        set_pipe(find,{})

    elif action == "find_reverse":
        set_pipe(find,{'reverse': True})
    
    elif action == "till":
        set_pipe(find,{'offset': -1})

    elif action == "till_reverse":
        set_pipe(find,{'offset': -1, 'reverse': True})

    elif "replace" in action:
        if len(infield.value):
            set_pipe(replace,{'action': action})





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




# GLOBALS #
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

UI_TRACE = [[return_to_infield,{},'']]
CURRENT_FILE = None

# given by server
COOKIE = "flamingoestothestore"

# base data array to append to
#BASE_DATA = {
#    "username": USERNAME,
#    "cookie": COOKIE,
#    "chatroom": ROOMID,
#}



# TEMP MAIN
if __name__ == "__main__":
    ## clear screen
    print('\033[2J')

    if DO_DEBUG:
        open(LOGFILE,'w').close()
    dbg('starting teahaz at size',str(WIDTH),str(HEIGHT))

    if WIDTH < 37:
        w = Container(height=3)
        w.add_elements(Label(value=bold(color('Window width too low!','38;5;196')),justify='center'))
        w.add_elements(Label(value=italic(color('A minimum of 37 columns are required for teahaz.','38;5;244')),justify='left'))
        print(w)
        for _ in range(HEIGHT-w.height):
            print()
        sys.exit(1)



    # set pytermgui styles
    pytermgui.set_style(
            'container_title',
            lambda item: bold(color(item.upper(),THEME['title'])+':').replace('_',' ')
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

    pytermgui.set_attribute_for_id('settings-themes_showcolors','handler',lambda *args: (UI_TRACE[-1][2].wipe(),test_ui()))
    

    # set default mode
    infield = getch.InputField(pos=get_infield_pos())
    infield.line_offset = None
    infield.visual_color = lambda: '\033['+THEME['field_highlight']+'m'
    
    MODE_LABEL = Label('-- ESCAPE --',justify='left')
    MODE_LABEL.set_style('value',lambda item: color(item,THEME['mode_indicator']))
    x,y = get_infield_pos()
    MODE_LABEL.pos = [x,y+5]
    
    switch_mode("ESCAPE")

    # main input loop
    getch_loop()
