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

__version__ = '0.0.1'

import sys



class PyGetWindowException(Exception):
    pass


def pointInRect(x, y, left, top, width, height):
    return left < x < left + width and top < y < top + height


if sys.platform == 'darwin':
    raise NotImplementedError() # TODO - implement mac
elif sys.platform == 'win32':
    from ._pygetwindow_win import Win32Window, getFocusedWindow, getWindowsAt, getWindowsWithTitle, getAllWindows, getAllTitles
    Window = Win32Window
else:
    raise NotImplementedError() # TODO - implement linux
