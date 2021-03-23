# PLANZ

# BUGS

# FEATURES 
## upcoming checklist
- [ ] settings should be overwritten by settings in .config/teahaz
- [ ] usercfg & session should be stored under .config/teahaz

- [ ] inline action sending

- [ ] notifications

- [ ] fix up completer
    - [ ] cant handle less than `self.rows` number of options

- windows compatibility:
    * [x] move os specific imports to their proper place
    * [ ] add more keys to keybinds for windows (specifically CTRL_*)
    * [x] convert \_GetchWindows \_\_call\_\_ to use wgetch || decode getch output
    * [ ] test on windows

- new binds
    * [ ] `s` 

- multi level inline codes
 
- add help menu for common errors

- FUTURE: gtk plugin

## maybe
- [ ] change infield cursor char depending on mode
- [ ] formatting commands, like `!th break`
- [ ] add pathbar to bottom in settings (maybe other menus too)

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
        * [x] matching parts of string are highlighted (with settable
          style)

```
    _________________________
    | your input matters    |
    | your input's cool     |
    | your input sucks      |
    | > your input          |
    -------------------------
```
- [x] messages would work better with positional printing

- [x] teahazrc file in $HOME/.config/teahaz/thconf.py

- [x] improve parse_inline_codes (refer to comment) !! USE REGEX !!

- [x] messaging lol
    * [ ] message
        + [x] get
        + [x] send
        + [x] display
            - [x] invent fancy formula to get pos of messages by index
        + [x] select

- [x] strip messages
    + [x] send
    + [x] receive

- [x] fix multiline
- [x] fix conv header

```
> FileManager(Container)

    """
    Container derivative that would show and let users interact
    with files.
    """

    - main methods (other than Container's):
        * [x] cd                 : change directory
        * [x] search(term)       : search for `term` in files
        * [x] execute(cmd) : execute given command in bash on the file
        * [x] open(opt: index)   : open selected file with the global filetype handlers

    - goals
        [x] have keybind support through field
        [x] highlight files and directories separately
        [x] do magiks :exclamation:
```

- [x] `--create-chatroom` arg

- [x] fix conv/user switching
    - [x] messages should reprint in set_chatroom (lno. 1935)

- [x] message replies!
    - [x] add submit action to message_select
    - [x] make reply action pre-set replyId
    - [x] add visual representation of replying-to
    - [x] make sent message add replyId
    - [x] make print_messages read & display replyId
    - [x] add goto_reply_parent action
    - [x] theres a specific message that breaks it all

```py
> LoadingScreen(Container):

    Universal loading screen to be called during
    any long operations. For re-implementation,
    provide .start() and .stop() methods, and 
    intercept input.

    - methods:
        + set_title
        + show
            * interrupts input
        + destroy
            * resumes input
    - goals
        + different functions can write data to it
        + callbacks are meant to destroy once loading is done
        + can be reimplemented easily in configs
```

- [x] universal handling of errors

- [x] ? help menu

- [x] work on chatroom selector
