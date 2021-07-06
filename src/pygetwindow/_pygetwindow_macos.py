#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import AppKit
import Quartz
import Cocoa
from pygetwindow import PyGetWindowException, pointInRect, BaseWindow, Rect, Point, Size

""" 
IMPORTANT NOTICE:
    There aren't mechanisms to manage other apps/windows on MacOS. So this is full of hacks based mainly on scripts.
    For non-scriptable apps, some methods will not work (and will return 'False'): move/To, resize/To.
    The rest of methods should work fine in most cases. 
    In case you need full-support, try to add your target application to Accessibility options.
"""

WS = AppKit.NSWorkspace.sharedWorkspace()
# WARNING: Changes are not immediately applied nor updated on stored window object
#          Activate wait option if you need to effectively know if/when change has been applied or updated values
WAIT_ATTEMPTS = 10
WAIT_DELAY = 0.025  # Will be progressively increased on every retry
MENUBAR_HEIGHT = 24  # Temporary Hack. MUST find a wayt to check if window is maximized or menubar height programmatically


def getActiveWindow():
    """Returns a Window object of the currently active Window or None."""
    app = WS.frontmostApplication()
    if app:
        windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        for win in windows:
            if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerName] == app.localizedName():
                return MacOSWindow(app, win)
    return None


def _getActiveWindow():
    """Alternative: Returns a Window object of the currently active Window."""
    # Source: https://stackoverflow.com/questions/53237266/how-can-i-minimize-maximize-windows-in-macos-with-the-cocoa-api-from-a-python-sc
    activeApps = WS.runningApplications()
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for app in activeApps:
        if app.isActive():
            for win in windows:
                if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerName] == app.localizedName():
                    return MacOSWindow(app, win)
    return None


def getActiveWindowTitle():
    """Returns a Window object of the currently active Window or empty string."""
    win = getActiveWindow()
    if win:
        return win.title
    else:
        return ""


def getWindowsAt(x, y):
    """Returns a list of windows under the mouse pointer or an empty list."""
    matches = []
    for win in getAllWindows():
        if pointInRect(x, y, win.left, win.top, win.width, win.height):
            matches.append(win)
    return matches


def getWindowsWithTitle(title):
    """Returns a list of window objects matching the given title or an empty list."""
    # DOUBT: Should the "owner" name (app to which the window belongs to) be included?
    matches = []
    for win in getAllWindows():
        if win.title == title:
            matches.append(win)
    return matches


def getAllTitles():
    """Returns a list of strings of window titles for all visible windows."""
    return [win.title for win in getAllWindows()]


def getAllWindows():
    """Returns a list of strings of window titles for all visible windows."""
    # It is restricted to layer 0, which seems to be the "user layer", but not sure...
    windows = []
    activeApps = WS.runningApplications()
    for app in activeApps:
        appwindows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        for win in appwindows:
            if win[Quartz.kCGWindowLayer] == 0 and win[Quartz.kCGWindowOwnerName] == app.localizedName():
                windows.append(MacOSWindow(app, win))
    return windows


