# so how will this work

# networking functions
- get_messages(time=None)
    - gets messages since last login (maybe earlier w arguments?)

- send(data,type)
    - sends data of type:
        * one function for all messages, difference only in the final part

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

## navigation & inputs
- vim like, binding based:
    * `i` always inserts into text box
    * esc goes to esc mode like in vim
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

