# documentation
temporary README file for documentation

## BIND system
- global BINDS dict controls it
- syntax of dict
    ```python
    BINDS = {
        "<MODENAME>" = {
            "<key>": "<action>",
            ...
        },
        # example
        "NORMAL" = {
            "i": "mode_insert",
            ...
        }
    }
    ```
### Key for values
- `<MODENAME>` is an uppercase string
- `<action>` is a lowercase string with `_` separating multiple words
- `<key>` can be aquired by running `import getch; getch.getch()` in the python intepreter (`python3 -i`)

## Variables
- BINDS: above dict
- VALID_KEYS: reassigned every `switch_mode` call, contains keys in BINDS[MODE]
- ESCAPE_KEY: the key to go to `ESCAPE` mode with, `ESC` by default

### Important notes
- all modes go to `ESCAPE` by pressing `$ESCAPE_KEY`.
- flowchart of bind system:
```md
getch_loop() -> getch.getch() -> if $ESCAPE_KEY -> switch_mode('ESCAPE')
                                 \
                                  else if in VIMKEYS -> handle_action
                                   \
                                    else if in VALID_KEYS -> handle_action
                                     \ 
                                      else if INPUT_MODE -> input.send(key)
```

## Extensions
- extensions would overwrite the `BINDS` dict with their `on_enter` method
- their actions would have to be prefixed with something, so that `handle_action` can direct it to the extension
