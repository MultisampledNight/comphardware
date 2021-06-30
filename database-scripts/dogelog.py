#!/usr/bin/env python3
"""
A logging module only for me to make my own log format easier to use. You
probably shouldn't use this, other, better modules like `logging` in the stdlib
are out there. This module is mainly thought for small scripts which just care
about logging itself, not controlling specifically how different modules log, or
how you want the final log entry to look like.

It has two modes. The normal mode looks like this:

:: Normal messages, issued with the info function.
// Verbose messages, issued with the debug function.
## Error, warning and critical messages, issued with the error function.

While the extensive mode looks like this:

[2021.06.02 21:56:29] [DEBUG //] A verbose message. As always.
[2021.06.02 22:11:09] [INFO  ::] Just an informational message that you are cool!
[2021.06.02 22:11:57] [ERROR ##] Can't find `Anime` in preferences!
"""
import atexit
import datetime
import enum
import sys
import time
from PIL.ImageColor import getrgb


COLOR_START = "\033[38;2;{0};{1};{2}m"
RESET = "\033[0m"

CYAN = COLOR_START.format(*getrgb("#00ffff"))
VIOLET = COLOR_START.format(*getrgb("#5f00ff"))
ORANGE = COLOR_START.format(*getrgb("#ff4b00"))


class Mode(enum.Enum):
    """
    The mode the formatter should be in. See the module notes for details.
    NONE is just the normal mode without colors.
    """
    NONE = 1
    NORMAL = 2
    EXTENSIVE = 3


class Level(enum.Enum):
    DEBUG = 1
    INFO = 2
    ERROR = 3


DEBUG = Level.DEBUG
INFO = Level.INFO
ERROR = Level.ERROR


mode = Mode.NORMAL
filterlevel = INFO
logfile = None
progress = None


def get_formatted_datetime():
    """
    Returns a pretty formatted datetime string in this format:
        YYYY.mm.dd HH.MM.SS
    """
    return datetime.datetime \
        .now() \
        .strftime("%Y.%m.%d %H:%M:%S")


def format_level(level):
    """
    Converts the given level into their representation in my logging system.
    """
    if mode == Mode.NONE:
        if level == DEBUG:
            return "//"
        elif level == INFO:
            return "::"
        elif level == ERROR:
            return "##"

    elif mode == Mode.NORMAL:
        if level == DEBUG:
            return f"{VIOLET}//{RESET}"
        elif level == INFO:
            return f"{CYAN}::{RESET}"
        elif level == ERROR:
            return f"{ORANGE}##{RESET}"

    if mode == Mode.EXTENSIVE:
        now = get_formatted_datetime()
        if level == DEBUG:
            return f"[{now}] [DEBUG //]"
        elif level == INFO:
            return f"[{now}] [INFO  ::]"
        elif level == ERROR:
            return f"[{now}] [ERROR ##]"


def close_if_needed():
    """Closes the logfile if needed."""
    global logfile
    if logfile is not None:
        logfile.close()
        logfile = None


def init():
    """
    Initializes logging using the INFO level, e.g. DEBUG messages don't get
    logged. This is the default if no other initialize function is called.
    You could also use this function to reset the settings to their default.
    """
    global mode
    global filterlevel

    close_if_needed()
    mode = Mode.NORMAL
    filterlevel = INFO

    atexit.register(close_if_needed)


def init_debug():
    """
    Initializes logging using the DEBUG level and normal terminal escape
    codes.
    """
    global mode
    global filterlevel

    close_if_needed()
    mode = Mode.NORMAL
    filterlevel = DEBUG

    atexit.register(close_if_needed)


def init_colorless():
    """
    Initializes logging using the INFO level, but with no colors.
    """
    global mode
    global filterlevel

    close_if_needed()
    mode = Mode.NONE
    filterlevel = INFO

    atexit.register(close_if_needed)


def init_file(file: str):
    """
    Initializes logging using the DEBUG level, and uses the given file as
    logging target.
    """
    global logfile
    global mode
    global filterlevel

    close_if_needed()
    mode = Mode.EXTENSIVE
    filterlevel = DEBUG
    logfile = open(file, "a")
    logfile.write(f"   >>> NEW LOG BEGINS AT {get_formatted_datetime()} <<<\n")

    atexit.register(close_if_needed)


def log(message: str, level: Level):
    """
    Logs to stdout and to stderr for the ERROR level by default, but instead
    logs to the given file if you used `init_file` to initialize logging.
    """
    message = str(message)
    # don't write the log entry if it is below filter level
    if level.value < filterlevel.value:
        return

    # I want to look the log like this if the message contains newlines:
    # 
    # :: Please note:
    #    I have no idea what I'm doing.
    #    Please stop reading this.
    #
    # And in extensive mode like this:
    # 
    # [2021.06.03 11:57:34] [INFO  ::] wow
    #                                  many newline
    #                                  such indent
    formatted_info = format_level(level)
    splitted_message = iter(message.split("\n"))

    # due to the color escape codes in the NORMAL mode, we just resort to
    # setting the length manually
    if mode == Mode.NORMAL:
        # not concerned? try this
        # >>> len("//")
        # 2
        # >>> len("::")
        # 2
        # you get the idea
        indent = 2
    else:
        indent = len(formatted_info)
    indent = " " * indent

    # now we actually format the message
    logentry = [f"{formatted_info} {next(splitted_message)}"]
    for part in splitted_message:
        logentry.append(f"{indent} {part}")
    logentry = "\n".join(logentry)

    # find the file target we want to write to
    if logfile is None:
        # let's misuse the fact that stdout is a file descriptor then
        if progress is None:
            if level == ERROR:
                target = sys.stderr
            else:
                target = sys.stdout
        else:
            # we can't print an error on stderr because stdout and stderr might
            # not be in sync, and that will look messed up
            target = sys.stdout

            # check if the log entry has to be printed before the progress bar, to
            # avoid conflict of entry and bar
            progress._delete_on_stdout()
            sys.stdout.flush()
            progress.last_print_len = 0  # don't print \b at the _redraw function
    else:
        target = logfile

    # the time has come, the logentry is formatted correctly, we've determined
    # where the logentry should be, let's write it to where it belongs
    print(logentry, file=target)

    if logfile is None and progress is not None:
        # output is a terminal and a progress bar is active
        # let's revive it, now that we printed the logentry
        progress._redraw()


