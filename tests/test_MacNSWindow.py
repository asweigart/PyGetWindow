#!/usr/bin/env python
# encoding: utf-8

# Lawrence Akka - https://sourceforge.net/p/pyobjc/mailman/pyobjc-dev/thread/0B4BC391-6491-445D-92D0-7B1CEF6F51BE%40me.com/#msg27726282

# We need to import the relevant object definitions from PyObjC
import time
from AppKit import *
from PyObjCTools import AppHelper
import pygetwindow


# Cocoa prefers composition to inheritance. The members of an object's
# delegate will be called upon the happening of certain events. Once we define
# methods with particular names, they will be called automatically
class Delegate(NSObject):

    npw = None
    demoMode = False

    def getDemoMode(self):
        return self.demoMode

    def toggleDemoMode(self):
        self.demoMode = not self.getDemoMode()

    def applicationDidFinishLaunching_(self, aNotification):
        '''Called automatically when the application has launched'''
        # Set it as the frontmost application
        NSApp().activateIgnoringOtherApps_(True)
        for win in NSApp().orderedWindows():
            print(win.title(), win.frame())

        if self.demoMode:

            if not self.npw:
                windows = pygetwindow.getAllWindows(NSApp())
                self.npw = windows[0]

            wait = False
            timelap = 0.0

            self.npw.maximize(wait=wait)
            time.sleep(timelap)
            assert self.npw.isMaximized
            self.npw.restore(wait=wait)
            time.sleep(timelap)
            assert not self.npw.isMaximized

            self.npw.minimize(wait=wait)
            time.sleep(timelap)
            assert self.npw.isMinimized
            self.npw.restore(wait=wait)
            time.sleep(timelap)
            assert not self.npw.isMinimized

            # Test resizing
            self.npw.resizeTo(600, 400, wait=wait)
            print("RESIZE", self.npw.size)
            time.sleep(timelap)
            assert self.npw.size == (600, 400)
            assert self.npw.width == 600
            assert self.npw.height == 400

            self.npw.resizeRel(10, 20, wait=wait)
            print("RESIZEREL", self.npw.size)
            time.sleep(timelap)
            assert self.npw.size == (610, 420)
            assert self.npw.width == 610
            assert self.npw.height == 420

            # Test moving
            self.npw.moveTo(600, 300, wait=wait)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.topleft == (600, 300)
            assert self.npw.left == 600
            assert self.npw.top == 300
            assert self.npw.right == 1210
            assert self.npw.bottom == 720
            assert self.npw.bottomright == (1210, 720)
            assert self.npw.bottomleft == (600, 720)
            assert self.npw.topright == (1210, 300)

            self.npw.moveRel(1, 2, wait=wait)
            print("MOVEREL", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.topleft == (601, 302)
            assert self.npw.left == 601
            assert self.npw.top == 302
            assert self.npw.right == 1211
            assert self.npw.bottom == 722
            assert self.npw.bottomright == (1211, 722)
            assert self.npw.bottomleft == (601, 722)
            assert self.npw.topright == (1211, 302)

            # Move via the properties
            self.npw.resizeTo(601, 401, wait=wait)
            print("RESIZE", self.npw.size)
            time.sleep(timelap)
            self.npw.moveTo(100, 600, wait=wait)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            self.npw.left = 200
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.left == 200

            self.npw.right = 200
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.right == 200

            self.npw.top = 200
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.top == 200

            self.npw.bottom = 800
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.bottom == 800

            self.npw.topleft = (300, 400)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.topleft == (300, 400)

            self.npw.topright = (300, 400)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.topright == (300, 400)

            self.npw.bottomleft = (300, 700)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.bottomleft == (300, 700)

            self.npw.bottomright = (300, 900)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.bottomright == (300, 900)

            self.npw.midleft = (300, 400)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.midleft == (300, 400)

            self.npw.midright = (300, 400)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.midright == (300, 400)

            self.npw.midtop = (300, 400)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.midtop == (300, 400)

            self.npw.midbottom = (300, 700)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.midbottom == (300, 700)

            self.npw.center = (300, 400)
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.center == (300, 400)

            self.npw.centerx = 1000
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.centerx == 1000

            self.npw.centery = 300
            print("MOVE", self.npw.topleft)
            time.sleep(timelap)
            assert self.npw.centery == 300

            self.npw.width = 600
            print("RESIZE", self.npw.size)
            time.sleep(timelap)
            assert self.npw.width == 600

            self.npw.height = 400
            time.sleep(timelap)
            assert self.npw.height == 400

            self.npw.size = (810, 610)
            time.sleep(timelap)
            assert self.npw.size == (810, 610)

            # Test closing
            self.npw.close()

    def windowWillClose_(self, aNotification):
        '''Called automatically when the window is closed'''
        print("Window has been closed")
        # Terminate the application
        NSApp().terminate_(self)

    def windowDidBecomeKey_(self, aNotification):
        print("Now I'm ACTIVE")


def demo():
    # Create a new application instance ...
    a = NSApplication.sharedApplication()
    # ... and create its delegate.  Note the use of the
    # Objective C constructors below, because Delegate
    # is a subclass of an Objective C class, NSObject
    delegate = Delegate.alloc().init()
    delegate.toggleDemoMode()
    # Tell the application which delegate object to use.
    a.setDelegate_(delegate)

    # Now we can start to create the window ...
    frame = NSMakeRect(400, 800, 250, 100)
    # (Don't worry about these parameters for the moment. They just specify
    # the type of window, its size and position etc)
    mask = NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable | NSWindowStyleMaskResizable
    w = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(frame, mask, NSBackingStoreBuffered, False)
    # ... tell it which delegate object to use (here it happens
    # to be the same delegate as the application is using)...
    w.setDelegate_(delegate)
    # ... and set some properties. Unicode strings are preferred.
    w.setTitle_(u'Hello, World!')
    # All set. Now we can show the window ...
    w.orderFrontRegardless()

    # ... and start the application
    w.display()
    a.run()
    #AppHelper.runEventLoop()


if __name__ == '__main__':
    demo()
