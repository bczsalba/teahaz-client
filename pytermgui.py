import sys,os,time



# HELPERS #
def clr():
    os.system('cls' if os.name == 'nt' else 'clear')

def set_style(key,value):
    key = key.upper()

    if key in globals():
        globals()[key] = value
    else:
        globals()[key+'_STYLE'] = value

def clean_ansi(s):
    import re
    return re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]').sub('', s)

def real_length(s):
    return len(clean_ansi(s))

def break_line(_inline,_len,_pad=0,_separator=' '):
    if _len == None or _separator not in _inline:
        return [_inline]

    # check if line is over length provided
    if real_length(_inline) > _len:
        clean = clean_ansi(_inline)
        current = ''
        control = ''
        lines = []
        pad = lambda l: (_pad*' ' if len(l) else '')

        for i,(clen,real) in enumerate(zip(clean.split(_separator),_inline.split(_separator))):
            # dont add separator if no current
            sep = (_separator if len(current) else "") 

            # add string to line if not too long
            if len(pad(lines)+control+_separator+clen) <= _len:
                current += sep + real
                control += sep + clen

            # add current to lines
            elif len(current):
                lines.append(pad(lines)+current)
                current = real
                control = clen

        # add leftover values
        if len(current):
            lines.append(pad(lines)+current)

        return lines

    # return original line in array
    else:
        return _inline.split('\n')



# EXAMPLES #

# generate list of containers from dict
# padding sets how much text should be indented under titles
#
# returns a list of Container objects, len() > 1 if the 
# container height wouldn't fit the screen
def container_from_dict(dic,padding=4,**kwargs):
    width = min(40,int(WIDTH*(2/3)))

    dic_c = Container(**kwargs,width=width)
    dicts = [dic_c]
    reverse_items = False
    handler = None
    current_padding = 1
    prompt_options = None
    datafile = None

    for i,(key,item) in enumerate(dic.items()):
        # read titles into labels
        if key.startswith("ui__title"):
            # get next title element
            for next_title,k in enumerate(list(dic.keys())[i+1:]):
                if k.startswith('ui__title') and k[-1].isdigit():
                    break

            l = Label(value=item,justify="left")
            l.set_style('value',CONTAINER_TITLE_STYLE)

            height_with_segment = dicts[-1].real_height + next_title*(1+dicts[-1].padding)+5
            
            if height_with_segment > HEIGHT-5:
                dicts.append(Container(**kwargs,width=width))
                dicts[-1].add_elements(l)
                continue

            
            # only pad if not the first element
            if not i == 0:
                pad = Label()
                dicts[-1].add_elements(pad)

            # add label to container
            dicts[-1].add_elements(l)

            # set new padding value
            current_padding = padding
            continue

        elif key.startswith("ui__prompt_options"):
            prompt_options = item
            continue

        elif key == "ui__reverse_items":
            reverse_items = True
            continue

        elif key.startswith("ui__prompt"):
            options = item
            p = Prompt(options=options)
            p.set_style('value',CONTAINER_VALUE_STYLE)
            dicts[-1].add_elements(p)
            continue

        elif key == "ui__file":
            datafile = item
            continue
            
        
        elif key.startswith("ui__padding"):
            dicts[-1].add_elements(Label())
            continue

        # reverse meanings of key & item
        if reverse_items:
            temp = key
            key = item
            item = temp

        # set real value (not str())
        real_value = item

        # ignore empty dicts
        if isinstance(item,dict):
            length = len(item.keys())
            if length == 0:
                continue
            else:
                item = "->"
        

        # create, add prompt
        p = Prompt(real_label=str(key),label=str(key),value=str(item),padding=current_padding)
        p.__ui_options = prompt_options
        prompt_options = None
        p.set_style('label',CONTAINER_LABEL_STYLE)
        p.set_style('value',CONTAINER_VALUE_STYLE)
        p.real_value = real_value
        p.__ui_keys = []
        
        # this is used to keep track of path taken for writing changes to a file


        # add prompt to dict
        if dicts[-1].height + p.height > HEIGHT-5:
            dicts.append(Container(**kwargs,width=width))

        dicts[-1].add_elements(p)


    do_tabline = len(dicts) > 1
    for i,d in enumerate(dicts):
        d.__ui_keys = []
        if not datafile == None:
            for e in d.elements:
                e.file = datafile
            d.file = datafile

        if do_tabline:
            tabline = Prompt(options=[n for n in range(len(dicts))])
            tabline.set_style('highlight',TABBAR_HIGHLIGHT_STYLE)
            tabline.select(i)
            tabline._is_selectable = False
            d.add_elements([Label(),tabline])

    return dicts




