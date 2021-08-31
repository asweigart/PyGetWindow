from __future__ import division, print_function

import sys
import pytest
import subprocess
import time
import pygetwindow


def test_basic():

    if sys.platform == "win32":
        subprocess.Popen('notepad')
        time.sleep(0.5)

        testWindows = [pygetwindow.getActiveWindow()]
        # testWindows = pygetwindow.getWindowsWithTitle('Untitled - Notepad')   # Not working in other languages
        assert len(testWindows) == 1

        npw = testWindows[0]  # testWindows[0] is the selected window

        basic_win32(npw)

    elif sys.platform == "linux":
        subprocess.Popen('gedit')
        time.sleep(5)

        testWindows = [pygetwindow.getActiveWindow()]
        assert len(testWindows) == 1

        npw = testWindows[0]  # testWindows[0] is the selected window

        basic_linux(npw)

    elif sys.platform == "darwin":
        subprocess.Popen(['touch', 'test.txt'])
        time.sleep(2)
        subprocess.Popen(['open', '-a', 'TextEdit', 'test.txt'])
        time.sleep(5)

        testWindows = [pygetwindow.getActiveWindow()]
        assert len(testWindows) == 1

        npw = testWindows[0]  # testWindows[0] is the selected window

        basic_macOS(npw)

        subprocess.Popen(['rm', 'test.txt'])

    else:
        raise NotImplementedError('PyGetWindow currently does not support this platform. If you have useful knowledge, please contribute! https://github.com/asweigart/pygetwindow')


def basic_win32(npw):

    assert npw is not None

    # Test maximize/minimize/restore.
    if npw.isMaximized:  # Make sure it starts un-maximized
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
    npw.moveTo(61, 50)

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


def basic_linux(npw):
    # WARNING: Xlib/EWMH does not support negative positions, so be careful with positions calculations
    # and/or set proper screen resolution to avoid negative values (tested OK on 1920x1200)

    assert npw is not None

    wait = True
    timelap = 0.1

    # Test maximize/minimize/restore.
    if npw.isMaximized:  # Make sure it starts un-maximized
        npw.restore(wait=wait)

    assert not npw.isMaximized

    npw.maximize(wait=wait)
    assert npw.isMaximized
    npw.restore(wait=wait)
    assert not npw.isMaximized

    npw.minimize(wait=wait)
    assert npw.isMinimized
    npw.restore(wait=wait)
    assert not npw.isMinimized

    # Test resizing
    npw.resizeTo(800, 600, wait=wait)
    assert npw.size == (800, 600)
    assert npw.width == 800
    assert npw.height == 600

    npw.resizeRel(10, 20, wait=wait)
    assert npw.size == (810, 620)
    assert npw.width == 810
    assert npw.height == 620

    # Test moving
    npw.moveTo(100, 200, wait=wait)
    assert npw.topleft == (100, 200)
    assert npw.left == 100
    assert npw.top == 200
    assert npw.right == 910
    assert npw.bottom == 820
    assert npw.bottomright == (910, 820)
    assert npw.bottomleft == (100, 820)
    assert npw.topright == (910, 200)

    npw.moveRel(1, 2, wait=wait)
    assert npw.topleft == (101, 202)
    assert npw.left == 101
    assert npw.top == 202
    assert npw.right == 911
    assert npw.bottom == 822
    assert npw.bottomright == (911, 822)
    assert npw.bottomleft == (101, 822)
    assert npw.topright == (911, 202)

    # Move via the properties
    npw.resizeTo(800, 600)
    npw.moveTo(200, 200)

    npw.left = 250
    time.sleep(timelap)
    assert npw.left == 250

    npw.right = 950
    time.sleep(timelap)
    assert npw.right == 950

    npw.top = 150
    time.sleep(timelap)
    assert npw.top == 150

    npw.bottom = 775
    time.sleep(timelap)
    assert npw.bottom == 775

    npw.topleft = (155, 350)
    time.sleep(timelap)
    assert npw.topleft == (155, 350)

    npw.topright = (1000, 300)
    time.sleep(timelap)
    assert npw.topright == (1000, 300)

    npw.bottomleft = (300, 975)
    time.sleep(timelap)
    assert npw.bottomleft == (300, 975)

    npw.bottomright = (1000, 900)
    time.sleep(timelap)
    assert npw.bottomright == (1000, 900)

    npw.midleft = (300, 400)
    time.sleep(timelap)
    assert npw.midleft == (300, 400)

    npw.midright = (1050, 600)
    time.sleep(timelap)
    assert npw.midright == (1050, 600)

    npw.midtop = (500, 350)
    time.sleep(timelap)
    assert npw.midtop == (500, 350)

    npw.midbottom = (500, 800)
    time.sleep(timelap)
    assert npw.midbottom == (500, 800)

    npw.center = (500, 350)
    time.sleep(timelap)
    assert npw.center == (500, 350)

    npw.centerx = 1000
    time.sleep(timelap)
    assert npw.centerx == 1000

    npw.centery = 600
    time.sleep(timelap)
    assert npw.centery == 600

    npw.width = 700
    time.sleep(timelap)
    assert npw.width == 700

    npw.height = 500
    time.sleep(timelap)
    assert npw.height == 500

    npw.size = (801, 601)
    time.sleep(timelap)
    assert npw.size == (801, 601)

    # Test closing
    npw.close()


