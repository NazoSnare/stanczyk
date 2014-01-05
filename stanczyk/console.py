from collections import OrderedDict
from functools import partial, update_wrapper
from inspect import getargspec
from stanczyk import consoleFunctions
from texttable import Texttable
from twisted.conch.stdio import ConsoleManhole

CTRL_K = "\x0b" # vertical tab


class LineKillingConsoleManhole(ConsoleManhole):
    """A console manhole that makes C-k do what you expect (kill until
    end-of-line).

    """
    def connectionMade(self):
        ConsoleManhole.connectionMade(self)
        self.keyHandlers[CTRL_K] = self._killLine


    def _killLine(self):
        self.terminal.eraseToLineEnd()
        del self.lineBuffer[self.lineBufferIndex:]



class Protocol(LineKillingConsoleManhole):
    ps = "(Crypto101) >>> ", "(Crypto101) ... "

    def __init__(self):
        LineKillingConsoleManhole.__init__(self)

        self.namespace = namespace = OrderedDict({"manhole": self})
        for f in consoleFunctions:
            partiallyApplied = partial(f, namespace=namespace)
            namespace[f.__name__] = update_wrapper(partiallyApplied, f)


    def connectionMade(self):
        """Does ``LineKillingConsoleManhole``'s connection made routine, then
        starts a session.

        """
        LineKillingConsoleManhole.connectionMade(self)
        self._startSession()


    def _startSession(self):
        """Clears terminal, writes a MOTD, and draws the input line.

        """
        self.terminal.eraseDisplay()
        self.terminal.cursorHome()
        self.terminal.write(MOTD)

        self.terminal.write("\nThe following commands are available:\n")

        table = Texttable()
        table.header(["Command", "Description"])
        for name, obj in self.namespace.iteritems():
            if obj is self:
                continue
            shortDoc = _extractFirstParagraphOfDocstring(obj)

            command = "{}({})".format(name, ", ".join(_extractArgs(obj.func)))
            table.add_row([command, shortDoc])

        # Ugh! I'm only giving Texttable bytes; why is it giving me unicode?
        self.terminal.write(table.draw().encode("utf-8"))

        self.terminal.nextLine()
        self.terminal.nextLine()

        self.drawInputLine()


    def writeLine(self, line):
        """
        Writes a line to the terminal, and then redraws the input line.
        """
        self.terminal.eraseToLineBeginning()
        self.terminal.write(line)
        self.terminal.nextLine()
        self.drawInputLine()



MOTD = """
Welcome to the Crypto 101 console client!

"""


def _extractFirstParagraphOfDocstring(f):
    """Extracts the first paragraph of the docstring of the given
    function.

    Also fixes extraneous whitespace due to indentation.
    """
    firstParagraph = f.__doc__.split("\n\n", 1)[0]
    lines = [line.strip() for line in firstParagraph.split("\n")]
    return " ".join(lines)


def _extractArgs(f):
    """Extracts all mandatory args of the function, minus the "namespace" argument.

    """
    spec = getargspec(f)
    if spec.defaults is not None: # Chop off all of the optional args
        mandatory = spec.args[:-len(spec.defaults)]
    else: # There are no optional args, so all args are mandatory
        mandatory = spec.args
    return tuple(a for a in mandatory if a != "namespace")
