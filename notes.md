    - [x] teahazrc file in $HOME/.config/teahaz/thconf.py
    - [ ] add loading screens to server functions
        + [ ] global object gets created, whos value can be set by functions
        + [ ] it launches a thread, then is killed by the caller

    - [ ] look into sorting functions under classes:
        + InputHandlers could be one
        + maybe Handlers in general

    - [ ] messages should be Containers
        + it would make retroactive proper grouping possible
        + there could be a bunch of cool new designs that way

    - [ ] messages would work better with positional printing



# BUGS
- [ ] add_new button in themes
- [ ] only the first element in multipage containers resizes

# TODO
- [ ] get_time should be current_day
- [ ] improve parse_inline_codes (refer to comment)
- [ ] restructure this file pls
- [ ] change infield cursor char depending on mode
- handle errors:
    * these should get you stuck in an infinite loop
    * [ ] Connection Refused
    * [ ] bad url
    * [ ] nodename nor service.. no internet

# FEATURES 
## upcoming checklist
- InputFieldCompleter(Container)

    """
    Container derivative for autocomplete function
    """

    - main goals:
        * [x] this object can get a field in the constructor,
          or create one for itself
        * [x] it uses FuzzyWuzzy for autocompletion
        * [x] intercepts field's keys to look for RETURN, up/down
        * [x] it gets a list of strings to look for, and it uses
          FW to get the 5 best matches
          NOTE: this list should be refreshable
        * [x] in the first iteration used by FileManager and emoji
          search
        * [ ] matching parts of string are highlighted (with settable
          style)

```
    _________________________
    | your input matters    |
    | your input's cool     |
    | your input sucks      |
    | > your input          |
    -------------------------
```

- FileManager(Container)

    """
    Container derivative that would show and let users interact
    with files.
    """

    - main methods (other than Container's):
        * cd : change directory
        * search(term) : search for `term` in files
        * open(opt: index) : open selected file with the global 
                             filetype handlers
        * execute(cmd,*maybe regex to match files*) : execute given command
                             in bash on the file


- file selector from messages:
    * some keybind lists all (recent) messages with files in them
    * at the bottom it also lists a keybind to open them
    ```
    nicholas cookieddough
    < filename >
    2021-03-05
    [`r`]
    ```

- add title to create_menu objects

- windows compatibility:
    * [x] move os specific imports to their proper place
    * [ ] add more keys to keybinds for windows (specifically CTRL_*)
    * [x] convert \_GetchWindows \__call__ to use wgetch || decode getch output
    * [ ] test on windows


- create general picker function that other pickers can call

- pytergmui.Container.get_lines()

    """
    would be needed for container support in messaging, 
    as printing further than end of terminal isnt supported 
    in the current state.
    """

    * [ ] keep track and return lines printed
    * [ ] also add borders to those lines, and return them


- messaging lol
    * [ ] message
        + [x] get
        + [x] send
        + [x] display
            - [x] invent fancy formula to get pos of messages by index
        + [ ] select

- new binds
    * [ ] `s` 

- general ui
    * [ ] add pathbar to bottom in settings (maybe other menus too)
 
- FUTURE: gtk plugin

## finished
- pytermgui `get_object_by_id(id)`
    * [x] store all objects with `ui__id` tag in a global dictionary
    * [x] make this dict appendable from other sources, as not everyone will use container_from_dict
    * [x] create method to return element of id given

- pytermgui buttons
    * [x] prompts should have a new type, which is a single button selection
    * [x] creation of buttons is done with the "ui__button" tag
    * [x] handlers of functions can be added by setting their `.handler` attribute

- color settings
    * [x] add highlights category
    * [x] make char styles live refresh
    * [x] fix <space> toggle
    * [x] (maybe) add corner char style

- profiles menu
    * [x] add settings/saving handler (maybe using edit_setting)
        + [x] make depth work properly
        + [x] add file attribute to all ui elements as they are made
    * [x] add handler functions & id system to pytermgui
    * [x] bugs
        + [x] UI_TRACE function doesn't restore values correctly
            - [x] obj.file not set sometimes
            - [x] deeper objects dont refresh their values

- login menu
    * [x] generate prompts for server options
        + basically, the idea is for the choice to be registered after an enter press, and for it to look like timetable.
        + [x] create dict to store data like address,nick,users?
        + [x] overwrite select to be like asztal's timetable
        + [x] overwrite handler for all prompts in serverlist with the id system

- multiline:
    * [x] implement `\033[7m` highlighting for infield
    * [x] implement custom cursor & highlight colors
    * [x] fix visual_goto_up/down not working
    * [x] fix paste not adjusting height
    * [x] strip `\n` from paste
    * [x] fix endless insert tags after `dd` and `ESC` `i`

- fixes for printing
    * [x] figure out what wipes the screen
    * [x] make it, like, not do that

- minor additions
    * [x] `add_to_trace` can get the caller function dynamically, so it really should

- new binds
    * [x] CTRL_L or something to reprint current ui

- general ui
    * [x] make colorguide nicer

- messaging lol
    * [x] basic functions first
        + [x] add server
        + [x] login/register
            - [x] basic menu
            - [x] login function
            - [x] register function

    * [x] top headerbar indicating current chatroom info

- restructure
    * [x] create Color class in pytermgui.py and move color things under it


- add inline formatting symbols
    + [x] italic
    + [x] bold
    + [x] italic_bold
    + [x] underline
    + [x] strikethrough

- [x] add prev_get support, extra messages before they send
