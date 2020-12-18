# SERVER SETTINGS
URL = "http://localhost:5000/api/v0/"
ROOMID = "conv1"
USERNAME = "pink"

# BINDINGS & INPUT
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
        "l": "goto_cursor_right",
        "ARROW_RIGHT": "goto_cursor_right",
        #"a": "mode_add",
        #"r": "mode_react",
        #"m": "mode_message",
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

# VIM BINDINGS
## will likely be merged together with other bind 
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
        "f": "find",
        "F": "find_reverse",
        "t": "till",
        "T": "till_reverse",
        "x": "character_delete",
    },
    "INSERT": {
    },

    "VISUAL": {
        "u": "selection_lowercase",
        "U": "selection_uppercase"
    }
}

# MISC
## this probably wont be user selectable
MESSAGE_BREAKLEN = 10
