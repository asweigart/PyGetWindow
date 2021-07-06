#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import platform
import time
import Xlib.X
import Xlib.display
import ewmh
import pyautogui
from pygetwindow import PyGetWindowException, pointInRect, BaseWindow, Rect, Point, Size

DISP = Xlib.display.Display()
ROOT = DISP.screen().root
EWMH = ewmh.EWMH(_display=DISP, root=ROOT)

# WARNING: Changes are not immediately applied, specially for hide/show (unmap/map)
#          You may choose to wait in case you need to effectively know if/when change has been applied.
WAIT_ATTEMPTS = 10
WAIT_DELAY = 0.025  # Will be progressively increased on every retry

# These _NET_WM_STATE_ constants are used to manage Window state and are documented at
# https://ewmh.readthedocs.io/en/latest/ewmh.html
STATE_NULL = 0
STATE_MODAL = '_NET_WM_STATE_MODAL'
STATE_STICKY = '_NET_WM_STATE_STICKY'
STATE_MAX_VERT = '_NET_WM_STATE_MAXIMIZED_VERT'
STATE_MAX_HORZ = '_NET_WM_STATE_MAXIMIZED_HORZ'
STATE_SHADED = '_NET_WM_STATE_SHADED'
STATE_SKIP_TASKBAR = '_NET_WM_STATE_SKIP_TASKBAR'
STATE_SKIP_PAGER = '_NET_WM_STATE_SKIP_PAGER'
STATE_HIDDEN = '_NET_WM_STATE_HIDDEN'
STATE_FULLSCREEN = '_NET_WM_STATE_FULLSCREEN'
STATE_ABOVE = '_NET_WM_STATE_ABOVE'
STATE_BELOW = '_NET_WM_STATE_BELOW'
STATE_ATTENTION = '_NET_WM_STATE_DEMANDS_ATTENTION'
STATE_FOCUSED = '_NET_WM_STATE_FOCUSED'

# EWMH/Xlib set state actions
ACTION_UNSET = 0   # Add state
ACTION_SET = 1     # Remove state
ACTION_TOGGLE = 2  # Toggle state

# EWMH/Xlib State Hints
HINT_STATE_WITHDRAWN = 0
HINT_STATE_NORMAL = 1
HINT_STATE_ICONIC = 3


def getActiveWindow():
    """Returns a Window object of the currently active Window or None."""

    win_id = EWMH.getActiveWindow()
    if win_id:
        return LinuxWindow(win_id)
    else:
        return None


def getActiveWindowTitle():
    """Returns a string of the title text of the currently active (focused) Window."""

    win = getActiveWindow()
    if win:
        return win.title
    else:
        return ""


def getWindowsAt(x, y):
    """Returns a list of Window objects whose windows contain the point ``(x, y)``.

    * ``x`` (int): The x position of the window(s).
    * ``y`` (int): The y position of the window(s)."""
    windowsAtXY = []
    for win in getAllWindows():
        if pointInRect(x, y, win.left, win.top, win.width, win.height):
            windowsAtXY.append(win)
    return windowsAtXY


def getWindowsWithTitle(title):
    """Returns a Window object list with the given name."""

    matches = []
    for win in getAllWindows():
        if win.title == title:
            matches.append(win)

    return matches


def getAllTitles():
    """Returns a list of strings of window titles for all visible windows."""
    return [window.title for window in getAllWindows()]


def getAllWindows():
    """Returns a list of strings of window titles for all visible windows."""
    return [LinuxWindow(window) for window in EWMH.getClientList()]


