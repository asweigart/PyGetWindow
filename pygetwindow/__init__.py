# PyGetWindow
# A cross-platform module to find information about the windows on the screen.

# Work in progress

# Useful info:
#https://stackoverflow.com/questions/373020/finding-the-current-active-window-in-mac-os-x-using-python
#https://stackoverflow.com/questions/7142342/get-window-position-size-with-python


"""
Features:
get foreground/focused window
get window by xy or caption title
get all windows
get list of all caption titles
maximize window
minimize window
maximize window to left half of screen
maximize window to right half of screen
close window
resize window
move window
focus window
get/click menu (win32: GetMenuItemCount, GetMenuItemInfo, GetMenuItemID, GetMenu, GetMenuItemRect)
"""


# constants
MINIMIZED = 'minimized'
MAXIMIZED = 'maximized'

FOCUSED = 'focused'
UNFOCUSED = 'unfocused'

CLOSED = 'closed'

def getWindow(xOrCaption=None, y=None):
    """Returns a Window object

    Args:
      x (int, optional): The x position of the window(s).
      y (int, optional): The y position of the window(s)."""

    if type(xOrCaption) == str:
        caption = xOrCaption
        x = None
    else:
        x = xOrCaption
        caption = None


def getWindows():
    """Returns all windows"""
    pass


# NOTE - YES, I *do* want an OOP approach here.

class Window():
    def __init__(self):
        self.caption = self.title = None
        self.state = None # one of: MINIMIZED, MAXIMIZED, FOCUSED, UNFOCUSED, CLOSED
        self.size = None
        self.topleft = None # have all the other rect properties

    def close(self):
        pass

    def minimize(self):
        pass

    def maximize(self):
        pass

    def restore(self):
        # when called on a minimized or maximized window, resizes to normal state
        pass

    def resize(self):
        pass

    def move(self):
        pass


    # TODO: Wait, come up with a better scheme. If a window is Maximized, is not focused AND not unfocused?

    def isMinimized(self):
        return self.state == MINIMIZED

    def isMaximized(self):
        return self.state == MAXIMIZED

    def isFocused(self):
        return self.state == FOCUSED

    def isUnfocused(self):
        return self.state == UNFOCUSED

    def isClosed(self):
        return self.state == CLOSED

    """Additionally, have something that lets you read the menus or click them."""



    # Getter and setter methods for properties
    def _propGetState(self):
        return self._state

    def _propSetState(self, rate):
        rate = float(rate)
        if rate < 0:
            raise ValueError('rate must be greater than 0.')
        self._rate = rate

    rate = property(_propGetRate, _propSetRate)