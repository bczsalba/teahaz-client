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
