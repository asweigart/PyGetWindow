import collections
import ctypes
from ctypes import wintypes # We can't use ctypes.wintypes, we must import wintypes this way.

import pygetwindow

NULL = 0 # Used to match the Win32 API value of "null".

# These FORMAT_MESSAGE_ constants are used for FormatMesage() and are
# documented at https://docs.microsoft.com/en-us/windows/desktop/api/winbase/nf-winbase-formatmessage#parameters
FORMAT_MESSAGE_ALLOCATE_BUFFER = 0x00000100
FORMAT_MESSAGE_FROM_SYSTEM = 0x00001000
FORMAT_MESSAGE_IGNORE_INSERTS = 0x00000200

# These SW_ constants are used for ShowWindow() and are documented at
# https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-showwindow#parameters
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9

# SetWindowPos constants:
HWND_TOP = 0

# Window Message constants:
WM_CLOSE = 0x0010


enumWindows = ctypes.windll.user32.EnumWindows
enumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
getWindowText = ctypes.windll.user32.GetWindowTextW
getWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
isWindowVisible = ctypes.windll.user32.IsWindowVisible



# NOTE: `Rect` is a named tuple for use in Python, while structs.RECT represents
# the win32 RECT struct.
Rect = collections.namedtuple('Rect', 'left top right bottom')


class RECT(ctypes.Structure):
    """A nice wrapper of the RECT structure.

    Microsoft Documentation:
    https://msdn.microsoft.com/en-us/library/windows/desktop/dd162897(v=vs.85).aspx
    """
    _fields_ = [('left', ctypes.c_long),
                ('top', ctypes.c_long),
                ('right', ctypes.c_long),
                ('bottom', ctypes.c_long)]


