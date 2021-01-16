# :main=python3 uitest.py
from ui import Container,Prompt,Label,WIDTH,HEIGHT,bold,italic,underline
from client import dbg
from getch import getch,InputField
import time
import json


class InputDialog(Container):
    def __init__(self,options=None,label_value='',label_justify="center",label_underpad=0,field_value='',**kwargs):
        super().__init__(**kwargs)

        # set up label class
        self.label = Label(value=label_value,justify=label_justify)

        # set up field depending on options given
        if isinstance(options,list):
            self.field = Prompt(options=options)
        else:
            self.field = InputDialogField(default=field_value)
        
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


class InputDialogField(InputField):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)

        self.width = len(self.value)
        self.height = 1
        self._is_selectable = True
        self.options = None

    # return text of self
    def __repr__(self):
        line = self.print(return_line=True)
        return line

    # return value
    def submit(self):
        return self.value


options = None



#  #i.field.send(key)
    

#for y in range(HEIGHT):
#    for x in range(WIDTH):
#        print(f'\033[{y};{x}H#')
#
# open settings file
with open('settings.json','r') as f:
    SETTINGS = json.load(f)
   
    # create container
    c = Container(height=None,border="-|",padding=0)

    # go through SETTINGS
    for i,(key,item) in enumerate(SETTINGS.items()):

        # read titles into labels
        if "title" in key and key[-1].isdigit():
            l = Label(value=italic(bold(item)),justify="left")
            
            # only pad if not the first element
            if not i == 0:
                pad = Label()
                c.add_elements(pad)

            # add label to container
            c.add_elements(l)
            continue

        # avoid long items
        if len(str(item)) > 7:
            item = "..."

        # create, add prompt
        p = Prompt(label=key,value=str(item),padding=4)
        c.add_elements(p)

c.move([35,10])
print(c)
#dialog = InputDialog(label_underpad=0,padding=1,options=options,label_value=bold(italic("Give me a choice:")),label_justify="center",width=27)

SELECTED = 0
c.select(SELECTED)
print(c)
while 1:
    key = getch()
    if key == "j":
        SELECTED += 1

    elif key == "k":
        SELECTED -= 1

    elif key == "ENTER":
        c.wipe()
        obj = c.selected[0]
        d = InputDialog(label_value=obj.label+':',field_value=obj.value)

        key = None
        print(d)

        d.field.visual(0,len(obj.value))
        in_visual = True

        while not key == "ENTER":
            key = getch()

            if in_visual:
                if "ARROW" in key:
                    in_visual = False
                    print(d)
                    continue

                else:
                    d.field.clear_value()
                    in_visual = False
                    continue
            else:
                d.field.send(key)

            print(d)

        d.wipe()
        del d
        print(c)

        continue
    
    c.select(SELECTED)
    print(c)

#
#
#print(c)
#selected = 0
#while True:
#    key = getch.getch()
#    if key == "j":
#        selected += 1
#        c.select(selected)
#
#    elif key == "k":
#        selected -= 1
#        c.select(selected)
#
#    print(c)
#
#"""
#TODO:
#    implement input menu subclass
#    implement hints (maybe)
#"""

