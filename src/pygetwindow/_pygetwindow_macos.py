import Quartz
import AppKit
import pygetwindow
import pyrect


def getAllTitles():
    """Returns a list of strings of window titles for all visible windows.
    """
    # Source: https://stackoverflow.com/questions/53237278/obtain-list-of-all-window-titles-on-macos-from-a-python-script/53985082#53985082
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    return ['%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')) for win in windows]


def getActiveWindow():
    """Returns a Window object of the currently active Window."""
    # Source: https://stackoverflow.com/questions/5286274/front-most-window-using-cgwindowlistcopywindowinfo
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if win['kCGWindowLayer'] == 0:
            return MacOSWindow(win['kCGWindowNumber'])
    raise Exception('Could not find an active window.') # Temporary hack.


def getWindowsAt(x, y):
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    matches = []
    for win in windows:
        w = win['kCGWindowBounds']
        if pygetwindow.pointInRect(x, y, w['X'], w['Y'], w['Width'], w['Height']):
            matches.append('%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')))
    return matches


def activate(title):
    """ Uses the `activateWithOptions_` to bring the window to the foreground.

    See https://developer.apple.com/documentation/appkit/nsrunningapplication?language=objc
    """
    w = _getWindowByTitle(title)
    w.activate()


def getWindowGeometry(title):
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if title in '%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')):
            w = win['kCGWindowBounds']
            return (w['X'], w['Y'], w['Width'], w['Height'])


def isVisible(title):
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if title in '%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')):
            return win['kCGWindowAlpha'] != 0.0


def isMinimized(title):
    # https://developer.apple.com/documentation/appkit/nsrunningapplication/1525949-hidden?language=objc
    w = _getWindowByTitle(title)
    return w.app.hidden


def _getWindowByTitle(title, exact=False):
    """Returns a MacOSWindow object for matched title.
    
    :param exact: Whether to only return where title is an exact match.
    """
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    for win in windows:
        if exact:
            if (title == win[Quartz.kCGWindowOwnerName]) or \
                (title == win.get(Quartz.kCGWindowName, '')):
                return MacOSWindow(win['kCGWindowNumber'])
        if title in '%s %s' % (win[Quartz.kCGWindowOwnerName], win.get(Quartz.kCGWindowName, '')):
            return MacOSWindow(win['kCGWindowNumber'])
    raise Exception('Could not find a matching window.') # HACK: Temporary hack.


def _getWindowRect(hWnd):
    """Returns `Rect` for specified MacOS window based on CGWindowID"""
    # hWnd equivalent in MacOS is CGWindowID
    # https://developer.apple.com/documentation/coregraphics/cgwindowid?language=objc
    # windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
    windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
    for win in windows:
        if hWnd == win['kCGWindowNumber']:
            w = win['kCGWindowBounds']
            return pygetwindow.Rect(
                left=w['X'],
                top=w['Y'],
                right=w['X']+w['Width'],
                bottom=w['Y']+w['Height'])


