# vim: foldmethod=marker

#: GENERAL {{{1
DO_DEBUG = 1

#: SERVER SETTINGS {{{1
URL = "http://localhost:5000/api/v0/"
ROOMID = "conv1"
USERNAME = "pink"

#: BINDINGS & INPUT {{{1
# general binds {{{2
ESCAPE_KEY = "ESC"
BINDS = {
    "ESCAPE": {
        "i": "mode_insert",
        "v": "mode_visual",
        "ENTER": "message_send",
        "j": "navigate_down",
        "k": "navigate_up",
        "h": "goto_cursor_left",
        "ARROW_LEFT": "goto_cursor_left",
        "ARROW_RIGHT": "goto_cursor_right",
        "l": "goto_cursor_right",
        "q": "quit",
    },
    "INSERT": {
        "ESC": "mode_escape",
        "ENTER": "insert_newline"
    },
    "VISUAL": {
        "h": "visual_selection_left",
        "l": "visual_selection_right",
        "x": "visual_selection_delete",
    }
}

# vim binds {{{2
## keep original cursor after exiting visual mode from `vi` input
KEEP_CURSOR_AFTER_SELECT = 0
VIMMODE = 1
VIMBINDS = {
    "ESCAPE": {
        "I":  "goto_line_start",
        "A":  "goto_line_end",
        "j":  "goto_line_down",
        "k":  "goto_line_up",
        "gg": "goto_text_start",
        "G":  "goto_text_end",
        "ci": "change_in",
        "di": "delete_in",
        "f":  "find",
        "F":  "find_reverse",
        "t":  "till",
        "T":  "till_reverse",
        "x":  "character_delete",
    },
    "INSERT": {
    },

    "VISUAL": {
        "u": "selection_lowercase",
        "U": "selection_uppercase",
        "$": "select_end",
        "w": "select_word_end",
        "i": "select_in" 
    }
}
# }}}