def basic_macOS(npw):

    assert npw is not None

    wait = True
    timelap = 0.0

    # Test maximize/minimize/restore.
    if npw.isMaximized:  # Make sure it starts un-maximized
        npw.restore(wait=wait)

    assert not npw.isMaximized

    npw.maximize(wait=wait)
    assert npw.isMaximized
    npw.restore(wait=wait)
    assert not npw.isMaximized

    npw.minimize(wait=wait)
    assert npw.isMinimized
    npw.restore(wait=wait)
    assert not npw.isMinimized

    # Test resizing
    npw.resizeTo(600, 400, wait=wait)
    assert npw.size == (600, 400)
    assert npw.width == 600
    assert npw.height == 400

    npw.resizeRel(10, 20, wait=wait)
    assert npw.size == (610, 420)
    assert npw.width == 610
    assert npw.height == 420

    # Test moving
    npw.moveTo(50, 24, wait=wait)
    assert npw.topleft == (50, 24)
    assert npw.left == 50
    assert npw.top == 24
    assert npw.right == 660
    assert npw.bottom == 444
    assert npw.bottomright == (660, 444)
    assert npw.bottomleft == (50, 444)
    assert npw.topright == (660, 24)

    npw.moveRel(1, 2, wait=wait)
    assert npw.topleft == (51, 26)
    assert npw.left == 51
    assert npw.top == 26
    assert npw.right == 661
    assert npw.bottom == 446
    assert npw.bottomright == (661, 446)
    assert npw.bottomleft == (51, 446)
    assert npw.topright == (661, 26)

    # Move via the properties
    npw.resizeTo(601, 401, wait=wait)
    npw.moveTo(51, 25, wait=wait)

    npw.left = 200
    time.sleep(timelap)
    assert npw.left == 200

    npw.right = 200
    time.sleep(timelap)
    assert npw.right == 200

    npw.top = 200
    time.sleep(timelap)
    assert npw.top == 200

    npw.bottom = 800
    time.sleep(timelap)
    assert npw.bottom == 800

    npw.topleft = (300, 400)
    time.sleep(timelap)
    assert npw.topleft == (300, 400)

    npw.topright = (300, 400)
    time.sleep(timelap)
    assert npw.topright == (300, 400)

    npw.bottomleft = (300, 700)
    time.sleep(timelap)
    assert npw.bottomleft == (300, 700)

    npw.bottomright = (300, 900)
    time.sleep(timelap)
    assert npw.bottomright == (300, 900)

    npw.midleft = (300, 400)
    time.sleep(timelap)
    assert npw.midleft == (300, 400)

    npw.midright = (300, 400)
    time.sleep(timelap)
    assert npw.midright == (300, 400)

    npw.midtop = (300, 400)
    time.sleep(timelap)
    assert npw.midtop == (300, 400)

    npw.midbottom = (300, 700)
    time.sleep(timelap)
    assert npw.midbottom == (300, 700)

    npw.center = (300, 400)
    time.sleep(timelap)
    assert npw.center == (300, 400)

    npw.centerx = 1000
    time.sleep(timelap)
    assert npw.centerx == 1000

    npw.centery = 300
    time.sleep(timelap)
    assert npw.centery == 300

    npw.width = 600
    time.sleep(timelap)
    assert npw.width == 600

    npw.height = 400
    time.sleep(timelap)
    assert npw.height == 400

    npw.size = (810, 610)
    time.sleep(timelap)
    assert npw.size == (810, 610)

    # Test closing
    npw.close()


def main():
    test_basic()


if __name__ == '__main__':
    pytest.main()
