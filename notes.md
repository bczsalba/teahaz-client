# BUGS
## in progress
[ ] Container-s don't update size properly when new elements are added
    -- this may not need to be fixed (lol), the reveal menu should be using labels for every level, not one long string.

## urgent
- `ESC` doesn't work after color menu

## can wait
- insert label should only show outside of menu
- only the first element in multipage containers resizes

## fixed


# FEATURES 
## upcoming checklist
- minor additions
    * [ ] `add_to_trace` can get the caller function dynamically, so it really should

- login menu
    * [ ] generate prompts for server options
        + basically, the idea is for the choice to be registered after an enter press, and for it to look like timetable.
        + [x] create dict to store data like address,nick,users?
        + [ ] overwrite select to be like asztal's timetable
        + [ ] overwrite handler for all prompts in serverlist with the id system

- general ui
    * [ ] add pathbar to bottom in settings (maybe other menus too)
    * [ ] make colorguide nicer
 
- multiline:
    * [ ] strip `\n` from paste
    * [ ] fix endless insert tags after `dd` and `ESC` `i`


- add to escape
    * [ ] `s` 

- new binds
    * [ ] CTRL_L or something to reprint current ui

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

- multiline:
    * [x] implement `\033[7m` highlighting for infield
    * [x] fix visual_goto_up/down not working
    * [x] implement custom cursor & highlight colors

- fixes for printing
    * [x] figure out what wipes the screen
    * [x] make it, like, not do that
