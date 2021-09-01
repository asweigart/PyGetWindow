#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys
import time
from AppKit import *
import Quartz
from pygetwindow import PyGetWindowException, pointInRect, BaseWindow, Rect, Point, Size

""" 
IMPORTANT NOTICE:
    There aren't many mechanisms to manage other apps/windows on MacOS, so this is based mainly on Apple Scripts.
    For non-scriptable apps, so some methods and properties might not work.
    The rest of methods should work fine in most cases. 
    In case you need full-support, granting your application in Accessibility options could fix it (or not)
"""

WS = NSWorkspace.sharedWorkspace()
# WARNING: Changes are not immediately applied nor updated on stored window object
#          Activate wait option if you need to effectively know if/when action has been performed
WAIT_ATTEMPTS = 10
WAIT_DELAY = 0.025  # Will be progressively increased on every retry


def getActiveWindow(app=None):
    """Returns a Window object of the currently active Window or None."""
    if not app:
        app = WS.frontmostApplication()
        windows = _getAllAppWindows(app)
        for win in windows:
            if win[Quartz.kCGWindowLayer] == 0:
                return MacOSWindow(app, win)
    else:
        for win in getAllWindows(app):  # .keyWindow() not working?!?!?!
            return MacOSNSWindow(app, win)
    return None


def getActiveWindowTitle(app=None):
    """Returns a Window object of the currently active Window or empty string."""
    win = getActiveWindow(app)
    if win:
        return win.title
    else:
        return ""


def getWindowsAt(x, y, app=None):
    """Returns a list of windows under the mouse pointer or an empty list."""
    matches = []
    for win in getAllWindows(app):
        if pointInRect(x, y, win.left, win.top, win.width, win.height):
            matches.append(win)
    return matches


def getWindowsWithTitle(title, app=None):
    """Returns a list of window objects matching the given title or an empty list."""
    # DOUBT: Should the "owner" name (app to which the window belongs to) be included?
    windows = []
    if not app:
        # On Catalina, WindowInfo objects do not include kCGWindowName, so this ugly hack is required
        activeApps = _getAllApps()
        appwindows = _getAllWindows(app)
        for app in activeApps:
            for win in appwindows:
                if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerPID] == app.processIdentifier():
                    name = win.get(Quartz.kCGWindowName, "")
                    if not name:
                        found = _getWindowByTitle(win[Quartz.kCGWindowOwnerName], title)
                        if found:
                            name = title
                    if name == title:
                        windows.append(MacOSWindow(app, win, title))
    else:
        for win in app.orderedWindows():
            w = MacOSWindow(app, win)
            if w.title == title:
                windows.append(w)
    return windows


def _getWindowByTitle(appName, title):
    cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                set found to false
                                try
                                    perform action "AXRaise" of (first window whose name is "%s")
                                    set found to true
                               end try
                            end tell
                            return (found as string)'""" % (appName, title)
    ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
    return ret == "true"


def getAllTitles(app=None):
    """Returns a list of strings of window titles for all visible windows."""
    return [win.title for win in getAllWindows(app)]


def getAllWindows(app=None):
    """Returns a list of window objects for all visible windows."""
    # It is restricted to layer 0, which should be the "user layer"
    windows = []
    if not app:
        activeApps = _getAllApps()
        appwindows = _getAllWindows(app)
        for app in activeApps:
            for win in appwindows:
                if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerPID] == app.processIdentifier():
                    windows.append(MacOSWindow(app, win))
    else:
        for win in app.orderedWindows():
            windows.append(MacOSNSWindow(app, win))
    return windows


def _getActiveWindow(app=None):
    # Source: https://stackoverflow.com/questions/53237266/how-can-i-minimize-maximize-windows-in-macos-with-the-cocoa-api-from-a-python-sc
    activeApps = _getAllApps()
    windows = _getAllWindows()
    for app in activeApps:
        if app.isActive():
            for win in windows:
                if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerPID] == app.processIdentifier():
                    return MacOSWindow(app, win)
    return None


def _getAllApps():
    return WS.runningApplications()


