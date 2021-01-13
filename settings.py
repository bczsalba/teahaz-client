# vim: set cursorline foldmethod=marker

#: GENERAL {{{1
DO_DEBUG = 1



#: SERVER SETTINGS {{{1
URL = "http://localhost:5000/api/v0/"
ROOMID = "conv1"
USERNAME = "pink"



#: BINDINGS & INPUT {{{1
# general binds {{{2
ESCAPE_KEY = "ESC"

BASEBINDS = {
    "ESCAPE": {
    },
    "INSERT": {
        "CTRL_L" : "mode_visual",
        "CTRL_P" : "paste",
        "CTRL_A" : "select_line",
        "ESC"    : "pass",
    },
    "VISUAL": {
        "ESC"        : "mode_insert",
        "ARROW_LEFT" : "selection_left",
        "ARROW_RIGHT": "selection_right",
        "BACKSPACE"  : "selection_delete",
        "CTRL_X"     : "selection_cut",
        "CTRL_P"     : "paste",
        "c"          : "selection_copy",
    }
}



# vim binds {{{2
## keep original cursor after exiting visual mode from `vi` input
KEEP_CURSOR_AFTER_SELECT = 0

VIMMODE = 1
VIMBINDS = {
    "ESCAPE": {
        # MODES
        "v" :          "mode_visual",
        "V" :          "select_line",
        "i" :          "mode_insert",
        
        # GOTO
        "I" :          "goto_line_start",
        "A" :          "goto_line_end",
        "h" :          "goto_cursor_left",
        "l" :          "goto_cursor_right",
        #"j":          "goto_line_down",
        #"k":          "goto_line_up",
        "gg":          "goto_text_start",
        "G" :          "goto_text_end",
        "w" :          "goto_word_next",
        "W" :          "goto_WORD_next",
        "b" :          "goto_word_prev",
        "B" :          "goto_WORD_prev",
        "dw":          "delete_word_end",
        "D" :          "delete_line_end",

        # INLINE
        "cw":          "change_word_end",
        "dw":          "delete_word_end",
        "D" :          "delete_line_end",
        "x" :          "character_delete",
        "p" :          "paste",
        "yy":          "copy_line",
        "dd":          "delete_line",
        "ENTER":       "message_send",

        # PIPES
        "ci":          "change_in",
        "di":          "delete_in",
        "f" :          "find",
        "F" :          "find_reverse",
        "t" :          "till",
        "T" :          "till_reverse",

        },
    "INSERT": {
        "ESC"  :       "mode_escape",
        "ENTER":       "insert_newline"
    },

    "VISUAL": {
        # MODES
        "ESC":         "mode_escape",

        # MOVEMENT
        "h"  :         "selection_left",
        "l"  :         "selection_right",
        "u"  :         "selection_lowercase",
        "U"  :         "selection_uppercase",
        "$"  :         "select_line_end",
        "w"  :         "select_word_end",
        "i"  :         "select_in", 

        # EDIT
        "x"  :         "selection_delete",
        "d"  :         "selection_cut",
        "y"  :         "copy",
    }
}
# }}}
