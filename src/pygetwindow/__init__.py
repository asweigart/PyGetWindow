# PyGetWindow
# A cross-platform module to find information about the windows on the screen.

"""

# Work in progress

# Useful info:
#https://stackoverflow.com/questions/373020/finding-the-current-active-window-in-mac-os-x-using-python
#https://stackoverflow.com/questions/7142342/get-window-position-size-with-python


win32 api and ctypes on Windows
cocoa api and pyobjc on Mac
Xlib on linux


Possible Future Features:
get/click menu (win32: GetMenuItemCount, GetMenuItemInfo, GetMenuItemID, GetMenu, GetMenuItemRect)
"""

__version__ = '0.0.7'

import sys
import collections


class PyGetWindowException(Exception):
    pass


def pointInRect(x, y, left, top, width, height):
    return left < x < left + width and top < y < top + height


if sys.platform == 'darwin':
    raise NotImplementedError('PyGetWindow currently does not support macOS. If you have Appkit/Cocoa knowledge, please contribute! https://github.com/asweigart/pygetwindow') # TODO - implement mac
elif sys.platform == 'win32':
    from ._pygetwindow_win import Win32Window, getActiveWindow, getActiveWindowTitle, getWindowsAt, getWindowsWithTitle, getAllWindows, getAllTitles
    Window = Win32Window
else:
    raise NotImplementedError('PyGetWindow currently does not support Linux. If you have Xlib knowledge, please contribute! https://github.com/asweigart/pygetwindow')


# NOTE: `Rect` is a named tuple for use in Python, while structs.RECT represents
# the win32 RECT struct. PyRect's Rect class is used for handling changing
# geometry of rectangular areas.
Rect = collections.namedtuple('Rect', 'left top right bottom')
Point = collections.namedtuple('Point', 'x y')
Size = collections.namedtuple('Size', 'width height')