# networking functions
- get(parameter,type="messages")
    * type can be `messages`/`file`
    * messages will return messages since `parameter` (in EPOCH time)
    * file will return contents of `parameter` on the server

- send(data,mType="text")
    * sends `data` of `mType`

# display stuff
## 2 threads:
- getch():
    * IMPORTANT: refresh should probably be here too, not sure how often though.
    * gets characters, sends them to input handler
    * likely could have custom bindings (local or server stored?)
    * needs its own thread as it's blocking
- main():
    * handles everything else
    * maybe uses frame based drawing?
        + pros:
            - would allow header and footer to always be present
        + cons:
            - id need to keep track of all messages, and only print the ones i need to specific coords
            - this could be done by storing messages line by line, and using the indexes as control

## navigation & inputs
- vim like, binding based:
    * `i` always inserts into text box
    * `ESC` goes to normal mode like in vim
    * rn there's no human-friendly translation for keycodes, so anything other than alphanumericals is a bit ugly
    * examples for binds:
        ```python
        BINDS = {
            "a": "add menu, like in messenger, has options for files and maybe games?",
            "jk": "probably binded separately, navigation",
            "r": "react menu"
        }
        
        VIMBINDS_ENABLED = 1
        VIMBINDS = {
            "I":  "goto_line_start",
            "A":  "goto_line_end",
            "j":  "goto_line_down",
            "k":  "goto_line_up",
            "gg": "goto_text_start",
            "G":  "goto_text_end"
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

