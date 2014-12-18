# PyGetWindow
# A cross-platform module to find information about the windows on the screen.

# Work in progress

# Useful info:
#https://stackoverflow.com/questions/373020/finding-the-current-active-window-in-mac-os-x-using-python
#https://stackoverflow.com/questions/7142342/get-window-position-size-with-python

def locateWindow():
    """Parameters can be partial caption match, window at an x, y or (x, y) point."""

def locateWindows():
    """Parameters can be partial caption match, window at an x, y or (x, y) point, or all windows in a region."""

class Window():
    MINIMIZED = 'minimized'
    MAXIMIZED = 'maximized'

    def __init__(self):
        self.caption = self.title = None
        self.state = None
        self.size = None
        self.topleft = None # have all the other rect properties

    def close(self):
        pass

    def minimize(self):
        pass

    def maximize(self):
        pass

    def resize(self):
        pass

    def move(self):
        pass

    """Additionally, have something that lets you read the menus or click them."""