def debug(message: str):
    """
    Just an alias for `dogelog.log` with the DEBUG level. Note that this
    doesn't get written to stdout or the logfile if it is below filter level,
    which is the case when initialized with `dogelog.init` or
    `dogelog.init_colorless`.
    """
    log(message, DEBUG)


def info(message: str):
    """
    Just an alias for `dogelog.log` with the DEBUG level. The entry won't be
    written to stdout or the logfile if you set the level manually to ERROR.
    """
    log(message, INFO)


def error(message: str):
    """
    Just an alias for `dogelog.log` with the ERROR level. This gets written to
    stderr, or to the logfile if logging has been initialized with
    `dogelog.init_file`.
    """
    log(message, ERROR)


def _map_range(value: float, instart: float, instop: float, outstart: float,
        outstop: float):
    return outstart + (outstop - outstart) \
        * ((value - instart) / (instop - instart))


class Progress:
    """
    An incredibly stupid implementation of a live progress bar.

    The message will be displayed before the progress bar, and right after that
    progress/end. As an example:
    
    :: Baking lights in your oven...  96/665 [/////——————————————————]
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^     ^^^
                  message                end

    Sidenote: Don't even try to change the fields manually. That will go wrong.
    Reading is fine though.
    Sidenote 2: I really recommend you to call .finish() if you won't use the
    progress bar anymore. That will allow you to log again.
    """
    def __init__(self, message: str, end: int):
        global progress

        self.message = message
        self.end = end
        self.current = 0
        self.last_print_len = 0

        progress = self

    def _delete_on_stdout(self):
        if self.last_print_len == 0 or logfile is not None:
            return
        sys.stdout.write("\b" * self.last_print_len)
        sys.stdout.write(" " * self.last_print_len)
        sys.stdout.write("\b" * self.last_print_len)

    def _redraw(self):
        # first delete all past characters
        self._delete_on_stdout()

        # compose the new status
        prefix = format_level(INFO)

        current = str(self.current).rjust(len(str(self.end)))  # avoid shifting the whole bar
        fraction = f"{current}/{self.end}"

        if self.current >= self.end:
            # no need for calculating the fill if we are out of the bar's scope
            bar = f"[{'/' * 23}]"
        else:
            # keep [//////////////——————————] in mind, length of the inner bar is 23
            # characters
            filled_count = int(_map_range(self.current, 0, self.end, 0, 23))
            empty_count = 23 - filled_count  # just inversed
            bar = f"[{'/' * filled_count}{'—' * empty_count}]"
        
        if logfile is not None:
            # don't update self.last_print_len as stdout hasn't been changed
            # instead just write the fraction to the file
            status = f"{prefix} {self.message} {fraction}"

            print(status, file=logfile)
        else:
            # print it and update self.last_print_len
            status = f"{prefix} {self.message} {fraction} {bar}"

            sys.stdout.write(status)

            sys.stdout.flush()
            self.last_print_len = len(status)

    def stack(self):
        """Increases the progress bar by 1 and re-draws it."""
        self.current += 1
        self._redraw()

    def increase(self, amount: int):
        """Increases the progress bar by the given amount and redraws it."""
        self.current += amount
        self._redraw()

    def is_done(self):
        """Returns whether the progress bar is finished."""
        return self.current >= self.end

    def finish(self):
        """Finishes the progress bar and enables logging again."""
        global progress

        # avoid calling _redraw on an now unimportant progress bar
        progress = None
        
        # in a file it doesn't matter
        if logfile is None:
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.last_print_len = 0


if __name__ == "__main__":
    init_debug()

    info("So many informations! uwu\nNewlines are possible as" \
         " well.\nNeeewlines!")
    debug("A debug/verbose message hidden in the shadows. uwu\nEverything" \
          " supports newlines. The error function, too.")
    error("Error! WEEEEEEEEEEEEEEEEEEEEE")

    info("Switching to INFO filter level, which ignores debug messages")
    init()
    debug("Debug trash that's invisible.")
    info("But INFO and ERROR messages still remain visible! (you don't see" \
         " the DEBUG message a bit above.)")
    error("welp\nAnd of course, newlines are still supported, they're" \
          " always supported")

    progress = Progress("A wild progress bar!", 100)
    for i in range(100):
        progress.stack()
        if i == 20:
            time.sleep(0.4)
        elif i == 45:
            info("Surprise message while progressing!")
            time.sleep(0.23)
        else:
            time.sleep(0.05)
    progress.finish()

    info("Beginning to log to the file `doge.log`, because I don't want to" \
         " spam the user's terminal. Idk.")
    init_file("doge.log")
    info("Phew, ok, we've got out of there. Finally.")
    debug("Debug messages are back again.\nI've decided to let them in the" \
          " logging file, as that is the one which developers get in a bug" \
          " report.")
    info("You don't need to call anything at exit. Just don't exit with " \
         "`os._exit`, as that one can't be catched by `atexit`.")
    error("Received an unrecoverable error, exiting for no reason!\nGoodbye!")


# vim:textwidth=80:
