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

BINDS = {
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

VIMMODE = 0
VIMBINDS = {
    "ESCAPE": {
        "ENTER":       "message_send",
        "I" :           "goto_line_start",
        "A" :           "goto_line_end",
        "h" :           "goto_cursor_left",
        "l" :           "goto_cursor_right",
        #"j":          "goto_line_down",
        #"k":          "goto_line_up",
        "gg":          "goto_text_start",
        "G" :          "goto_text_end",
        "w" :          "goto_word_next",
        "W" :          "goto_WORD_next",
        "b" :          "goto_word_prev",
        "B" :          "goto_WORD_prev",
        "ci":          "change_in",
        "cw":          "change_word_end",
        "di":          "delete_in",
        "dw":          "delete_word_end",
        "D" :          "delete_line_end",
        "f" :          "find",
        "F" :          "find_reverse",
        "t" :          "till",
        "T" :          "till_reverse",
        "x" :          "character_delete",
        "p" :          "paste",
        "yy":          "copy_line",
        "dd":          "delete_line",
    },
    "INSERT": {
        "ESC"  :       "mode_escape",
        "ENTER":       "insert_newline"
    },

    "VISUAL": {
        "ESC":         "mode_escape",
        "h"  :         "selection_left",
        "l"  :         "selection_right",
        "x"  :         "selection_delete",
        "u"  :         "selection_lowercase",
        "U"  :         "selection_uppercase",
        "$"  :         "select_line_end",
        "w"  :         "select_word_end",
        "i"  :         "select_in", 
        "d"  :         "selection_cut",
        "y"  :         "copy",
    }
}
# }}}
