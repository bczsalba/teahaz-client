Hey!

This file will document my development of the client side of Teahaz. It will be periodically updated.



# 2020/12/20

## intro
Firstly, I'd like to explain our plan with this project. It will be an end-to-end encrypted, open source, privately hosted messaging service, that is based in expandability. For now, the primary client will be a terminal client written in Python, but we have plans to create interfaces for the web and possibly mobile too. 

For now, the client doesn't really do much. I have implemented an easily extendable bind-based system, and using it created various Vim-like actions. Since Vim is both of our editors of choice, it is what is most important for the moment. However, the bind system is extendable to create a more traditional hotkey setup too.


## extension basics
The extension system is planned to be a huge part of Teahaz. The idea is, that these extensions could be normal Python projects, that would be run from Teahaz main. They would be stored in their own subfolder under some extensions directory, since they'll likely need multiple files to function. For now, I think a sort of manifest file would be needed alongside the script, so TH knows how to handle it. This would include the type of extension, along with some options. All of them would be able to overwrite the BINDS dict, and likely also the action_handler (at least to an extent). With this, they would be allowed to set up their own bindings and custom actions. The current idea for extension types are ['chatbot','binding','program']. 


## extension details
Chatbot extensions would locally host a webserver, and would show up in the TH chatroom browser as normal conversations, just like other extensions. The message sent to them would be interpreted by them, and responses would be automated. Not sure how much use this has, but its an idea.

Binding extensions would primarily extend the bindings for TH. Writing this, I'm realizing the best way to handle this would probably be as an option in all extensions, but alas, I've already started writing this paragraph.

Program extensions are what I think has the most potential. I've spent my day making so Asztal (a project of mine) can be run as a thread, its input set remotely and its print statements can be offset on the screen. I still want to implement a y-offset value too. These additions would be a chatroom (like the others), but instead of the messaging interface, they would show a program instead. Input to these programs would be handled by TH, using the standard getch_loop, allowing a sort of window focus system, where only the focused window gets input sent to it. The program could take up all space on the screen, but it would by default be limited to a certain width/height, and it would get this by the offset argument that will need to be standard.


## notification system
As expected, a messaging client will need some way to notify users. I am yet to have great ideas for mobile, but on desktop this should work. When starting teahaz, a daemon-like process would fork off of it, that would be listening to any new messages. When a new message is received, the process would print it to a location (probably top right corner) into the terminal. This way, whatever the user is doing it should notify them, so long as they're in their terminals. I could also implement a custom notification command to be set in the settings, which on linux could be `notify`, that gets sent (along with the message), by the daemon.

That is I think it for the day, next log will probably be more code-focused, as this was kind of an introduction. Thank you!

@bczsalba



# 2020/12/22

Today, I want to start working on some UI. 



# 2021/01/06

## 06:06 PM
Plans were made, not many of them were followed up on.

I *did* start working on UI, but then I realized multiline support is a must before I get to that. However, multiline support is basically Palpatine, and I am about a random engineer in the rebel team. I'm sure you can figure out how well that went.

Jokes aside, I have some of it down, the biggest problem is that the system was made with pretty much only single line inputs in mind. This means much of the underlying systems need to be changed and rearranged, and the whole logistics of it all need to be figured out. 

In the meanwhile though, I spent a good amount of time creating a git-based config syncing system which ended up pretty cool.

## 11:33 PM
Not much work was done today (surprisingly, right?), but I hope to be more productive tomorrow.

@bczsalba



# 2021/01/11
Man, I'm not good at this.

Delays and inability to remember things aside, I actually did a lot of work on the input mechanism.

Firstly, I rewrote the whole `change_in` function, as it was painfully non-modular. The current implementation consists of the function `do_in`, which takes a key and an action as parameters, gets start and end through `get_indices`, and does the rest of the handling itself. This made the pretty hard to understand/work with, single use `change_in` into two short and modular functions working together. 

I also added the capability of detecting `word`s using a lot more delimiters, as it was previously limited to " ".



I also spent some time trying to work out kinks about extensions. Here's my current idea:

All extensions have a sort of `manifest` file (or it could also be in the extension file as well, it's currently undecided), where they *have to* set up some key variables.

All of these would then be returned from their load method, and the client takes care of all the data.

An example of how I imagine this would work:

```python
def load():

    # ...
    # extension load procedures
    
    return {
                "name": 'Test',
                "version": 0.0,
                "type": 'context', #'context'/'bind'
                "handler": test_action_handler,
                "binds": {
                        'a': "do_a",
                        'b': "do_b",
                        'c': "do_c"
                }
            }
```

Now, you may have noticed the term `context`, which hasn't been mentioned yet. The original plan was to keep using the mode-based bindings, and for extensions to just add a new mode to those. However, this is problematic in multiple ways, mainly, that without re-implementation all the default actions would be unaccessible while the extension is active. 

So my (current) solution is the following. `BINDS`, as a dict will stay the same in the settings file. During runtime, it will be merged (and its conflicts overwritten) with the current context provided dictionary.

This merge would be done by a function like `change_context`. The job of this function will be to change the global `CONTEXT` value, set the new `CONTEXT_HANDLER` as well as update the dicts. 

Other than this, `handle_action` also needs to be able to use extension parts. This will be done by a code snippet similar to this:

```python

def handle_action(key,context_overwrite=False):
    if CONTEXT != <default_context> or context_overwrite:
        ret = CONTEXT_HANDLER(key)
        if not ret == "not_handled":
            return
        else:
            handle_action(key,context_overwrite=True)
            return

    # normal handler stuff
    # ...
    
```

This should, in theory, fix most of the problems I was having with the idea. I hope to be able to start implementing this somewhat soon, but it's not high priority as long as stuff like *the entire messaging functionality* is missing.

Thanks for reading!
@bczsalba
