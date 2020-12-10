# networking functions
- get(time)
    * gets messages since time

- get_file(name)
    * downloads file given

- send(data,type)
    * sends data of type

# display stuff
## 2 threads:
- getch():
    * gets characters, sends them to input handler like fishtank does
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
    * `ESC` goes to esc mode like in vim
    * rn there's no human-friendly translation for keycodes, so anything other than alphanumericals is a bit ugly
    * examples for binds:
        ```python
        binds = {
            "a": "add menu, like in messenger, has options for files and maybe games?",
            "jk": "probably binded separately, navigation",
            "r": "react menu"
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
            - user selects a message, and reactions come up:
            ```
            hey whats up
            0 :joy: 
            1 :sad:
            2 :idontknowdiscordemoticons:
            ```
            - if user inputs int in range of reactions that reaction is sent
            - else an input is built in the input field and sent as a normal reply

