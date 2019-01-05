from __future__ import division, print_function

import pytest
import pygetwindow

import sys
import subprocess
import time

RUNNING_PYTHON_2 = sys.version_info[0] == 2

try:
    if RUNNING_PYTHON_2:
        import Tkinter as tk
    else:
        import tkinter as tk

    rootWindowPosition = '+300+200'
    if tk.TkVersion < 8.0:
        raise RuntimeError('You are running Tk version: ' + str(tk.TkVersion) + 'You must be using Tk version 8.0 or greater to run this test.')
except ImportError:
    raise RuntimeError('Could not import tkinter, which is required for these tests.')



def test_basic_win32():
    subprocess.Popen('notepad')
    time.sleep(0.5)

    testWindows = pygetwindow.getWindowsWithTitle('Untitled - Notepad')
    assert len(testWindows) == 1

    npw = testWindows[0] # testWindows[0] is the notepad window

    # Test maximize/minimize/restore.
    if npw.isMaximized: # Make sure it starts un-maximized
        npw.restore()

    assert not npw.isMaximized

    npw.maximize()
    assert npw.isMaximized
    npw.restore()
    assert not npw.isMaximized
    npw.minimize()
    assert npw.isMinimized
    npw.restore()

    # Test resizing
    npw.resizeTo(300, 200)
    time.sleep(0.5)
    assert npw.size == (300, 200)
    assert npw.width == 300
    assert npw.height == 200

    npw.resizeRel(10, 20)
    time.sleep(0.5)
    assert npw.size == (310, 220)
    assert npw.width == 310
    assert npw.height == 220

    # Test moving
    npw.moveTo(10, 20)
    assert npw.topleft == (10, 20)
    assert npw.left == 10
    assert npw.top == 20
    assert npw.right == 320
    assert npw.bottom == 240
    assert npw.bottomright == (320, 240)
    assert npw.bottomleft == (10, 240)
    assert npw.topright == (320, 20)

    npw.moveRel(1, 2)
    assert npw.topleft == (11, 22)
    assert npw.left == 11
    assert npw.top == 22
    assert npw.right == 321
    assert npw.bottom == 242
    assert npw.bottomright == (321, 242)
    assert npw.bottomleft == (11, 242)
    assert npw.topright == (321, 22)

    # Move via the properties
    npw.resizeTo(301, 201)
    npw.moveTo(11, 21)

    npw.left = 200
    assert npw.left == 200

    npw.right = 200
    assert npw.right == 200

    npw.top = 200
    assert npw.top == 200

    npw.bottom = 200
    assert npw.bottom == 200

    npw.topleft = (300, 400)
    assert npw.topleft == (300, 400)

    npw.topright = (300, 400)
    assert npw.topright == (300, 400)

    npw.bottomleft = (300, 400)
    assert npw.bottomleft == (300, 400)

    npw.bottomright = (300, 400)
    assert npw.bottomright == (300, 400)

    npw.midleft = (300, 400)
    assert npw.midleft == (300, 400)

    npw.midright = (300, 400)
    assert npw.midright == (300, 400)

    npw.midtop = (300, 400)
    assert npw.midtop == (300, 400)

    npw.midbottom = (300, 400)
    assert npw.midbottom == (300, 400)

    npw.center = (300, 400)
    assert npw.center == (300, 400)

    npw.centerx = 1000
    assert npw.centerx == 1000

    npw.centery = 1000
    assert npw.centery == 1000

    npw.width = 300
    assert npw.width == 300

    npw.height = 200
    assert npw.height == 200

    npw.size = (301, 201)
    assert npw.size == (301, 201)


    # Test closing
    npw.close()


if __name__ == '__main__':
    pytest.main()