class LinuxWindow(BaseWindow):

    def __init__(self, hWnd):
        self._hWnd = hWnd
        self._setupRectProperties()
        # Store initial Window parameters to allow reset and other actions
        self._saveWindowInitValues()

    def _get_frame(self, hWnd):
        """Returns the last ancestor (before root) of a given window."""
        # https://stackoverflow.com/questions/12775136/get-window-position-and-size-in-python-with-xlib - mgalgs
        frame = hWnd
        while frame.query_tree().parent != ROOT:
            frame = frame.query_tree().parent
        return frame

    def _getWindowRect(self):
        """Returns a rect of window position and size (left, top, right, bottom).
        It follows ctypes format for compatibility"""
        # https://stackoverflow.com/questions/12775136/get-window-position-and-size-in-python-with-xlib - mgalgs
        win = self._hWnd
        geom = win.get_geometry()
        (x, y) = (geom.x, geom.y)
        while True:
            parent = win.query_tree().parent
            pgeom = parent.get_geometry()
            x += pgeom.x
            y += pgeom.y
            if parent.id == ROOT.id:
                break
            win = parent
        return Rect(x, y, x + geom.width, y + geom.height)

    def _saveWindowInitValues(self):
        """Saves initial rect values to allow reset to original
        position, size, state and hints."""
        self._init_left, self._init_top, self._init_right, self._init_bottom = self._getWindowRect()
        self._init_width = self._init_right - self._init_left
        self._init_height = self._init_bottom - self._init_top
        self._init_state = self._hWnd.get_wm_state()
        self._init_hints = self._hWnd.get_wm_hints()
        self._init_normal_hints = self._hWnd.get_wm_normal_hints()
        # self._init_attributes = self._hWnd.get_attributes()  # can't be modified, so not saving it

    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)

    def __eq__(self, other):
        return isinstance(other, LinuxWindow) and self._hWnd == other._hWnd

    def close(self):
        """Closes this window. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from actually
        closing. This is identical to clicking the X button on the window."""
        EWMH.setCloseWindow(self._hWnd)
        EWMH.display.flush()

    def _get_wm(self):
        # https://stackoverflow.com/questions/3333243/how-can-i-check-with-python-which-window-manager-is-running
        return os.environ.get('XDG_CURRENT_DESKTOP') or ""

    def minimize(self, wait=False):
        """Minimizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        if not self.isMinimized:
            if "GNOME" in self._get_wm():
                # Temporary hack.
                self.activate(wait=True)
                pyautogui.hotkey('winleft', 'h')
                retries = 0
                while wait and retries < WAIT_ATTEMPTS and not self.isMinimized:
                    retries += 1
                    time.sleep(WAIT_DELAY * retries)
            else:
                # This is working OK at least on Mint/Cinnamon and Raspbian/LXDE
                hints = self._hWnd.get_wm_hints()
                prev_state = hints["initial_state"]
                hints["initial_state"] = HINT_STATE_ICONIC
                self._hWnd.set_wm_hints(hints)
                self.hide(wait=wait)
                self.show(wait=wait)
                hints["initial_state"] = prev_state
                self._hWnd.set_wm_hints(hints)
        return self.isMinimized

    def maximize(self, wait=False):
        """Maximizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        if not self.isMaximized:
            EWMH.setWmState(self._hWnd, ACTION_SET, STATE_MAX_VERT, STATE_MAX_HORZ)
            EWMH.display.flush()
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and not self.isMaximized:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return self.isMaximized

    def restore(self, wait=False):
        """If maximized or minimized, restores the window to it's normal size.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        # Activation is enough to restore a minimized window in GNOME/Unity, CINNAMON and LXDE
        self.activate(wait=wait)
        if self.isMaximized:
            EWMH.setWmState(self._hWnd, ACTION_UNSET, STATE_MAX_VERT, STATE_MAX_HORZ)
            EWMH.display.flush()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and (self.isMaximized or self.isMinimized):
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return not self.isMaximized and not self.isMinimized

    def hide(self, wait=False):
        """If hidden or showing, hides the window from screen and title bar.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        win = DISP.create_resource_object('window', self._hWnd)
        win.unmap_sub_windows()
        DISP.sync()
        win.unmap()
        DISP.sync()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return not self._isMapped

    def show(self, wait=False):
        """If hidden or showing, shows the window on screen and in title bar.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        win = DISP.create_resource_object('window', self._hWnd)
        win.map()
        DISP.sync()
        win.map_sub_windows()
        DISP.sync()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self._isMapped

    def activate(self, wait=False):
        """Activate this window and make it the foreground (focused) window.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        if "arm" in platform.platform():
            EWMH.setWmState(self._hWnd, ACTION_SET, STATE_ABOVE, STATE_NULL)
        else:
            EWMH.setActiveWindow(self._hWnd)
        EWMH.display.flush()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self.isActive:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.isActive

    def resize(self, widthOffset, heightOffset, wait=False):
        """Resizes the window relative to its current size.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        return self.resizeTo(self.width + widthOffset, self.height + heightOffset, wait)

    resizeRel = resize  # resizeRel is an alias for the resize() method.

    def resizeTo(self, newWidth, newHeight, wait=False):
        """Resizes the window to a new width and height.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        EWMH.setMoveResizeWindow(self._hWnd, x=self.left, y=self.top, w=newWidth, h=newHeight)
        EWMH.display.flush()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and (self.width != newWidth or self.height != newHeight):
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.width == newWidth and self.height == newHeight

    def move(self, xOffset, yOffset, wait=False):
        """Moves the window relative to its current position.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        return self.moveTo(self.left + xOffset, self.top + yOffset, wait)

    moveRel = move  # moveRel is an alias for the move() method.

    def moveTo(self, newLeft, newTop, wait=False):
        """Moves the window to new coordinates on the screen.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        if newLeft < 0 or newTop < 0:  # Xlib/EWMH won't accept negative positions
            return False
        EWMH.setMoveResizeWindow(self._hWnd, x=newLeft, y=newTop, w=self.width, h=self.height)
        EWMH.display.flush()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and (self.left != newLeft or self.top != newTop):
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.left == newLeft and self.top == newTop

    def _moveResizeTo(self, newLeft, newTop, newWidth, newHeight, wait=False):
        if newLeft < 0 or newTop < 0:  # Xlib/EWMH won't accept negative positions
            return False
        EWMH.setMoveResizeWindow(self._hWnd, x=newLeft, y=newTop, w=newWidth, h=newHeight)
        EWMH.display.flush()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and (self.left != newLeft or self.top != newTop):
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.left == newLeft and self.top == newTop

    @property
    def isMinimized(self):
        """Returns ``True`` if the window is currently minimized."""
        return STATE_HIDDEN in EWMH.getWmState(self._hWnd, str=True)

    @property
    def isMaximized(self):
        """Returns ``True`` if the window is currently maximized."""
        state = EWMH.getWmState(self._hWnd, str=True)
        return STATE_MAX_VERT in state and STATE_MAX_HORZ in state

    @property
    def isActive(self):
        """Returns ``True`` if the window is currently the active, foreground window."""
        return EWMH.getActiveWindow() == self._hWnd

    @property
    def title(self):
        """Returns the window title as a string."""
        return EWMH.getWmName(self._hWnd)

    @property
    def visible(self):
        """Return ``True`` if the window is currently visible."""
        win = DISP.create_resource_object('window', self._hWnd)
        return win.get_attributes().map_state == Xlib.X.IsViewable

    @property
    def _isMapped(self):
        """Return ``True`` if the window is currently mapped."""
        win = DISP.create_resource_object('window', self._hWnd)
        return win.get_attributes().map_state != Xlib.X.IsUnmapped


