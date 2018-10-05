import ctypes

# This code taken from https://sjohannes.wordpress.com/2012/03/23/win32-python-getting-all-window-titles/

enumWindows = ctypes.windll.user32.EnumWindows
enumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
getWindowText = ctypes.windll.user32.GetWindowTextW
getWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
isWindowVisible = ctypes.windll.user32.IsWindowVisible

def _getAllTitles():
    titles = []
    def foreach_window(hwnd, lParam):
        if isWindowVisible(hwnd):
            length = getWindowTextLength(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            getWindowText(hwnd, buff, length + 1)
            titles.append(buff.value)
        return True
    enumWindows(enumWindowsProc(foreach_window), 0)

    return titles
