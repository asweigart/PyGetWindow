#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import platform
import subprocess
import sys
import time
import numpy as np
from AppKit import *
import Quartz
from pygetwindow import PyGetWindowException, pointInRect, BaseWindow, Rect, Point, Size

""" 
IMPORTANT NOTICE:
    This script uses NSWindow objects, so you have to pass the app object (NSApp()) when instantiating the class.
    To manage other apps windows, this script uses Apple Script, so grant permissions on Security & Privacy -> Accessibility
"""

WS = NSWorkspace.sharedWorkspace()
# WARNING: Changes are not immediately applied nor updated on stored Window Info object (specially using AppScript)
#          Activate wait option if you need to effectively know if/when action has been performed
WAIT_ATTEMPTS = 10
WAIT_DELAY = 0.025  # Will be progressively increased on every retry


def _levenshtein(seq1, seq2):
    # fuzzywuzzy throws a warning if python-levenshtein is not installed
    # textdistance is not available on Python2
    # https://stackabuse.com/levenshtein-distance-and-text-similarity-in-python/
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros((size_x, size_y))
    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x, y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y - 1],
                    matrix[x, y - 1] + 1
                )
            else:
                matrix[x, y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y - 1] + 1,
                    matrix[x, y - 1] + 1
                )
    # Modified to return a custom similarity ratio (adding a weight of 1 for replacements, instead of 2)
    ret = matrix[size_x - 1, size_y - 1]
    return 1 - ret / max(size_x - 1, size_y - 1)


def getActiveWindow(app=None):
    """Returns a Window object of the currently active Window or None."""
    if not app:
        app = WS.frontmostApplication()
        windows = _getAllAppWindows(app)
        for win in windows:
            return MacOSWindow(app, win)
    else:
        for win in getAllWindows(app):  # .keyWindow() / .mainWindow() not working?!?!?!
            return win
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
    if not app:
        activeApps = _getAllApps()
        activeWindows = _getAllWindows()
        for app in activeApps:
            for win in activeWindows:
                w = win["kCGWindowBounds"]
                if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerPID] == app.processIdentifier() and \
                        pointInRect(x, y, w["X"], w["Y"], w["Width"], w["Height"]):
                    matches.append(MacOSWindow(app, win))
    else:
        for win in getAllWindows(app):
            if pointInRect(x, y, win.left, win.top, win.width, win.height):
                matches.append(win)
    return matches


def getWindowsWithTitle(title, app=None):
    """Returns a list of window objects matching the given title or an empty list."""
    matches = []
    windows = getAllWindows(app)
    for win in windows:
        if _levenshtein(win.title, title) > 0.9:
            matches.append(win)
    return matches


def getAllTitles(app=None):
    """Returns a list of strings of window titles for all visible windows."""
    return [win.title for win in getAllWindows(app)]


def getAllWindows(app=None):
    """Returns a list of window objects for all visible windows."""
    windows = []
    if not app:
        activeApps = _getAllApps()
        winTitles = _getWindowTitles()
        filteredApps = []
        for app in activeApps:
            appTitles = []
            for item in winTitles:
                if item[0] == app.localizedName():
                    appTitles.append(item[1])
            filteredApps.append([app, appTitles])
        for app in filteredApps:
            appWindows = _getAllAppWindows(app[0])
            i = 0
            for title in app[1]:
                if i < len(appWindows):
                    windows.append(MacOSWindow(app[0], appWindows[i], title))
                else:
                    break
                i += 1
    else:
        for win in app.orderedWindows():
            windows.append(MacOSNSWindow(app, win))
    return windows


def _getWindowTitles():
    cmd = """osascript -e 'tell application "System Events"
                                set winNames to {}
                                repeat with p in every process whose background only is false
                                    repeat with w in every window of p
                                        set end of winNames to {name of p, name of w}
                                    end repeat
                                end repeat
                            end tell
                            return winNames'"""
    ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip().split(", ")
    retList = []
    for i in range(len(ret)-1):
        subList = [ret[i], ret[i + 1]]
        retList.append(subList)
    return retList


def _getAllApps():
    return WS.runningApplications()


def _getAllWindows(excludeDesktop=True, screenOnly=True):
    # Source: https://stackoverflow.com/questions/53237278/obtain-list-of-all-window-titles-on-macos-from-a-python-script/53985082#53985082
    flags = Quartz.kCGWindowListExcludeDesktopElements if excludeDesktop else 0 | \
            Quartz.kCGWindowListOptionOnScreenOnly if screenOnly else 0
    return Quartz.CGWindowListCopyWindowInfo(flags, Quartz.kCGNullWindowID)


def _getAllAppWindows(app):
    windows = _getAllWindows()
    windowsInApp = []
    for win in windows:
        if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerPID] == app.processIdentifier():
            windowsInApp.append(win)
    return windowsInApp