class MacOSWindow():
    def __init__(self, hWnd=None):
        # hWnd equivalent in MacOS is CGWindowID
        # https://developer.apple.com/documentation/coregraphics/cgwindowid?language=objc
        self._hWnd = hWnd
        self._app = None

        def _onRead(attrName):
            r = _getWindowRect(self._hWnd)
            self._rect._left = r.left # Setting _left directly to skip the onRead.
            self._rect._top = r.top # Setting _top directly to skip the onRead.
            self._rect._width = r.right - r.left # Setting _width directly to skip the onRead.
            self._rect._height = r.bottom - r.top # Setting _height directly to skip the onRead.

        def _onChange(oldBox, newBox):
            self.moveTo(newBox.left, newBox.top)
            self.resizeTo(newBox.width, newBox.height)

        r = _getWindowRect(self._hWnd)
        self._rect = pyrect.Rect(r.left, r.top, r.right - r.left, r.bottom - r.top, onChange=_onChange, onRead=_onRead)
        self.__get_kCGWindow_dict()


    def __str__(self):
        r = _getWindowRect(self._hWnd)
        width = r.right - r.left
        height = r.bottom - r.top
        return '<%s left="%s", top="%s", width="%s", height="%s", title="%s">' % (self.__class__.__name__, r.left, r.top, width, height, self.title)


    def __repr__(self):
        return '%s(hWnd=%s)' % (self.__class__.__name__, self._hWnd)


    def __eq__(self, other):
        return isinstance(other, MacOSWindow) and self._hWnd == other._hWnd


    def __get_kCGWindow_dict(self):
        """Sets the specific keys returned by Quartz for later re-use"""
        windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
        for win in windows:
            if self._hWnd == win['kCGWindowNumber']:
                for key, value in win.items():
                    setattr(self, key, value)

    @property
    def app(self):
        """Represents a running associated NSApplication instance."""
        if self._app:
            return self._app
        else:
            windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements | Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID)
            for win in windows:
                if self._hWnd == win['kCGWindowNumber']:
                    ap = AppKit.NSRunningApplication.\
                    runningApplicationWithProcessIdentifier_(win['kCGWindowOwnerPID'])
                    self._app = ap
                    return ap

    @property
    def isActive(self):
        return self.app.active


    def close(self):
        """Closes this window. This may trigger "Are you sure you want to
        quit?" dialogs or other actions that prevent the window from
        actually closing. This is identical to clicking the X button on the
        window."""
        result = self.app.terminate()
        if not result:
            raise Exception("Unable to terminate application")


    def minimize(self):
        """Minimizes this window."""
        # https://developer.apple.com/documentation/appkit/nsrunningapplication/1526608-hide?language=objc
        self.app.hide()


    def maximize(self):
        """Maximizes this window."""
        self.app.unhide()
        self.activate()


    def restore(self):
        """If maximized or minimized, restores the window to it's normal size."""
        self.maximize()


    def activate(self):
        """Activate this window and make it the foreground window."""
        if not self.isActive:
            self.app.activateWithOptions_(AppKit.NSApplicationActivateIgnoringOtherApps)        


    def resizeRel(self, widthOffset, heightOffset):
        """Resizes the window relative to its current size."""
        raise NotImplementedError("Method not implemented in MacOS")


    def resizeTo(self, newWidth, newHeight):
        """Resizes the window to a new width and height."""
        raise NotImplementedError("Method not implemented in MacOS")


    def moveRel(self, xOffset, yOffset):
        """Moves the window relative to its current position."""
        raise NotImplementedError("Method not implemented in MacOS")


    def moveTo(self, newLeft, newTop):
        """Moves the window to new coordinates on the screen."""
        raise NotImplementedError("Method not implemented in MacOS")


    @property
    def isMinimized(self):
        """Returns True if the window is currently minimized."""
        try:
            return self.app.hidden
        except AttributeError:
            return False

    @property
    def isMaximized(self):
        """Returns True if the window is currently maximized."""
        raise NotImplementedError("Method not implemented in MacOS")

    @property
    def isActive(self):
        """Returns True if the window is currently the active, foreground window."""
        return getActiveWindow() == self

    @property
    def title(self):
        """Returns the window title as a string."""
        return self.kCGWindowName

    @property
    def visible(self):
        windows = Quartz.CGWindowListCopyWindowInfo(Quartz.kCGWindowListExcludeDesktopElements, Quartz.kCGNullWindowID)
        for win in windows:
            if self._hWnd == win[Quartz.kCGWindowNumber]:
                return win['kCGWindowAlpha'] != 0.0

    # Wrappers for pyrect.Rect object's properties.
    @property
    def left(self):
        return self._rect.left

    @left.setter
    def left(self, value):
        #import pdb; pdb.set_trace()
        self._rect.left # Run rect's onRead to update the Rect object.
        self._rect.left = value


    @property
    def right(self):
        return self._rect.right

    @right.setter
    def right(self, value):
        self._rect.right # Run rect's onRead to update the Rect object.
        self._rect.right = value


    @property
    def top(self):
        return self._rect.top

    @top.setter
    def top(self, value):
        self._rect.top # Run rect's onRead to update the Rect object.
        self._rect.top = value


    @property
    def bottom(self):
        return self._rect.bottom

    @bottom.setter
    def bottom(self, value):
        self._rect.bottom # Run rect's onRead to update the Rect object.
        self._rect.bottom = value


    @property
    def topleft(self):
        return self._rect.topleft

    @topleft.setter
    def topleft(self, value):
        self._rect.topleft # Run rect's onRead to update the Rect object.
        self._rect.topleft = value


    @property
    def topright(self):
        return self._rect.topright

    @topright.setter
    def topright(self, value):
        self._rect.topright # Run rect's onRead to update the Rect object.
        self._rect.topright = value


    @property
    def bottomleft(self):
        return self._rect.bottomleft

    @bottomleft.setter
    def bottomleft(self, value):
        self._rect.bottomleft # Run rect's onRead to update the Rect object.
        self._rect.bottomleft = value


    @property
    def bottomright(self):
        return self._rect.bottomright

    @bottomright.setter
    def bottomright(self, value):
        self._rect.bottomright # Run rect's onRead to update the Rect object.
        self._rect.bottomright = value


    @property
    def midleft(self):
        return self._rect.midleft

    @midleft.setter
    def midleft(self, value):
        self._rect.midleft # Run rect's onRead to update the Rect object.
        self._rect.midleft = value


    @property
    def midright(self):
        return self._rect.midright

    @midright.setter
    def midright(self, value):
        self._rect.midright # Run rect's onRead to update the Rect object.
        self._rect.midright = value


    @property
    def midtop(self):
        return self._rect.midtop

    @midtop.setter
    def midtop(self, value):
        self._rect.midtop # Run rect's onRead to update the Rect object.
        self._rect.midtop = value


    @property
    def midbottom(self):
        return self._rect.midbottom

    @midbottom.setter
    def midbottom(self, value):
        self._rect.midbottom # Run rect's onRead to update the Rect object.
        self._rect.midbottom = value


    @property
    def center(self):
        return self._rect.center

    @center.setter
    def center(self, value):
        self._rect.center # Run rect's onRead to update the Rect object.
        self._rect.center = value


    @property
    def centerx(self):
        return self._rect.centerx

    @centerx.setter
    def centerx(self, value):
        self._rect.centerx # Run rect's onRead to update the Rect object.
        self._rect.centerx = value


    @property
    def centery(self):
        return self._rect.centery

    @centery.setter
    def centery(self, value):
        self._rect.centery # Run rect's onRead to update the Rect object.
        self._rect.centery = value


    @property
    def width(self):
        return self._rect.width

    @width.setter
    def width(self, value):
        self._rect.width # Run rect's onRead to update the Rect object.
        self._rect.width = value


    @property
    def height(self):
        return self._rect.height

    @height.setter
    def height(self, value):
        self._rect.height # Run rect's onRead to update the Rect object.
        self._rect.height = value


    @property
    def size(self):
        return self._rect.size

    @size.setter
    def size(self, value):
        self._rect.size # Run rect's onRead to update the Rect object.
        self._rect.size = value


    @property
    def area(self):
        return self._rect.area

    @area.setter
    def area(self, value):
        self._rect.area # Run rect's onRead to update the Rect object.
        self._rect.area = value


    @property
    def box(self):
        return self._rect.box

    @box.setter
    def box(self, value):
        self._rect.box # Run rect's onRead to update the Rect object.
        self._rect.box = value