class MacOSWindow(BaseWindow):

    def __init__(self, app, hWnd):
        self._app = app
        self._hWnd = hWnd
        self._setupRectProperties()

    def _getWindowRect(self):
        """Returns a rect of window position and size (left, top, right, bottom).
        It follows ctypes format for compatibility"""
        self._updateAppWindow(self._app, self._hWnd)
        w = self._hWnd['kCGWindowBounds']
        return Rect(int(w["X"]), int(w["Y"]), int(w["X"] + w["Width"]), int(w["Y"] + w["Height"]))

    def _updateAppWindow(self, app, hWnd):
        # Update window object since we stored a static copy
        windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
        for win in windows:
            if win[Quartz.kCGWindowOwnerName] == app.localizedName() and \
                    win[Quartz.kCGWindowNumber] == hWnd[Quartz.kCGWindowNumber]:
                self._hWnd = win
        return

    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)

    def __eq__(self, other):
        return isinstance(other, MacOSWindow) and self._hWnd == other._hWnd

    def close(self):
        """Closes this window. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from actually
        closing. This is identical to clicking the X button on the window."""
        self._app.terminate()

    def minimize(self, wait=False):
        """Minimizes this window.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        # https://stackoverflow.com/questions/1770312/is-there-a-sendkey-for-mac-in-python
        if not self.isMinimized:
            self.activate(wait=True)
            cmd = """osascript -e 'tell application "System Events" to keystroke "m" using {command down, option down}'"""
            os.system(cmd)
            self._updateAppWindow(self._app, self._hWnd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and not self.isMinimized:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
                self._updateAppWindow(self._app, self._hWnd)
        return self.isMinimized

    def maximize(self, wait=False, force=False):
        """Maximizes (fullscreen) this window.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        if not self.isMaximized:
            self.activate(wait=True)
            cmd = """osascript -e 'tell application "System Events" to keystroke "f" using {command down, control down}'"""
            os.system(cmd)
            self._updateAppWindow(self._app, self._hWnd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and not self.isMaximized:
                retries += 1
                time.sleep(WAIT_DELAY * retries)
                self._updateAppWindow(self._app, self._hWnd)
        return self.isMaximized

    def restore(self, wait=False):
        """If maximized or minimized, restores the window to it's normal size.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        self.activate(wait=True)
        if self.isMaximized:
            cmd = """osascript -e 'tell application "System Events" to keystroke "f" using {command down, control down}'"""
            os.system(cmd)
            self._updateAppWindow(self._app, self._hWnd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and (self.isMinimized or self.isMaximized):
                retries += 1
                time.sleep(WAIT_DELAY * retries)
                self._updateAppWindow(self._app, self._hWnd)
        if self.isMinimized:
            # Some apps (e.g. Terminal) will allow this method, but not some others (e.g. TextEdit)
            # winIndex = self._findWindowNumber(self._app, self._hWnd)
            # cmd = """osascript -e 'tell application "System Events" to keystroke "%i" using {command down, option down}'""" % winIndex
            #
            # To allow this, the script must be added to Accessibility options
            # https://stackoverflow.com/questions/57412472/how-to-unminimize-a-minimized-window-apple-script-not-working-with-upgrade-from
            # cmd = """ osascript -e 'tell application "System Events"
            #             tell process "Dock"
            #                 tell list 1
            #                     try
            #                         click (every UI element whose name is "%s")
            #                     on error errstr
            #                         display alert errstr
            #                     end try
            #                 end tell
            #             end tell
            #         end tell'""" % self.title
            #
            # This simulates MacOS behavior, but requires user action
            cmd = """osascript -e 'tell application "System Events" to key code 125 using control down'"""
            os.system(cmd)
            self._updateAppWindow(self._app, self._hWnd)
            retries = 0
            while wait and retries < WAIT_ATTEMPTS and (self.isMinimized or self.isMaximized):
                retries += 1
                time.sleep(WAIT_DELAY * retries)
                self._updateAppWindow(self._app, self._hWnd)
        return not self.isMaximized and not self.isMinimized

    def hide(self, wait=False):
        """If hidden or showing, hides the window from screen and title bar.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        self._app.hide()
        self._updateAppWindow(self._app, self._hWnd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
            self._updateAppWindow(self._app, self._hWnd)
        return not self._isMapped

    def show(self, wait=False):
        """If hidden or showing, shows the window on screen and in title bar.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        self._app.unhide()
        self.activate(wait=True)
        self._updateAppWindow(self._app, self._hWnd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self._isMapped:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
            self._updateAppWindow(self._app, self._hWnd)
        return self._isMapped

    def activate(self, wait=False):
        """Activate this window and make it the foreground (focused) window.
        Use 'wait' option to confirm action requested (in a reasonable time)."""
        self._app.activateWithOptions_(Cocoa.NSApplicationActivateIgnoringOtherApps)
        self._updateAppWindow(self._app, self._hWnd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and not self.isActive:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
            self._updateAppWindow(self._app, self._hWnd)
        return self.isActive

    def resize(self, widthOffset, heightOffset, wait=False):
        """Resizes the window relative to its current size. For non-scriptable apps, it will not work.
        Use 'wait' option to confirm action requested (in a reasonable time).
        WARNING: Will not work if target app is not scriptable"""
        return self.resizeTo(self.width + widthOffset, self.height + heightOffset, wait)

    resizeRel = resize  # resizeRel is an alias for the resize() method.

    def resizeTo(self, newWidth, newHeight, wait=False):
        """Resizes the window to a new width and height. For non-scriptable apps, it will not work.
        Use 'wait' option to confirm action requested (in a reasonable time).
        WARNING: Will not work if target app is not scriptable"""
        self._updateAppWindow(self._app, self._hWnd)
        cmd = """osascript -e 'tell application "%s" to tell window 1 to set bounds to {%i, %i, %i, %i}'""" % \
              (self._app.localizedName(), self.left, self.top, self.left + newWidth, self.top + newHeight)
        os.system(cmd)
        self._updateAppWindow(self._app, self._hWnd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.width != newWidth and self.height != newHeight:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
            self._updateAppWindow(self._app, self._hWnd)
        return self.width == newWidth and self.height == newHeight

    def move(self, xOffset, yOffset, wait=False):
        """Moves the window relative to its current position. For non-scriptable apps, it will not work.
        Use 'wait' option to confirm action requested (in a reasonable time).
        WARNING: Will not work if target app is not scriptable"""
        return self.moveTo(self.left + xOffset, self.top + yOffset, wait)

    moveRel = move  # moveRel is an alias for the move() method.

    def moveTo(self, newLeft, newTop, wait=False):
        """Moves the window to new coordinates on the screen. For non-scriptable apps, it will not work.
        Use 'wait' option to confirm action requested (in a reasonable time).
        WARNING: Will not work if target app is not scriptable"""
        self._updateAppWindow(self._app, self._hWnd)
        cmd = """osascript -e 'tell application "%s" to tell window 1 to set bounds to {%i, %i, %i, %i}'""" % \
              (self._app.localizedName(), newLeft, newTop, newLeft + self.width, newTop + self.height)
        os.system(cmd)
        self._updateAppWindow(self._app, self._hWnd)
        retries = 0
        while wait and retries < WAIT_ATTEMPTS and self.left != newLeft and self.top != newTop:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
            self._updateAppWindow(self._app, self._hWnd)
        return self.left == newLeft and self.top == newTop

    def _moveResizeTo(self, newLeft, newTop, newWidth, newHeight, wait=False):
        # https://stackoverflow.com/questions/16598551/os-x-move-window-from-python
        # https://apple.stackexchange.com/questions/350256/how-to-move-mac-os-application-to-specific-display-and-also-resize-automatically
        # I guess this solution relies on the target app scripting capabilities, so it's not general...
        # Nevertheless, it might be the only solution since Apple does not "like" apps controlling other apps.
        self._updateAppWindow(self._app, self._hWnd)
        cmd = """osascript -e 'tell application "%s" to tell window 1 to set bounds to {%i, %i, %i, %i}'""" % \
              (self._app.localizedName(), newLeft, newTop, newLeft + newWidth, newTop + newHeight)
        ret = os.system(cmd)
        self._updateAppWindow(self._app, self._hWnd)
        retries = 0
        while ret == 0 and wait and retries < WAIT_ATTEMPTS and self.left != newLeft and self.top != newTop and \
                self.width != newWidth and self.height != newHeight:
            retries += 1
            time.sleep(WAIT_DELAY * retries)
            self._updateAppWindow(self._app, self._hWnd)
        return True if ret == 0 else False

    @property
    def isMinimized(self):
        """Returns ``True`` if the window is currently minimized."""
        return Quartz.kCGWindowIsOnscreen not in self._hWnd.keys() and not self.isMaximized #and self._isMapped

    @property
    def isMaximized(self):
        """Returns ``True`` if the window is currently maximized (fullscreen)."""
        return self.left == 0 and self.top in (0, MENUBAR_HEIGHT) and \
               self.width == resolution().width and self.height == resolution().height - self.top

    @property
    def isActive(self):
        """Returns ``True`` if the window is currently the active, foreground window."""
        win = getActiveWindow()
        if win:
            if win.isMaximized and self.isMaximized:
                return True
            else:
                return self._app.isActive() and \
                       win._hWnd[Quartz.kCGWindowNumber] == self._hWnd[Quartz.kCGWindowNumber]
        return False

    @property
    def title(self):
        """Returns the window title as a string."""
        # Source: https://stackoverflow.com/questions/53237278/obtain-list-of-all-window-titles-on-macos-from-a-python-script/53985082#53985082
        # Should the owner (app) be added?
        # return self._hWnd.get([Quartz.kCGWindowOwnerName], '') + " - " + self._hWnd.get(Quartz.kCGWindowName, '')
        return self._hWnd.get(Quartz.kCGWindowName, '')

    def _parentName(self):
        return self._hWnd.get(Quartz.kCGWindowOwnerName, '')

    @property
    def visible(self):
        """Return ``True`` if the window is currently visible."""
        if self.isMaximized:
            return True
        if not self._isMapped or self.isMinimized:
            return False
        windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        for win in windows:
            if win[Quartz.kCGWindowOwnerName] == self._app.localizedName() and \
                    win[Quartz.kCGWindowNumber] == self._hWnd[Quartz.kCGWindowNumber]:
                return True
        return False

    @property
    def _isMapped(self):
        """Return ``True`` if the window is currently mapped."""
        for win in getAllWindows():
            if win._hWnd[Quartz.kCGWindowOwnerName] == self._app.localizedName() and \
                    win._hWnd[Quartz.kCGWindowNumber] == self._hWnd[Quartz.kCGWindowNumber]:
                return True
        return False
        # return not self._app.isHidden()  # Returns always 'False' (maybe because of virtualbox???)


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
    displayWindowsUnderMouse(0, 0)


if __name__ == "__main__":
    main()
