# fuck
import sys,os,time

# these two should be imported from here in client
WIDTH,HEIGHT = os.get_terminal_size()

# client global
VERBOSE = 0




# HELPERS #
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




# CLASSES #
class Container:
    """
    Object that contains other classes defined here.
    It needs a position, and its width & height can
    be automatically set when adding new elements.

    The `select` method goes through a list of this
    object's selectable elements, which means that 
    after adding a Prompt with multiple options all
    said options are added to the indexes.
    """

    def __init__(self,pos,border=['=','#'],width=None,height=None,dynamic_size=True,center_elements=True):
        # set up descriptory values
        self.width = min(width,WIDTH)
        self.height = min(height,HEIGHT)
        self.pos = pos
        self.elements = []
        self.selectables = []

        # set up real_height value
        if not height == None:
            self.real_height = height
        else:
            self.real_height = 1
            self.height = 1

        # set up border
        self.borderchar_x,self.borderchar_y = border 
        self.get_border()

        # set up flags
        self._do_dynamic_size = dynamic_size
        self._do_center_elements = center_elements


    # text representation of self
    def __repr__(self):
        line = ''
        new_real_height = self.height

        # print elements
        x,starty = self.pos
        starty += 1
        x += 2

        # vertically center elements
        if self._do_center_elements:
            starty += (self.height-len(self.elements))//2

        # print all elements
        extra_lines = 0
        for i,e in enumerate(self.elements):
            # i wish i could explain why this works
            if WIDTH > 70:
                pad = max(17-(WIDTH-70),4)
            else:
                pad = 17

            e.width = self.width - pad

            # get lines from element
            lines = repr(e).split('\n')

            if lines == [""]:
                self.elements.remove(e)
                for o in self.selectables:
                    if o[0] == e:
                        self.selectables.remove(o)
                continue

            diff = len(lines)-1
            extra_lines += diff

            for li,l in enumerate(lines):
                line += f"\033[{starty+i+li};{x}H "+l

            starty += diff

        if not self.real_height == new_real_height+extra_lines:
            self.real_height += extra_lines
            self.get_border()

        # print border
        py = None
        for x,y,char in self.border:
            # set previous y
            py = y

            # write to stdout
            line += f'\033[{y};{x}H'+char

        return line


    # internal function to add elements
    def _add_element(self,element):
        # set width for element if none is avaiable
        if element.width == None:
            element.width = self.width

        # update self sizing
        if self.width == None or self._do_dynamic_size:
            # if element is too wide selt self width to it+pad
            if element.width >= self.width:
                self.width = element.width+3

            # if element is too tall set self height
            if self.real_height+element.height >= self.height:
                self.height = self.real_height+element.height

        # add to elements
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
                self.selectables.append([element,i])

        # update real_height
        self.real_height += element.height

        # update border
        self.get_border()

    
    # get list of border coordinates
    def get_border(self):
        px,py = self.pos
        x1,y1 = px,py
        x1 += 1
        y1 += 1
        x2 = px+self.width
        y2 = py+self.real_height

        self.border = []
        for y in range(py+1,py+self.real_height):
            self.border.append([x1,y,self.borderchar_y])
            self.border.append([x2,y,self.borderchar_y])

        for x in range(px+1,px+self.width+1):
            self.border.append([x,y1,self.borderchar_x])
            self.border.append([x,y2,self.borderchar_x])


    # wrapper for _add_element to make bulk adding easier
    def add_elements(self,elements):
        if not isinstance(elements,list):
            elements = [elements]

        for e in elements:
            self._add_element(e)

        # check if everything is valid
        repr(self)


    # select index in selectables list
    def select(self,index):
        # error if invalid index
        if index >= len(self.selectables):
            if VERBOSE:
                raise Exception("Index is not in elements.")
            else:
                index = len(self.selectables)-1
        
        # go through selectables
        for i,(e,sub_i) in enumerate(self.selectables):
            # check if current is the target
            if i == index:
                e.select(sub_i)
                
            # unselect element if 
            elif not i in range(index,len(self.selectables)):
                e._is_selected = False



class Prompt:
    """ 
    A class to display an optional label, along with choices.
    There are two layouts: "<label> [option]" and a centered
    list of options. 

    If there is a label given during construction the first 
    option is chosen, and the options given are disregarded.
    """
    
    def __init__(self,width=None,options=None,label=None,value=""): 
        # the existence of label decides the layout (<> []/[] [] [])
        if label:
            self.label = str(label)
        else:
            self.label = label

        # set up dimensions
        self.height = 1
        self.width = width

        # set up instance variables
        self.selected_index = None
        self.options = options
        self.value = value
        
        # flags
        self._is_selectable = True
        self._is_selected = False


    # return string representation of self
    def __repr__(self):
        # if there is a label do <label> [ ]
        if not self.label == None:
            highlight = ('\033[47m\033[30m' if self._is_selected else '')

            left = self.label + (self.width-len(clean_ansi(self.label)) - 4 - real_length(self.value)) * " "
            right = highlight + f"[ {self.value} ]" + '\033[0;0m'

            line = left + right

        # else print all options
        else:
            # set up line
            line = ''
            for i,option in enumerate(self.options):
                line += "  "+ self._get_option_highlight(i) + f"[ {option} ]" + '\33[0;0m'

            # center all lines 
            lines = break_line(line,_len=self.width-3,_separator="  ")

            if lines == []:
                if VERBOSE:
                    raise Exception("Lines are empty, likely because the given length was too short.")
                else:
                    return ""
            
            for i,l in enumerate(lines):
                l_len = real_length(l)
                pad = ( (self.width-l_len)//2 ) * " "
                lines[i] = pad + l + pad
                
            # set new hight, return line
            self.height = len(lines)
            line = "\n".join(lines) 
        
        return line


    # get highlight value for index in options
    def _get_option_highlight(self,index):
        if self._is_selected and self.selected_index == index:
            highlight = '\033[47m\033[30m'
        else:
            highlight = ''
        return highlight


    # select index in options
    def select(self,index=0):
        self._is_selected = True
        self.selected_index = index


    # method to overwrite
    def submit(self):
        if VERBOSE:
            raise Exception("Submit method needs to be implemented on a per-object basis.")
        else:
            return



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
        if self.justify == "left":
            line = self.value

        elif self.justify == "center":
            pad = ((self.width-real_length(self.value))//2)*' '
            line = pad + self.value + pad

        elif self.justify == "right":
            pad = (self.width-real_length(self.value))*' '
            line = pad + self.value

        return line
        



# TEST CODE #
if __name__ == "__main__":
    c = Container(width=70,height=6,pos=[1,1])
    p1 = Prompt(label="One:",value="fish")
    p2 = Prompt(label="Two:",value="pog")
    p3 = Prompt(label="Three:")
    p4 = Prompt(options=["exit program","abandon all hope","I'm feeling lucky","ye who enter here","have graduated"])
    l1 = Label(value="left",justify="left")
    l2 = Label(value="center",justify="center")
    l3 = Label(value="right",justify="right")

    c.add_elements([p1,p2,p3,p4,l1,l2,l3])


    TODO:
        add padding to container
        clean up code
        fix selection uppercase

    for i in range(len(c.selectables)):
        time.sleep(0.4)
        c.select(i)
        print(repr(c))





    print(f'\033[{HEIGHT-10};0H')
