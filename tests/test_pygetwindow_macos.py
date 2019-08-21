from __future__ import division, print_function

import pytest
import pygetwindow

import sys


RUNNING_PYTHON_2 = sys.version_info[0] == 2

if sys.platform != 'darwin':
    pytest.skip("skipping macos-only tests", allow_module_level=True)


def test_get_all_titles():
    """Should return a list of window titles"""
    wl = pygetwindow.getAllTitles()
    assert len(wl) > 0
    assert isinstance(wl[0], str)


def test_getActiveWindow():
    """Should return a Window object of the currently active Window."""
    w = pygetwindow.getActiveWindow()
    assert isinstance(w, pygetwindow.Window)


def test_windowHasBounds():
    """Should return a Window object of the currently active Window."""
    w = pygetwindow.getActiveWindow()
    # Check bounds have been set
    bounds = [
        'area',
        'bottom',
        'bottomleft',
        'bottomright',
        'box',
        'center',
        'centerx',
        'centery',
        'height',
        'left',
        'midbottom',
        'midleft',
        'midright',
        'midtop',
        'right',
        'size',
        'top',
        'topleft',
        'topright',
        'width',
    ]
    for k in bounds:
        assert hasattr(w, k)
        v = getattr(w, k)
        assert(v != None)


def test_window_geometry():
    """Tests that we can find a logical center of the window"""
    w = pygetwindow.getActiveWindow()
    assert w.centerx == int(w.box.width / 2 + w.box.left)
    assert w.centery == int(w.box.height / 2 + w.box.top)