def _getAllTitles():
    # This code taken from https://sjohannes.wordpress.com/2012/03/23/win32-python-getting-all-window-titles/
    # A correction to this code (for enumWindowsProc) is here: http://makble.com/the-story-of-lpclong
    titles = []
    def foreach_window(hWnd, lParam):
        if isWindowVisible(hWnd):
            length = getWindowTextLength(hWnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            getWindowText(hWnd, buff, length + 1)
            titles.append((hWnd, buff.value))
        return True
    enumWindows(enumWindowsProc(foreach_window), 0)

    return titles


def _formatMessage(errorCode):
    """A nice wrapper for FormatMessageW(). TODO

    Microsoft Documentation:
    https://docs.microsoft.com/en-us/windows/desktop/api/winbase/nf-winbase-formatmessagew

    Additional information:
    https://stackoverflow.com/questions/18905702/python-ctypes-and-mutable-buffers
    https://stackoverflow.com/questions/455434/how-should-i-use-formatmessage-properly-in-c
    """
    lpBuffer = wintypes.LPWSTR()

    ctypes.windll.kernel32.FormatMessageW(FORMAT_MESSAGE_FROM_SYSTEM | FORMAT_MESSAGE_ALLOCATE_BUFFER | FORMAT_MESSAGE_IGNORE_INSERTS,
                                          NULL,
                                          errorCode,
                                          0, # dwLanguageId
                                          ctypes.cast(ctypes.byref(lpBuffer), wintypes.LPWSTR),
                                          0, # nSize
                                          NULL)
    msg = lpBuffer.value.rstrip()
    ctypes.windll.kernel32.LocalFree(lpBuffer) # Free the memory allocated for the error message's buffer.
    return msg


def _raiseWithLastError():
    """A helper function that raises PyGetWindowException using the error
    information from GetLastError() and FormatMessage()."""
    errorCode = ctypes.windll.kernel32.GetLastError()
    raise pygetwindow.PyGetWindowException('Error code from Windows: %s - %s' % (errorCode, _formatMessage(errorCode)))


def _getWindowRect(hWnd):
    """A nice wrapper for GetWindowRect(). TODO

    Syntax:
    BOOL GetWindowRect(
      HWND   hWnd,
      LPRECT lpRect
    );

    Microsoft Documentation:
    https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-getwindowrect
    """
    rect = RECT()
    result = ctypes.windll.user32.GetWindowRect(hWnd, ctypes.byref(rect))
    if result != 0:
        return Rect(rect.left, rect.top, rect.right, rect.bottom)
    else:
        _raiseWithLastError()


def _getWindowText(hWnd):
    """A wrapper for the GetWindowTextW() win api. TODO

    Syntax:
    int GetWindowTextW(
      HWND   hWnd,
      LPWSTR lpString,
      int    nMaxCount
    );

    int GetWindowTextLengthW(
      HWND hWnd
    );

    Microsoft Documentation:
    https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-getwindowtextw
    https://docs.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-getwindowtextlengthw
    """
    textLenInCharacters = ctypes.windll.user32.GetWindowTextLengthW(hWnd)
    stringBuffer = ctypes.create_unicode_buffer(textLenInCharacters + 1) # +1 for the \0 at the end of the null-terminated string.
    ctypes.windll.user32.GetWindowTextW(hWnd, stringBuffer, textLenInCharacters + 1)

    # TODO it's ambiguous if an error happened or the title text is just empty. Look into this later.
    return stringBuffer.value


def getFocusedWindow():
    """Returns a Window object of the currently focused Window."""
    hWnd = ctypes.windll.user32.GetForegroundWindow()
    if hWnd == 0:
        # TODO - raise error instead
        return None # Note that this function doesn't use GetLastError().
    else:
        return Win32Window(hWnd)


def getWindowsAt(x, y):
    """Returns a tuple of Window objects

    Args:
      x (int, optional): The x position of the window(s).
      y (int, optional): The y position of the window(s)."""
    windowsAtXY = []
    for window in getAllWindows():
        if pygetwindow.pointInRect(x, y, window.left, window.top, window.width, window.height):
            windowsAtXY.append(window)
    return tuple(windowsAtXY)


def getWindowsWithTitle(title):
    """Returns a tuple of Window objects that substring match the title.
    """
    hWndsAndTitles = _getAllTitles()
    windowObjs = []
    for hWnd, winTitle in hWndsAndTitles:
        if title.upper() in winTitle.upper(): # do a case-insensitive match
            windowObjs.append(Win32Window(hWnd))
    return tuple(windowObjs)


def getAllTitles():
    """Returns a tuple of strings of window titles for all visible windows.
    """
    return tuple([window.title for window in getAllWindows()])


def getAllWindows():
    """Returns a tuple of Window objects for all visible windows.
    """
    windowObjs = []
    def foreach_window(hWnd, lParam):
        if ctypes.windll.user32.IsWindowVisible(hWnd) != 0:
            windowObjs.append(Win32Window(hWnd))
        return True
    enumWindows(enumWindowsProc(foreach_window), 0)

    return tuple(windowObjs)


# NOTE - YES, I *do* want an OOP approach here.

class Win32Window():
    def __init__(self, hWnd):
        self._hWnd = hWnd # TODO fix this, this is a LP_c_long insead of an int.

    def __str__(self):
        r = _getWindowRect(self._hWnd)
        width = r.right - r.left
        height = r.bottom - r.top
        return '<%s left="%s", top="%s", width="%s", height="%s", title="%s">' % (self.__class__.__name__, r.left, r.top, width, height, self.title)


    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)


    def __eq__(self, other):
        return isinstance(other, Win32Window) and self._hWnd == other._hWnd


    def close(self):
        result = ctypes.windll.user32.PostMessageA(self._hWnd, WM_CLOSE, 0, 0)
        if result == 0:
            _raiseWithLastError()


    def minimize(self):
        ctypes.windll.user32.ShowWindow(self._hWnd, SW_MINIMIZE)


    def maximize(self):
        ctypes.windll.user32.ShowWindow(self._hWnd, SW_MAXIMIZE)


    def restore(self):
        # when called on a minimized or maximized window, resizes to normal state
        ctypes.windll.user32.ShowWindow(self._hWnd, SW_RESTORE)


    def focus(self):
        result = ctypes.windll.user32.SetForegroundWindow(self._hWnd)
        if result == 0:
            _raiseWithLastError()


    def resize(self, widthOffset, heightOffset):
        result = ctypes.windll.user32.SetWindowPos(self._hWnd, HWND_TOP, self.left, self.top, self.width + widthOffset, self.height + heightOffset, 0)
        if result == 0:
            _raiseWithLastError()


    def resizeTo(self, newWidth, newHeight):
        result = ctypes.windll.user32.SetWindowPos(self._hWnd, HWND_TOP, self.left, self.top, newWidth, newHeight, 0)
        if result == 0:
            _raiseWithLastError()


    def move(self, xOffset, yOffset):
        result = ctypes.windll.user32.SetWindowPos(self._hWnd, HWND_TOP, self.left + xOffset, self.top + yOffset, self.width, self.height, 0)
        if result == 0:
            _raiseWithLastError()


    def moveTo(self, newLeft, newTop):
        result = ctypes.windll.user32.SetWindowPos(self._hWnd, HWND_TOP, newLeft, newTop, self.width, self.height, 0)
        if result == 0:
            _raiseWithLastError()


    @property
    def isMinimized(self):
        return ctypes.windll.user32.IsIconic(self._hWnd) != 0

    @property
    def isMaximized(self):
        return ctypes.windll.user32.IsZoomed(self._hWnd) != 0

    @property
    def isFocused(self):
        return getFocusedWindow() == self

    @property
    def isUnfocused(self):
        return getFocusedWindow() != self

    @property
    def title(self):
        return _getWindowText(self._hWnd)


    @property
    def width(self):
        r = _getWindowRect(self._hWnd)
        return r.right - r.left

    @property
    def height(self):
        r = _getWindowRect(self._hWnd)
        return r.bottom - r.top

    @property
    def size(self):
        r = _getWindowRect(self._hWnd)
        return (r.right - r.left, r.bottom - r.top) # Returns (width, height)

    @property
    def topleft(self):
        r = _getWindowRect(self._hWnd)
        return (r.left, r.top)

    @property
    def topright(self):
        r = _getWindowRect(self._hWnd)
        return (r.right, r.top)

    @property
    def bottomleft(self):
        r = _getWindowRect(self._hWnd)
        return (r.left, r.bottom)

    @property
    def bottomright(self):
        r = _getWindowRect(self._hWnd)
        return (r.right, r.bottom)

    @property
    def top(self):
        return _getWindowRect(self._hWnd).top

    @property
    def bottom(self):
        return _getWindowRect(self._hWnd).bottom

    @property
    def left(self):
        return _getWindowRect(self._hWnd).left

    @property
    def right(self):
        return _getWindowRect(self._hWnd).right