def cursor():
    """Returns the current xy coordinates of the mouse cursor as a two-integer tuple

    Returns:
      (x, y) tuple of the current xy coordinates of the mouse cursor.
    """
    mp = ROOT.query_pointer()
    return Point(mp.root_x, mp.root_y)


def resolution():
    """Returns the width and height of the screen as a two-integer tuple.

    Returns:
      (width, height) tuple of the screen size, in pixels.
    """
    res = EWMH.getDesktopGeometry()
    return Size(res[0], res[1])


def displayWindowsUnderMouse(xOffset=0, yOffset=0):
    """This function is meant to be run from the command line. It will
    automatically show mouse pointer position and windows names under it"""
    if xOffset != 0 or yOffset != 0:
        print('xOffset: %s yOffset: %s' % (xOffset, yOffset))
    try:
        prevWindows = None
        while True:
            x, y = cursor()
            positionStr = 'X: ' + str(x - xOffset).rjust(4) + ' Y: ' + str(y - yOffset).rjust(4) + '  (Press Ctrl-C to quit)'
            if prevWindows is not None:
                sys.stdout.write(positionStr)
                sys.stdout.write('\b' * len(positionStr))
            windows = getWindowsAt(x, y)
            if windows != prevWindows:
                print('\n')
                prevWindows = windows
                for win in windows:
                    name = win.title
                    eraser = '' if len(name) >= len(positionStr) else ' ' * (len(positionStr) - len(name))
                    sys.stdout.write(name + eraser + '\n')
            sys.stdout.flush()
            time.sleep(0.3)
    except KeyboardInterrupt:
        sys.stdout.write('\n\n')
        sys.stdout.flush()


def main():
    """Run this script from command-line to get windows under mouse pointer"""
    print("PLATFORM:", sys.platform)
    print("SCREEN SIZE:", resolution())
    npw = getActiveWindow()
    print("ACTIVE WINDOW:", npw.title, "/", npw.box)
    print("")
    displayWindowsUnderMouse(0, 0)


if __name__ == "__main__":
    main()
