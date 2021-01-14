from ui import Container,Prompt,Label,WIDTH,HEIGHT
from client import dbg,getch
import time
import json


for y in range(HEIGHT):
    for x in range(WIDTH):
        print(f'\033[{y};{x}H#')

# open settings file
with open('settings.json','r') as f:
    SETTINGS = json.load(f)
    
    # create container
    c = Container(height=None,border="-|",padding=0)

    # go through SETTINGS
    for i,(key,item) in enumerate(SETTINGS.items()):

        # read titles into labels
        if "title" in key and key[-1].isdigit():
            l = Label(value=item,justify="left")
            
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


    c.pos = [35,10]


selected = 0
while True:
    key = getch.getch()
    if key == "j":
        selected += 1
        c.select(selected)

    elif key == "k":
        selected -= 1
        c.select(selected)

    c.wipe()
    print(c)