class MacOSWindow(BaseWindow):

    def __init__(self, app, hWnd, title=""):
        self._app = app
        self._hWnd = hWnd
        self.winNumber = self._hWnd[Quartz.kCGWindowNumber]
        if title:
            self.Title = title
        else:
            self.Title = ""
            self.Title = self.title
        self._setupRectProperties()
        v = platform.mac_ver()[0].split(".")
        ver = float(v[0]+"."+v[1])
        # On Yosemite and below we need to use Zoom instead of FullScreen to maximize windows
        self.use_zoom = (ver <= 10.10)

    def _getWindowRect(self):
        """Returns a rect of window position and size (left, top, right, bottom).
        It follows ctypes format for compatibility"""
        w = [0, 0, 0, 0]
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                        set winIndex to %i
                                        set appBounds to {0, 0, 0, 0}
                                        try
                                            set appPos to (get position of window winIndex)
                                            set appSize to (get size of window winIndex)
                                            set appBounds to {appPos, appSize}
                                        end try
                                    end tell
                                    return appBounds'""" % (self._app.localizedName(), winSeq)
            w = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip().split(", ")
        # This solution is smarter and faster, but it seems to take some time to update window info
        # TODO: check if this always works on "real" (non-virtual) installs
        # for win in _getAllAppWindows(self._app):
        #     if win[Quartz.kCGWindowNumber] == self.winNumber:
        #         bounds = win[Quartz.kCGWindowBounds]
        #         w = [bounds["X"], bounds["Y"], bounds["Width"], bounds["Height"]]
        return Rect(int(w[0]), int(w[1]), int(w[0]) + int(w[2]), int(w[1]) + int(w[3]))

    def _getWindowIndex(self):
        # Window index can be tricky for maximized and unmapped windows
        # Using window name instead (fuzzy comparison is needed for apps like Terminal, which changes name when resized)
        i = 0
        for win in _getAllAppWindows(self._app):
            i += 1
            if win.get(Quartz.kCGWindowNumber, -1) == self.winNumber:
                return i
        return -1

    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)

    def __eq__(self, other):
        return isinstance(other, MacOSWindow) and self._hWnd == other._hWnd

    def close(self):
        """Closes this window or app. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from actually
        closing. This is identical to clicking the X button on the window."""
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "%s" 
                                        try
                                            close window %i
                                        end try
                                    end tell'""" % (self._app.localizedName(), winSeq)
            os.system(cmd)
        return self._getWindowIndex() < 0

    def minimize(self, wait=False):
        """Minimizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was minimized"""
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s" 
                                    try
                                        set value of attribute "AXMinimized" of window %i to true
                                    end try
                                end tell'""" % (self._app.localizedName(), winSeq)
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
            winSeq = self._getWindowIndex()
            if winSeq > 0:
                if self.use_zoom:
                    cmd = """osascript -e 'tell application "System Events" to tell application "%s" 
                                                try
                                                    tell window %i to set zoomed to true
                                                end try
                                            end tell'""" % (self._app.localizedName(), winSeq)
                else:
                    cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                                try
                                                    set value of attribute "AXFullScreen" of window %i to true
                                                end try
                                            end tell'""" % (self._app.localizedName(), winSeq)
                os.system(cmd)
                retries = 0
                while wait and retries < WAIT_ATTEMPTS and not self.isMaximized:
                    retries += 1
                    time.sleep(WAIT_DELAY * retries)
                if self.use_zoom:
                    self.resizeTo(resolution().width, resolution().height, wait=wait)
        return self.isMaximized

    def restore(self, wait=False):
        """If maximized or minimized, restores the window to it's normal size.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was restored"""
        self.activate(wait=True)
        if self.isMaximized:
            if self.use_zoom:
                winSeq = self._getWindowIndex()
                if winSeq > 0:
                    cmd = """osascript -e 'tell application "System Events" to tell application "%s" 
                                                try
                                                    tell window %i to set zoomed to false
                                                end try
                                            end tell'""" % (self._app.localizedName(), winSeq)
                    os.system(cmd)
            else:
                cmd = """osascript -e 'tell application "System Events" to tell application process "%s" 
                                            try
                                                set value of attribute "AXFullScreen" of window 1 to false
                                            end try
                                        end tell'""" % self._app.localizedName()
                os.system(cmd)
        if self.isMinimized:
            winSeq = self._getWindowIndex()
            if winSeq > 0:
                cmd = """osascript -e 'tell application "System Events" to tell application process "%s" 
                                            try
                                                set value of attribute "AXMinimized" of window %i to false
                                            end try
                                        end tell'""" % (self._app.localizedName(), winSeq)
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
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application "%s"
                                        try
                                            tell window %i to set visible to false
                                        end try
                                     end tell'""" % (self._app.localizedName(), winSeq)
            os.system(cmd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and self._isMapped:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return not self._isMapped

    def show(self, wait=False):
        """If hidden or showing, shows the window on screen and in title bar.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window is showing (mapped)"""
        cmd = """osascript -e 'tell application "System Events" to tell application "%s"
                                    activate
                                    repeat with w in every window whose visible is false
                                        if name of w is equal to "%s"
                                            tell w to set visible to true
                                            exit repeat
                                        end if
                                    end repeat
                                 end tell'""" % (self._app.localizedName(), self.title)
        os.system(cmd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
        return self._isMapped

    def activate(self, wait=False):
        """Activate this window and make it the foreground (focused) window.
        Use 'wait' option to confirm action requested (in a reasonable time).

        Returns ''True'' if window was activated"""
        # self._app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application "%s"
                                        try
                                            set visible to true
                                            activate
                                            set winIndex to %i
                                            tell window winIndex to set visible to true 
                                            tell window winIndex to set index to 1
                                        end try
                                    end tell'""" % (self._app.localizedName(), winSeq)
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
        # https://apple.stackexchange.com/questions/350256/how-to-move-mac-os-application-to-specific-display-and-also-resize-automatically
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                        try
                                            set size of window %i to {%i, %i}
                                        end try
                                    end tell'""" % (self._app.localizedName(), winSeq, newWidth, newHeight)
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
        # https://apple.stackexchange.com/questions/350256/how-to-move-mac-os-application-to-specific-display-and-also-resize-automatically
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                        try
                                            set position of window %i to {%i, %i}
                                        end try
                                    end tell'""" % (self._app.localizedName(), winSeq, newLeft, newTop)
            os.system(cmd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and self.left != newLeft and self.top != newTop:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return self.left == newLeft and self.top == newTop

    def _moveResizeTo(self, newLeft, newTop, newWidth, newHeight):
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                        set winIndex to %i
                                        try
                                            set position of window winIndex to {%i, %i}
                                        end try
                                        try
                                            set size of window winIndex to {%i, %i}
                                        end try
                                    end tell'""" % \
                  (self._app.localizedName(), winSeq, newLeft, newTop, newWidth, newHeight)
            os.system(cmd)
            retries = 0
            while retries < WAIT_ATTEMPTS and self.left != newLeft and self.top != newTop and \
                    self.width != newWidth and self.height != newHeight:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
        return

    @property
    def isMinimized(self):
        """Returns ``True`` if the window is currently minimized."""
        ret = "false"
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell process "%s" 
                                        set isMin to false
                                        try
                                            set isMin to value of attribute "AXMinimized" of window %i
                                        end try
                                    end tell
                                    return (isMin as string)'""" % (self._app.localizedName(), winSeq)
            ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return ret == "true"

    @property
    def isMaximized(self):
        """Returns ``True`` if the window is currently maximized (fullscreen)."""
        if self.use_zoom:
            cmd = """osascript -e 'tell application "System Events" to tell application "%s" 
                                        set winIndex to 0
                                        set winName to ""
                                        try
                                            set winIndex to index of (first window whose zoomed is true)
                                        end try
                                        if winIndex > 0 then
                                            try
                                                set winName to name of window (winIndex as integer)
                                            end try
                                        end if
                                    end tell 
                                    return winName'""" % self._app.localizedName()
        else:
            cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                        set isFull to false
                                        set winName to ""
                                        try
                                            set isFull to value of attribute "AXFullScreen" of window 1
                                        end try
                                        if isFull then
                                            try
                                                set winName to name of window 1
                                            end try
                                        end if
                                    end tell
                                    return winName'""" % self._app.localizedName()
        ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return _levenshtein(ret, self.title) > 0.9


    @property
    def isActive(self):
        """Returns ``True`` if the window is currently the active, foreground window."""
        if self._app.isActive():
            winSeq = self._getWindowIndex()
            return winSeq == 1
        return False

    @property
    def title(self):
        name = self._hWnd.get(Quartz.kCGWindowName, '')
        if not name:
            winSeq = self._getWindowIndex()
            if winSeq > 0:
                cmd = """osascript -e 'tell application "System Events" to tell application process "%s"
                                            set winName to ""
                                            try
                                                set winName to name of window %i
                                            end try
                                        end tell
                                        return winName'""" % (self._app.localizedName(), winSeq)
                name = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        if name:
            if not self.Title:
                self.Title = name
        else:
            if self.Title:
                name = self.Title
        return name

    @property
    def visible(self):
        """Returns ``True`` if the window is currently visible."""
        return self._isMapped and not self.isMinimized

    @property
    def _isMapped(self):
        # Returns ``True`` if the window is currently mapped by WM (minimized windows also have visible set to true)
        ret = "false"
        winSeq = self._getWindowIndex()
        if winSeq > 0:
            cmd = """osascript -e 'tell application "System Events" to tell application "%s"
                                        set isMapped to false 
                                        try
                                            tell window %i to set isMapped to visible
                                        end try
                                     end tell'""" % (self._app.localizedName(), winSeq)
            ret = subprocess.check_output(cmd, shell=True).decode(encoding="utf-8").strip()
        return ret == "true"


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
        return isinstance(other, MacOSNSWindow) and self._hWnd == other._hWnd

    def close(self):
        """Closes this window. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from actually
        closing. This is identical to clicking the X button on the window."""
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
            positionStr = 'X: ' + str(x - xOffset).rjust(4) + ' Y: ' + str(y - yOffset).rjust(4) + '  (Press Ctrl-C to quit)'
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