# COLORS #
def bold(s):
    return '\033[1m'+str(s)+'\033[0m'

def italic(s):
    return '\033[3m'+str(s)+'\033[0m'

def underline(s):
    return '\033[4m'+str(s)+'\033[0m'

def highlight(s,fg='30'):
    return color(clean_ansi(s),['47',fg])

def color(s,col):
    if isinstance(col,list):
        col = ';'.join(col)

    return f'\033[{col}m'+str(s)+'\033[0m'




# CLASSES #
class Container:
    """
    Object that contains other classes defined here.
    It needs a position, and its width & height can
    be automatically set when adding new elements.

    The `select` method goes through a list of this
    object's selectable elements, and instead of 
    just using the object, the individual options
    are stored.

    Styles:
          GROUP      KEY
        - Label      value_style  : style of labels
        - Prompt     label_style  : prompt left
        - Prompt     value_style  : prompt right
        - Container  corner_style : style for corners
    """

    def __init__(self,pos=None,border=None,width=None,height=None,dynamic_size=True,center_elements=True,padding=0):
        # sanitize width
        if not width == None:
            self.width = min(width,WIDTH)
        else:
            self.width = 0

        # sanitize height
        if not height == None:
            self.height = min(height,HEIGHT-2)
        else:
            self.height = 0
        self.real_height = self.height

        # set default position
        if pos == None:
            pos = [0,0]
        self.pos = pos

        # set up values
        self.previous_pos = None
        self.padding = padding

        self.elements = []
        self.selected = None
        self.selectables = []
        self.selected_index = 0

        self.styles = {}
        self.corners = [[],[],[],[]]
        self.corner_style = lambda c: c

        # set up border
        if border == None:
            border = CONTAINER_BORDER_CHARS
        self.border_style = CONTAINER_BORDER_STYLE
        self.set_borders(border)

        # set up flags
        self._do_dynamic_size = dynamic_size
        self._do_center_elements = center_elements
        self._is_centered = False
        

    # set style for element type `group`
    def set_style(self,group,key,value):
        # non group items
        if group == type(self):
            setattr(self,key+'_style',value)
            return

        if not group in self.styles.keys():
            self.styles[group] = []

        self.styles[group].append([key,value])

        for e in self.elements:
            if type(e) == group:
                e.set_style(key,value)


    # text representation of self
    def __repr__(self):
        global WIDTH,HEIGHT

        # TODO: detect need for centering (maybe?)
        nWIDTH,nHEIGHT = os.get_terminal_size()
        if not [WIDTH,HEIGHT] == [nWIDTH,nHEIGHT]:
            WIDTH,HEIGHT = nWIDTH,nHEIGHT
            self._window_size_changed()


        line = ''
        new_real_height = self.height

        # print elements
        x,starty = self.pos
        starty += 2
        x += 2

        # vertically center elements
        if self._do_center_elements:
            vertical_padding = max((self.real_height-sum(e.height for e in self.elements))//2,0)
            starty += vertical_padding

        # print all elements
        extra_lines = 0
        for i,e in enumerate(self.elements):
            self.width = min(max(self.width,e.width+4),WIDTH-4)
            e.width = self.width - 4

            # call event
            self._handle_long_element(e)

            e.pos = [x+1,starty+i]

            # get lines from element
            lines = repr(e).split('\n')

            # remove lines whos line_break returned empty
            if lines == [""]:
                self.elements.remove(e)
                for o in self.selectables:
                    if o[0] == e:
                        self.selectables.remove(o)
                continue

            diff = len(lines) - 1
            new_real_height += diff

            for li,l in enumerate(lines):
                line += f"\033[{starty+i+li};{x}H"+(real_length(l)+2)*' '
                line += f"\033[{starty+i+li};{x}H "+l

            starty += diff

        
        if not self.real_height <= new_real_height:
            self.real_height = new_real_height
            self.height = new_real_height
        self.get_border()

        # print border
        py = None
        from client import dbg
        for x,y,char in self.border[:]:
            # set previous y
            py = y

            # write to stdout
            line += f'\033[{y};{x}H'+char

        # update previous pos
        return line


    # internal function to add elements
    def _add_element(self,element):
        # set width for element if none is available
        if element.width == None:
            element.width = self.width

        # update self sizing
        if self.width == None or self._do_dynamic_size:
            # if element is too wide selt self width to it+pad
            if WIDTH-5 > element.width >= self.width:
                self.width = element.width+3

            # if element is too tall set self height
            if self.real_height+element.height >= self.height:
                self.height = self.real_height+element.height

        # run element to update its values
        repr(element)

        # add to elements
        # update real_height
        self.real_height += element.height
        self.height += element.height

        # add padding
        for _ in range(self.padding):
            e = Label("")
            self.elements.append(e)
            self.real_height += e.height
            self.height += e.height

        self.elements.append(element)

        # add selectables
        if element._is_selectable:
            # set options for range
            if element.options == None:
                options = 1
            else:
                options = len(element.options)

            # go through options, add element+index_in_element,index_in_container
            for i in range(options):
                self.selectables.append([element,i,len(self.selectables)+i])

        # update border
        self.get_border()


    # set border values
    def set_borders(self,border):
        if len(border) == 1:
            self.borders = [border,border,border,border]
        elif len(border) == 2:
            sides,topbottom = border
            self.borders = [sides,topbottom,sides,topbottom]
        elif len(border) == 3:
            left,top,right = border
            self.borders = [left,top,right,top]
        elif len(border) == 4:
            self.borders = border

    
    # set border corners
    def set_corner(self,corner,value,offset=0):
        if not hasattr(self,'border'):
            self.get_border()

        # get values
        if corner in ["TOP_LEFT",0]:
            char = self.border[1]
            side = "left"
            index = 0

        elif corner in ["TOP_RIGHT",1]:
            char = self.border[1]
            side = "right"
            index = 1

        elif corner in ["BOTTOM_LEFT",2]:
            char = self.border[3]
            side = "left"
            index = 2

        elif corner in ["BOTTOM_RIGHT",3]:
            char = self.border[3]
            side = "right"
            index = 3

        # get & replace indexes
        px,py = self.pos

        ## get x
        if side == 'right':
            startx = px+self.width+2 - real_length(value) - offset
        elif side == 'left':
            startx = px+1 + offset

        ## get y
        if char == self.border[1]:
            y = py+1
        elif char == self.border[3]:
            y = py+self.real_height+2+self.padding

        # insert new
        new = []
        for x,char in zip(range(startx,startx+real_length(value)),value):
            new.append([x,y,self.corner_style(char)])

        # filter duplicates
        coords = [[x,y] for x,y,_ in self.border]
        newcoords = [[x,y] for x,y,_ in new]

        for i,c in enumerate(self.border):
            x,y,_ = c

            from client import dbg
            if [x,y] in newcoords:
                newindex = newcoords.index([x,y])
                self.border.pop(i)
                self.border.insert(i,new[newindex])

        self.corners[index] = [corner,value,offset]


    # get list of border coordinates
    def get_border(self):
        px,py = self.pos
        x1,y1 = px,py
        x1 += 1
        y1 += 1
        x2 = px+self.width+1
        y2 = py+self.real_height+2+self.padding

        left,top,right,bottom = [self.border_style(a) for a in self.borders]
        self.border = []
        for y in range(py+1,y2):
            self.border.append([x1,y,left])
            self.border.append([x2,y,right])

        for x in range(px+1,x2+1):
            self.border.append([x,y2,bottom])
            self.border.append([x,y1,top])

        for c in self.corners:
            if not len(c):
                continue
            corner,value,offset = c
            self.set_corner(corner,value,offset)


    # wrapper for _add_element to make bulk adding easier
    def add_elements(self,elements):
        if not isinstance(elements,list):
            elements = [elements]

        for e in elements:
            self._add_element(e)

        # check if everything is valid
        repr(self)


    # select index in selectables list
    def select(self,index=None):
        if index == None:
            index = self.selected_index

        # error if invalid index
        if len(self.selectables) == 0:
            return

        if index > len(self.selectables)-1:
            if VERBOSE:
                raise Exception("Index is not in elements.")
            else:
                index = len(self.selectables)-1

        # avoid < 0 indexes
        index = max(0,index)
        
        # set instance variables
        self.selected = self.selectables[index]
        self.selected_index = index

        # go through selectables
        target_element = self.selectables[index][0]
        for i,(e,sub_i,_) in enumerate(self.selectables):
            # check if current is the target
            if i == index:
                e.select(sub_i)
                
            # unselect element if 
            elif not target_element == self.selectables[i][0]:
                e._is_selected = False
  
    
    # go through object, wipe ever character contained
    def wipe(self,pos=None):
        if pos == None:
            pos = self.pos

        if self.pos == None:
            return

        px,py = pos
        for y in range(py+1,py+self.height+2):
            for x in range(px+1,px+self.width+2):
                sys.stdout.write(f'\033[{y};{x}H ')

        sys.stdout.flush()

    
    # transform self to new position
    def move(self,pos):
        self.pos = pos
        self.wipe()
        self.get_border()


    # center container
    def center(self,xoffset=0,yoffset=5):
        self._is_centered = True
        if HEIGHT//2 < self.height-yoffset:
            yoffset = 0
        if WIDTH//2 < self.width-xoffset:
            xoffset = 0

        x = (WIDTH-self.width-xoffset)//2
        y = (HEIGHT-self.height-yoffset)//2
        self.move([x,y])


    # EVENT: window size changed
    # - checked for during __repr__
    def _window_size_changed(self):
        clr()

        self.width = min(self.width,WIDTH-5)
        self.height = min(self.height,HEIGHT)

        if self._is_centered:
            self.center()

        self.get_border()


    # EVENT: check for long elements, handle them
    # - called during __repr__ element loop
    def _handle_long_element(self,e):
        if hasattr(e,'label') and hasattr(e,'value'):
            # check value length
            if real_length(str(e.value))+4 > self.width*(1/3):
                # check if self can be extended
                if e.width+10 < WIDTH*(1/2) and e.width < self.width:
                    self.width = e.width+10
                else:
                    e.value = '...'
                
            if real_length(str(e.label))+4 > self.width*(1/2):
                e.label = str(e.label)[:int(self.width*(1/3))-3]+'...'

class Prompt:
    """ 
    A class to display an optional label, along with choices.
    There are two layouts: "<label> [option]" and a centered
    list of options. 

    If there is a label given during construction the first 
    option is chosen, and the options given are disregarded.

    Styles:
        - highlight_style : used for highlighting
        - label_style     : used for labels in type1 of prompt
        - value_style     : used for values (between [ and ],
                            non-inclusive.)
    """
    
    def __init__(self,width=None,options=None,label=None,real_label=None,value="",padding=0): 
        # the existence of label decides the layout (<> []/[] [] [])
        if label:
            self.label = str(label)
            if real_label == None:
                self.real_label = clean_ansi(self.label)
            else:
                self.real_label = real_label

            self.width = real_length(self.real_label)+real_length(value)
        else:
            self.label = label
            self.width = width
            self.real_label = label

        # set up dimensions
        self.height = 1

        # set up instance variables
        self.selected_index = None
        self.options = options
        self.padding = padding
        self.value = value

        # styles
        self.highlight_style = PROMPT_HIGHLIGHT_STYLE
        self.label_style = PROMPT_LABEL_STYLE
        self.value_style = PROMPT_VALUE_STYLE
        self.delimiter_style = PROMPT_DELIMITER_STYLE
        
        # flags
        self._is_selectable = True
        self._is_selected = False


    # return string representation of self
    def __repr__(self):
        delimiters = []
        for i,v in enumerate(self.delimiter_style):
            if i % 2 == 0:
                delimiters.append(v+' ')
            else:
                delimiters.append(' '+v)

        start,end = delimiters[:2]

        
        # if there is a label do <label> [ ]
        if not self.label == None:
            label = self.label_style(self.label)
            value = self.value_style(self.value)

            highlight = (self.highlight_style if self._is_selected else lambda item: item)

            middle_pad = (self.width-real_length(label)) - len(start+end) - real_length(value) - self.padding
            middle_pad = max(2,middle_pad)

            left = self.padding*" " + label + middle_pad*" "
            right = highlight(f"{start}{value}{end}")

            line = left + right
            self.width = max(self.width,real_length(line))

        # else print all options
        else:
            # set up line
            line = ''
            if isinstance(self.options, list):
                for i,option in enumerate(self.options):
                    option = self.value_style(option)
                    line += self._get_option_highlight(i)(f"{start}{option}{end}")+'  '
            else:
                line = self.value_style(self.value)

            # center all lines 
            lines = break_line(line,_len=self.width-3,_separator="  ")

            if lines == []:
                if VERBOSE:
                    raise Exception("Lines are empty, likely because the given length was too short.")
                else:
                    return ""
            
            for i,l in enumerate(lines):
                l_len = real_length(l)
                pad = ( (self.width-l_len)//2 + self.padding + 2) * " "
                lines[i] = pad + l + pad
                
            # set new hight, return line
            self.height = len(lines)
            line = "\n".join(lines) 
        
        return line


    # get highlight value for index in options
    def _get_option_highlight(self,index):
        if self._is_selected and self.selected_index == index:
            highlight = self.highlight_style
        else:
            highlight = lambda item: item
        return highlight


    # select index in options
    def select(self,index=0):
        self._is_selected = True
        self.selected_index = index

        if isinstance(self.options,list):
            self.value = self.options[index]
        return self.value


    # set style
    def set_style(self,key,value):
        setattr(self,key+'_style',value)


    # method to overwrite
    def submit(self):
        return self.value

class Label:
    """ 
    A simple, non-selectable object for printing text

    Styles:
        - value_style : style for string value of label
    """
    def __init__(self,value="",justify="center",width=None,padding=1):
        # values
        self.value = value
        self.height = 1

        # set width
        if not width == None:
            self.width = width
        else:
            self.width = real_length(self.value)+3

        self.justify = justify
        self.padding = padding
        self.value_style = LABEL_VALUE_STYLE


        # flags
        self._is_selectable = False
        self._is_selected = False

    def __repr__(self):
        lines = break_line(self.value_style(self.value),_len=self.width)

        if self.justify == "left":
            # nothing needs to be done
            lines[0] = self.padding*' '+lines[0]

        elif self.justify == "center":
            for i,l in enumerate(lines):
                pad = ((self.width-real_length(l))//2+1)*' '
                lines[i] = pad + l + pad

        elif self.justify == "right":
            for i,l in enumerate(lines):
                pad = (self.width-real_length(l))*' '
                lines[i] = pad + l

        self.height = len(lines)
        return "\n".join(lines)
        
    # set style of key to value
    def set_style(self,key,value):
        setattr(self,key+'_style',value)



# GLOBALS #

# global width & height -- refreshed at every new object creation
WIDTH,HEIGHT = os.get_terminal_size()

# styles
## other
GLOBAL_HIGHLIGHT_STYLE = highlight
CURSOR_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE
TABBAR_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE

# container
CONTAINER_BORDER_CHARS = "|-"
CONTAINER_BORDER_STYLE = lambda item: item
CONTAINER_LABEL_STYLE = lambda item: item
CONTAINER_VALUE_STYLE = lambda item: item
CONTAINER_CORNER_STYLE = lambda char: char
CONTAINER_TITLE_STYLE = lambda item: italic(bold(item))

## prompt
PROMPT_LABEL_STYLE = lambda item: item
PROMPT_VALUE_STYLE = lambda item: item
PROMPT_DELIMITER_STYLE = '[]'
PROMPT_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE

## label
LABEL_VALUE_STYLE = lambda item: item


# client global
VERBOSE = 0



# TEST CODE #
if __name__ == "__main__":
    import json,requests

    r = requests.get('https://online.sprinter.hu/terkep/data.json')
    d = r.json()
    d = d[0]
        
    c = container_from_dict(d)[0]
    c.set_corner(0,'example using sprinter json')
    c.set_corner(3,'pytermgui')
    c.set_style(Container,'corner',lambda a: color(a,'38;5;141'))
    c.set_style(Container,'border',lambda a: color(a,'38;5;220'))
    c.set_style(Prompt,'label',lambda a: color(a,'38;5;103'))
    c.set_style(Prompt,'value',lambda a: color(a,'38;5;61'))
    c.set_style(Prompt,'delimiter',['< ',' >'])
    c.set_borders('|_|-')
    c.select(3)
    c.center()
    print(c)
    input()
