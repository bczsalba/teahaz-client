# Teahaz Client
this is the ongoing notes documenting the program, proper README to be added closer to release.

## networking functions
- get(parameter,type="messages")
    * type can be `messages`/`file`
    * messages will return messages since `parameter` (in EPOCH time)
    * file will return contents of `parameter` on the server

- send(data,mType="text")
    * sends `data` of `mType`

## display stuff
### 2 threads:
- getch():
    * uses getch.InputField class
    * bindings are stored in the BINDS dict
    * needs its own thread as it's blocking
- main():
    * handles everything else
    * maybe uses frame based drawing? BINGO
        + pros:
            - would allow header and footer to always be present
        + cons:
            - id need to keep track of all messages, and only print the ones i need to specific coords
            - this could be done by storing messages line by line, and using the indexes as control

### navigation & inputs
- vim like, binding based:
    * `i` always inserts into text box
    * `ESC` goes to normal mode like in vim
    * examples for binds:
        ```python
        BINDS = {
            "NORMAL": {
                "i": "insert",
                "ESC": "escape",
                "j": "navigate_down",
                "k": "navigate_up",
                "a": "menu_add",
                "r": "menu_react",
                "m": "menu_message"
            },
            "INSERT": {
                "ESC": "escape"
            },
            "MESSAGE": {
                "s": "message_send",
                "ENTER": "message_newline",
                "c": "message_clear",
            },
        }
        VIMBINDS_ENABLED = 1
        VIMBINDS = {
            "I":  "goto_line_start",
            "A":  "goto_line_end",
            "j":  "goto_line_down",
            "k":  "goto_line_up",
            "gg": "goto_text_start",
            "G":  "goto_text_end",
        }
        ```
        + add menu:
            - brings up selection between modes
            - modes:
                * file:
                    - brings up file selector
                * games?
                    - ????????
        + react menu:
            - compacts all messages, gives each an index and allows scrolling
                * maybe can be accessed by using arrow UP/DOWN in normal mode
            - user selects a message, and reactions come up:
            ```
            0 :joy: 
            1 :sad:
            2 :idontknowdiscordemoticons:
            ```
            - message moves to center of screen, other messages are hidden or **faded**
            - if user inputs int in range of reactions that reaction is sent
            - else an input is built in the input field and sent as a normal reply

## notification system
- likely separate program that runs in the background
- shows new message in top right corner of terminal
- allows user to go to teahaz to open it (like a special argument or something) with a command

## extensions
- separate scripts
- teahaz imports them and runs their start function in a thread
- they can be locally hosted servers
- if the user switches to locally hosted chatroom, its `on_enter` function is called, same with `on_exit`
- these functions are to set up special bindings for the server, and to start whatever process it needs
