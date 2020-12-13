# taken and edited from https://code.activestate.com/recipes/134892/
# originally written by Danny Yoo
#
# fun note: it was posted 18 years ago and still works!


class _Getch:
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()
        self.keycodes = self.impl.keycodes

    def readchar(self):
        # from https://github.com/magmax/python-readchar
        # this checks if the input has ended or not
        c1 = self.impl()
        if ord(c1) != 0x1b:
            return c1

        c2 = self.impl()
        if ord(c2) != 0x5b:
            return c1 + c2

        c3 = self.impl()
        if ord(c3) != 0x33:
            return c1 + c2 + c3
        
        c4 = self.impl()
        return c1 + c2 + c3 + c4

    def __call__(self):
        key = self.readchar()

        # return human-readable name if found
        if key in self.keycodes.keys():
            return self.keycodes[key]
        else:
            return key


class _GetchUnix:
    def __init__(self):
        import tty, sys, select
        self.keycodes = {
            # SIGNALS
            "\x03": "SIGTERM",
            "\x1a": "SIGHUP",
            "\x1c": "SIGQUIT",
            # TEXT EDITING
            "\x7b": "BACKSPACE",
            "\x1b": "ESC",
            "\n": "ENTER",
            "\r": "ENTER",
            "\t": "TAB",
            # MOVEMENT
            "\x1b[A": "ARROW_UP",
            "\x1b[B": "ARROW_RIGHT",
            "\x1b[C": "ARROW_DOWN",
            "\x1b[D": "ARROW_LEFT",
        }

    def __call__(self):
        import sys, tty, termios, select
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt
        # TODO: add more compatibility
        self.keycodes = {
            "\x1b": "ESC",
            "\n": "ENTER",
            "\r": "ENTER",
            "\x7b": "BACKSPACE",
        }

    def __call__(self):
        global key

        import msvcrt
        return msvcrt.getch()

getch = _Getch()