def _getAllWindows(excludeDesktop=True, screenOnly=True):
    flags = Quartz.kCGWindowListExcludeDesktopElements if excludeDesktop else 0 | \
            Quartz.kCGWindowListOptionOnScreenOnly if screenOnly else 0
    return Quartz.CGWindowListCopyWindowInfo(flags, Quartz.kCGNullWindowID)


def _getAllAppWindows(app):
    windows = _getAllWindows(screenOnly=False)
    windowsInApp = []
    for win in windows:
        if win[Quartz.kCGWindowOwnerPID] == app.processIdentifier():
            windowsInApp.append(win)
    return windowsInApp


class MacOSWindow(BaseWindow):

    def __init__(self, app, hWnd, title=""):
        self._app = app
        self._hWnd = hWnd
        if not title:
            title = self.altTitle()
        self.Title = title
        self._setupRectProperties()

    def _getWindowRect(self):
        """Returns a rect of window position and size (left, top, right, bottom).
        It follows ctypes format for compatibility"""
        cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                    set winName to "%s" 
                                    set appPos to (get position of first window whose name is winName)
                                    set appSize to (get size of first window whose name is winName)
                                    set appBounds to {appPos, appSize}
                                end tell
                                return appBounds'""" % (self._app.localizedName(), self.title)
        w = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip().split(", ")
        return Rect(int(w[0]), int(w[1]), int(w[0]) + int(w[2]), int(w[1]) + int(w[3]))

    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)

    def __eq__(self, other):
        return isinstance(other, MacOSNSWindow) and self._hWnd == other._hWnd

    def close(self, close_parent=False):
        """Closes this window or app. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from actually
        closing. This is identical to clicking the X button on the window."""
        if close_parent:
            self._app.terminate()
        else:
            cmd = """osascript -e 'tell application "%s" to close (first window whose name is "%s")'""" % \
                  (self._app.localizedName(), self.title)
            os.system(cmd)

    def minimize(self, wait=False):
        """Minimizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was minimized"""
        # https://apple.stackexchange.com/questions/35189/is-there-a-way-to-minimize-open-windows-from-the-command-line-in-os-x-lion
        if not self.isMinimized:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s" 
                                        try
                                            set value of attribute "AXMinimized" of (first window whose name is "%s") to true
                                        end try
                                    end tell'""" % (self._app.localizedName(), self.title)
            os.system(cmd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and not self.isMinimized:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return self.isMinimized

    def maximize(self, wait=False, force=False):
        """Maximizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was maximized"""
        # Thanks to: macdeport (for this piece of code, his help, and the moral support!!!)
        if not self.isMaximized:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s" 
                                        try
                                            set value of attribute "AXFullScreen" of (first window whose name is "%s") to true
                                        end try
                                    end tell'""" % (self._app.localizedName(), self.title)
            os.system(cmd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and not self.isMaximized:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return self.isMaximized

    def restore(self, wait=False):
        """If maximized or minimized, restores the window to it's normal size.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was restored"""
        self.activate(wait=True)
        if self.isMaximized:
            cmd = """osascript -e 'tell application "System Events" to tell process "%s" 
                                        try
                                            set value of attribute "AXFullScreen" of window 1 to false
                                        end try
                                    end tell'""" % self._app.localizedName()
            os.system(cmd)
        if self.isMinimized:
            cmd = """osascript -e 'tell application "System Events" to tell process "%s" 
                                        try
                                            set value of attribute "AXMinimized" of (first window whose name is "%s") to false
                                        end try
                                    end tell'""" % (self._app.localizedName(), self.title)
            os.system(cmd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and (self.isMinimized or self.isMaximized):
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return not self.isMaximized and not self.isMinimized

    def hide(self, wait=False):
        """If hidden or showing, hides the app from screen and title bar.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was hidden (unmapped)"""
        self._app.hide()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.visible:  # and self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return not self.visible

    def show(self, wait=False):
        """If hidden or showing, shows the window on screen and in title bar.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window is showing (mapped)"""
        self._app.unhide()
        self.activate(wait=wait)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self.visible:  # and not self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.visible

    def activate(self, wait=False):
        """Activate this window and make it the foreground (focused) window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was activated"""
        self._app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        # TODO: Why these two options do not work sometimes: "set index of (first window whose name is "%s") to 1"
        cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                    try
                                        perform action "AXRaise" of (first window whose name is "%s")
                                    end try
                                end tell'""" % (self._app.localizedName(), self.title)
        os.system(cmd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self.isActive:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.isActive

    def resize(self, widthOffset, heightOffset, wait=False):
        """Resizes the window relative to its current size.
        Use 'wait' option to confirm action requested (in a reasonable time)

        Returns ''True'' if window was resized to the given size
        WARNING: Will not work if target app is not scriptable"""
        return self.resizeTo(self.width + widthOffset, self.height + heightOffset, wait)

    resizeRel = resize  # resizeRel is an alias for the resize() method.

    def resizeTo(self, newWidth, newHeight, wait=False):
        """Resizes the window to a new width and height.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was resized to the given size
        WARNING: Will not work if target app is not scriptable"""
        cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                    try
                                        set size of (first window whose name is "%s") to {%i, %i}
                                    end try
                                end tell'""" % \
              (self._app.localizedName(), self.title, newWidth, newHeight)
        os.system(cmd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.width != newWidth and self.height != newHeight:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.width == newWidth and self.height == newHeight

    def move(self, xOffset, yOffset, wait=False):
        """Moves the window relative to its current position.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was moved to the given position
        WARNING: Will not work if target app is not scriptable"""
        return self.moveTo(self.left + xOffset, self.top + yOffset, wait)

    moveRel = move  # moveRel is an alias for the move() method.

    def moveTo(self, newLeft, newTop, wait=False):
        """Moves the window to new coordinates on the screen.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was moved to the given position
        WARNING: Will not work if target app is not scriptable"""
        cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                    try
                                        set position of (first window whose name is "%s") to {%i, %i}
                                    end try
                                end tell'""" % \
              (self._app.localizedName(), self.title, newLeft, newTop)
        os.system(cmd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.left != newLeft and self.top != newTop:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.left == newLeft and self.top == newTop

    def _moveResizeTo(self, newLeft, newTop, newWidth, newHeight):
        # https://stackoverflow.com/questions/16598551/os-x-move-window-from-python
        # https://apple.stackexchange.com/questions/350256/how-to-move-mac-os-application-to-specific-display-and-also-resize-automatically
        cmd = """osascript -e 'tell application "System Events" to tell application process "%s" 
                                    set winName to "%s"
                                    try
                                        set position of (first window whose name is winName) to {%i, %i}
                                    end try
                                    try
                                        set size of (first window whose name is winName) to {%i, %i}
                                    end try
                                end tell'""" % \
              (self._app.localizedName(), self.title, newLeft, newTop, newWidth, newHeight)
        os.system(cmd)
        return

    @property
    def isMinimized(self):
        """Returns ``True`` if the window is currently minimized."""
        cmd = """osascript -e 'tell application "System Events" to tell process "%s" 
                                    set isMin to false
                                    try
                                        set isMin to value of attribute "AXMinimized" of (first window whose name is "%s")
                                    end try
                                end tell
                                return (isMin as string)'""" % (self._app.localizedName(), self.title)
        ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return ret == "true"

    @property
    def isMaximized(self):
        """Returns ``True`` if the window is currently maximized (fullscreen)."""
        cmd = """osascript -e 'tell application "System Events" to tell process "%s" 
                                    set isFull to false
                                    set winName to ""
                                    try
                                        set isFull to value of attribute "AXFullScreen" of window 1
                                        if isFull then
                                            set winName to name of window 1
                                        end if
                                    end try
                                end tell
                                return (winName as string)'""" % self._app.localizedName()
        ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return ret == self.title

    @property
    def isActive(self):
        """Returns ``True`` if the window is currently the active, foreground window."""
        cmd = """osascript -e 'tell application "System Events" 
                                    set frontApp to 0
                                    try
                                        set frontApp to first application process whose frontmost is true
                                    end try
                                end tell
                                set win_name to ""
                                if frontApp is not equal to 0
                                    if frontApp is equal to "%s"
                                        tell application "System Events" to tell application process frontApp
                                            try
                                                set win_name to name of front window
                                            end try
                                        end tell
                                    end if
                                end if
                                return win_name'""" % self._app.localizedName()
        ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return ret == self.title

    def altTitle(self):
        name = self._hWnd.get(Quartz.kCGWindowName, '')
        if not name:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                        set window_name to ""
                                        try
                                            set window_name to name of window 1
                                        end try
                                    end tell
                                    return window_name'""" % self._app.localizedName()
            name = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return name

    @property
    def title(self):
        """Returns the window title as a string."""
        # Source: https://stackoverflow.com/questions/53237278/obtain-list-of-all-window-titles-on-macos-from-a-python-script/53985082#53985082
        # Should the owner (app) be added?
        # return self._hWnd.get([Quartz.kCGWindowOwnerName], '') + " - " + self._hWnd.get(Quartz.kCGWindowName, '')
        return self.Title

    @property
    def visible(self):
        """Returns ``True`` if the window is currently visible."""
        return self._isMapped and not self.isMinimized

    @property
    def _isMapped(self):
        # Returns ``True`` if the window is currently mapped (well, only if it doesn't exist... by the moment)
        cmd = """osascript -e 'tell application "System Events"
                                    set isMapped to false
                                    try
                                        set isMapped to (visible of application process "%s")
                                    end try
                                end tell
                                return isMapped'""" % self._app.localizedName()
        ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return ret == "true"
        # return not self._app.isHidden()  # Returns always 'False'


class MacOSNSWindow(BaseWindow):

    def __init__(self, app, hWnd):
        self._app = app
        self._hWnd = hWnd
        self._setupRectProperties()

    def _getWindowRect(self):
        """Returns a rect of window position and size (left, top, right, bottom).
        It follows ctypes format for compatibility"""
        frame = self._hWnd.frame()
        res = resolution()
        x = int(frame.origin.x)
        y = int(res.height) - int(frame.origin.y) - int(frame.size.height)
        w = x + int(frame.size.width)
        h = y + int(frame.size.height)
        return Rect(x, y, w, h)

    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)

    def __eq__(self, other):
        return isinstance(other, MacOSWindow) and self._hWnd == other._hWnd

    def close(self, close_parent=False):
        """Closes this window. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from actually
        closing. This is identical to clicking the X button on the window."""
        if close_parent:
            self._app.terminate()
        else:
            self._hWnd.performClose_(self._app)

    def minimize(self, wait=False):
        """Minimizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was minimized"""
        if not self.isMinimized:
            self._hWnd.performMiniaturize_(self._app)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and not self.isMinimized:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return self.isMinimized

    def maximize(self, wait=False, force=False):
        """Maximizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was maximized"""
        if not self.isMaximized:
            self._hWnd.performZoom_(self._app)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and not self.isMaximized:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return self.isMaximized

    def restore(self, wait=False):
        """If maximized or minimized, restores the window to it's normal size.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was restored"""
        self.activate(wait=True)
        if self.isMaximized:
            self._hWnd.performZoom_(self._app)
        if self.isMinimized:
            self._hWnd.deminiaturize_(self._app)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and (self.isMinimized or self.isMaximized):
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return not self.isMaximized and not self.isMinimized

    def hide(self, wait=False):
        """If hidden or showing, hides the app from screen and title bar.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was hidden (unmapped)"""
        self._app.hide()
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.visible:  # and self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return not self.visible

    def show(self, wait=False):
        """If hidden or showing, shows the window on screen and in title bar.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window is showing (mapped)"""
        self._app.unhide()
        self.activate(wait=wait)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self.visible:  # and not self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.visible

    def activate(self, wait=False):
        """Activate this window and make it the foreground (focused) window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was activated"""
        self._app.activateIgnoringOtherApps_(True)
        self._hWnd.makeKeyAndOrderFront_(self._app)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self.isActive:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.isActive

    def resize(self, widthOffset, heightOffset, wait=False):
        """Resizes the window relative to its current size.
        Use 'wait' option to confirm action requested (in a reasonable time)

        Returns ''True'' if window was resized to the given size
        WARNING: Will not work if target app is not scriptable"""
        return self.resizeTo(self.width + widthOffset, self.height + heightOffset, wait)

    resizeRel = resize  # resizeRel is an alias for the resize() method.

    def resizeTo(self, newWidth, newHeight, wait=False):
        """Resizes the window to a new width and height.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was resized to the given size
        WARNING: Will not work if target app is not scriptable"""
        self._hWnd.setFrame_display_animate_(NSMakeRect(self.bottomleft.x, self.bottomleft.y, newWidth, newHeight), True, True)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.width != newWidth and self.height != newHeight:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.width == newWidth and self.height == newHeight

    def move(self, xOffset, yOffset, wait=False):
        """Moves the window relative to its current position.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was moved to the given position
        WARNING: Will not work if target app is not scriptable"""
        return self.moveTo(self.left + xOffset, self.top + yOffset, wait)

    moveRel = move  # moveRel is an alias for the move() method.

    def moveTo(self, newLeft, newTop, wait=False):
        """Moves the window to new coordinates on the screen.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was moved to the given position
        WARNING: Will not work if target app is not scriptable"""
        self._hWnd.setFrame_display_animate_(NSMakeRect(newLeft, resolution().height - newTop - self.height, self.width, self.height), True, True)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.left != newLeft and self.top != newTop:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self.left == newLeft and self.top == newTop

    def _moveResizeTo(self, newLeft, newTop, newWidth, newHeight):
        self._hWnd.setFrame_display_animate_(NSMakeRect(newLeft, resolution().height - newTop - newHeight, newWidth, newHeight), True, True)
        return

    @property
    def isMinimized(self):
        """Returns ``True`` if the window is currently minimized."""
        return self._hWnd.isMiniaturized()

    @property
    def isMaximized(self):
        """Returns ``True`` if the window is currently maximized (fullscreen)."""
        return self._hWnd.isZoomed()

    @property
    def isActive(self):
        """Returns ``True`` if the window is currently the active, foreground window."""
        windows = getAllWindows(self._app)
        for win in windows:
            return self._hWnd == win
        return False

    @property
    def title(self):
        """Returns the window title as a string."""
        # Should the owner (app) be added?
        return self._hWnd.title()

    @property
    def visible(self):
        """Returns ``True`` if the window is currently visible."""
        return self._hWnd.isVisible()


def cursor():
    """Returns the current xy coordinates of the mouse cursor as a two-integer tuple

    Returns:
      (x, y) tuple of the current xy coordinates of the mouse cursor.
    """
    # https://stackoverflow.com/questions/3698635/getting-cursor-position-in-python/24567802
    Quartz.NSEvent.mouseLocation()
    return Point(Quartz.NSEvent.mouseLocation().x, resolution().height - Quartz.NSEvent.mouseLocation().y)


def resolution():
    """Returns the width and height of the screen as a two-integer tuple.

    Returns:
      (width, height) tuple of the screen size, in pixels.
    """
    # https://stackoverflow.com/questions/1281397/how-to-get-the-desktop-resolution-in-mac-via-python
    mainMonitor = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    return Size(mainMonitor.size.width, mainMonitor.size.height)


def displayWindowsUnderMouse(xOffset=0, yOffset=0):
    """This function is meant to be run from the command line. It will
    automatically show mouse pointer position and windows names under it"""
    if xOffset != 0 or yOffset != 0:
        print('xOffset: %s yOffset: %s' % (xOffset, yOffset))
    try:
        prevWindows = None
        while True:
            x, y = cursor()
            positionStr = 'X: ' + str(x - xOffset).rjust(4) + ' Y: ' + str(y - yOffset).rjust(
                4) + '  (Press Ctrl-C to quit)'
            if prevWindows is not None:
                sys.stdout.write(positionStr)
                sys.stdout.write('\b' * len(positionStr))
            windows = getWindowsAt(x, y)
            if windows != prevWindows:
                prevWindows = windows
                print('\n')
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
    print(getAllTitles())
    displayWindowsUnderMouse(0, 0)


if __name__ == "__main__":
    main()
