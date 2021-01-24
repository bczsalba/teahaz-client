import sys,os,time



# HELPERS #
def clr():
    os.system('cls' if os.name == 'nt' else 'clear')

def set_style(key,value):
    if not callable(value):
        return Exception("Style value needs to be callable.")

    globals()[key.upper()+'_STYLE'] = value

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

def container_from_dict(dic,**kwargs):
    dic_c = Container(**kwargs)
    dicts = [dic_c]
    reverse_items = False
    handler = None

    if False:
        options = {
                "dialog_type": None,
                "reverse_items": False
        }

        try:
            from pytermconf import GROUPS
        except ImportError as e:
            if VERBOSE:
                raise e


    for i,(key,item) in enumerate(dic.items()):
        # look for flag groups, UNUSED
        if key == "ui__group":
            if "GROUPS" in locals() and item in GROUPS.keys():
                for key,value in GROUPS[item].items():
                    options[key] = value
            continue

        # read titles into labels
        elif "ui__title" in key and key[-1].isdigit():
            # get next title element
            for next_title,k in enumerate(list(dic.keys())[i:]):
                if k.startswith('ui__title') and k[-1].isdigit():
                    break

            l = Label(value=CONTAINER_TITLE_STYLE(item),justify="left")
            height_with_segment = dicts[-1].height + next_title*(1+dicts[-1].padding)+15

            if height_with_segment > HEIGHT:
                dicts.append(Container(**kwargs))
                dicts[-1].add_elements(l)
                continue



            
            # only pad if not the first element
            if not i == 0:
                pad = Label()
                dicts[-1].add_elements(pad)

            # add label to container
            dicts[-1].add_elements(l)
            continue

        elif key == "ui__reverse_items":
            reverse_items = True
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
            if len(item.keys()) == 0:
                continue
            else:
                item = "..."


        # create, add prompt
        p = Prompt(real_label=str(key),label=CONTAINER_LABEL_STYLE(str(key)),value=CONTAINER_VALUE_STYLE(str(item)),padding=4)
        p.real_value = real_value


        # add prompt to dict
        if dicts[-1].height + p.height > WIDTH-15:
            dicts.append(Container(**kwargs))

        dicts[-1].add_elements(p)


    # avoid long items
    do_tabline = len(dicts) > 1
    for i,d in enumerate(dicts):
        for e in d.elements:
            if isinstance(e,Prompt):
                item = e.value
                label = e.label

                if real_length(str(item)+str(label)) > min(d.width-10,WIDTH-5):
                    e.value = "..."

        if do_tabline:
            tabline = Prompt(options=[n for n in range(len(dicts))],highlight_style=TABBAR_HIGHLIGHT_STYLE)
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
    """

    def __init__(self,pos=None,border=None,width=None,height=None,dynamic_size=True,center_elements=True,padding=0):
        # sanitize width
        if not width == None:
            self.width = min(width,WIDTH-2)
        else:
            self.width = 0

        # sanitize height
        if not height == None:
            self.height = min(height,HEIGHT)
        else:
            self.height = 0
        self.real_height = self.height

        # set default position
        if pos == None:
            pos = [0,0]
        self.pos = pos

        # set up values
        self.elements = []
        self.selected = None
        self.selectables = []
        self.padding = padding
        self.selected_index = 0
        self.previous_pos = None

        # set up border
        if border == None:
            border = CONTAINER_BORDER_STYLE
        self.set_borders(border)

        # set up flags
        self._do_dynamic_size = dynamic_size
        self._do_center_elements = center_elements
        

    # text representation of self
    def __repr__(self):
        global WIDTH,HEIGHT

        nWIDTH,nHEIGHT = os.get_terminal_size()
        if not [WIDTH,HEIGHT] == [nWIDTH,nHEIGHT]:
            clr()
            xdiff = (nWIDTH-WIDTH)//2
            ydiff = nHEIGHT-HEIGHT

            WIDTH,HEIGHT = nWIDTH,nHEIGHT

            self.pos[0] += xdiff
            #self.pos[1] += ydiff

            self.width = min(self.width,WIDTH-2)
            self.height = min(self.height,HEIGHT)
            self.get_border()
        #self.center()

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
            if e.width > self.width-4:
                if e.width >= WIDTH:
                    if VERBOSE:
                        raise Exception("Element width too high.")
                    else:
                        continue
                elif self._do_dynamic_size:
                    self.width = e.width + 4

            e.width = self.width - 4
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
        for x,y,char in self.border:
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
            if WIDTH-6 > element.width >= self.width:
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

            # go through options, add element+index pairs
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
    #TODO
    def set_corner(self,corner,value):
        self.get_border()

        # get values
        if corner in ["TOP_LEFT",0]:
            char = self.borders[1]
            side = "left"

        elif corner in ["TOP_RIGHT",1]:
            char = self.border[1]
            side = "right"

        elif corner in ["BOTTOM_LEFT",2]:
            char = self.border[3]
            side = "right"

        elif corner in ["BOTTOM_RIGHT",3]:
            char = self.border[3]
            side = "right"


    # get list of border coordinates
    def get_border(self):
        px,py = self.pos
        x1,y1 = px,py
        x1 += 1
        y1 += 1
        x2 = px+self.width+1
        y2 = py+self.real_height+2+self.padding

        left,top,right,bottom = self.borders

        self.border = []
        for y in range(py+1,y2):
            self.border.append([x1,y,left])
            self.border.append([x2,y,right])

        for x in range(px+1,x2+1):
            self.border.append([x,y1,top])
            self.border.append([x,y2,bottom])


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
        if HEIGHT//2 < self.height-yoffset:
            yoffset = 0
        if WIDTH//2 < self.width-xoffset:
            xoffset = 0

        x = (WIDTH-self.width-xoffset)//2
        y = (HEIGHT-self.height-yoffset)//2
        self.move([x,y])


class Prompt:
    """ 
    A class to display an optional label, along with choices.
    There are two layouts: "<label> [option]" and a centered
    list of options. 

    If there is a label given during construction the first 
    option is chosen, and the options given are disregarded.
    """
    
    def __init__(self,width=None,options=None,label=None,real_label=None,value="",padding=0,highlight_style=None): 
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
        if highlight_style == None or not callable(highlight_style):

            self.highlight_style = PROMPT_HIGHLIGHT_STYLE
        else:
            self.highlight_style = highlight_style

        self.options = options
        self.padding = padding
        self.value = value
        
        # flags
        self._is_selectable = True
        self._is_selected = False


    # return string representation of self
    def __repr__(self):
        # if there is a label do <label> [ ]
        if not self.label == None:
            highlight = (self.highlight_style if self._is_selected else lambda item: item)

            middle_pad = (self.width-real_length(self.label)) - 4 - real_length(self.value) - self.padding
            middle_pad = max(4,middle_pad)

            left = self.padding*" "+ self.label + middle_pad * " "
            right = highlight(f"[ {self.value} ]")

            line = left + right
            self.width = max(self.width,real_length(line))

        # else print all options
        else:
            # set up line
            line = ''
            if isinstance(self.options, list):
                for i,option in enumerate(self.options):
                    line += "  "+ self._get_option_highlight(i)(f"[ {option} ]")
            else:
                line = self.value

            # center all lines 
            lines = break_line(line,_len=self.width-3,_separator="  ")

            if lines == []:
                if VERBOSE:
                    raise Exception("Lines are empty, likely because the given length was too short.")
                else:
                    return ""
            
            for i,l in enumerate(lines):
                l_len = real_length(l)
                pad = ( (self.width-l_len)//2 + self.padding - 1) * " "
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


    # method to overwrite
    def submit(self):
        return self.value


class Label:
    def __init__(self,value="",justify="center",width=None):
        # values
        self.value = value
        self.height = 1

        # set width
        if not width == None:
            self.width = width
        else:
            self.width = real_length(self.value)+3

        self.justify = justify


        # flags
        self._is_selectable = False
        self._is_selected = False

    def __repr__(self):
        lines = break_line(self.value,_len=self.width)

        if self.justify == "left":
            # nothing needs to be done
            pass

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
        



# GLOBALS #

# global width & height -- refreshed at every new object creation
WIDTH,HEIGHT = os.get_terminal_size()

# styles
CONTAINER_TITLE_STYLE = lambda item: italic(bold(item))
CONTAINER_LABEL_STYLE = lambda item: item
CONTAINER_VALUE_STYLE = lambda item: item
CONTAINER_BORDER_STYLE = "|-"

GLOBAL_HIGHLIGHT_STYLE = highlight
PROMPT_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE
CURSOR_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE
TABBAR_HIGHLIGHT_STYLE = GLOBAL_HIGHLIGHT_STYLE

# client global
VERBOSE = 0




# TEST CODE #
if __name__ == "__main__":
    c = Container(width=50,height=None,pos=[10,5],padding=1,dynamic_size=False)
    c.set_borders([bold('|'),bold('-')])
    p1 = Prompt(label="One:",value="fish")
    p2 = Prompt(label="Two:",value="pog")
    p3 = Prompt(label="Three:")
    p4 = Prompt(options=["exit program","abandon all hope","I'm feeling lucky","ye who enter here","have graduated"])
    l1 = Label(value="left",justify="left")
    l2 = Label(value="center",justify="center")
    l3 = Label(value="right",justify="right")

    c.add_elements([l1,l2,l3])
    #c.add_elements(Label())
    c.add_elements([p1,p2,p3])
    #c.add_elements(Label())
    c.add_elements([p4])


    """
    TODO:
        fix selection uppercase
    """

    for i in range(len(c.selectables)):
        time.sleep(0.8)
        c.select(i)
        print(repr(c))
        #input()




    print(f'\033[{HEIGHT-10};0H')
