# BUGS
## in progress

## urgent
- `D` doesn't work

## can wait
- insert label should only show outside of menu
- only the first element in multipage containers resizes

## fixed
- [x] exit doesnt reenable cursor
- [x] login menu is narrow as shit
- [x] holding j on long buttons causes weird expansion
- [x] there is an extra padding when ui__file is set



# FEATURES 
## upcoming checklist
- login menu
    * [ ] generate prompts for server options
        + [ ] create dict to store data like address,nick,users?
        + [ ] overwrite handler for all prompts in serverlist with the id system
        + [ ] overwrite select to be like asztal's timetable

- fixes for printing
    * currently, every print() call wipes the container
    * this causes flashing in lower performance terminals like vim's
    * to fix:
        + [ ] make `container.select` clear the previously selected prompt
        + [ ] make InputDialog only clear Infield (maybe even just the changes made to it)
 
- multiline:
    * [ ] fix endless insert tags after `dd` and `ESC` `i`
    * [ ] fix visual_goto_up/down not working


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
