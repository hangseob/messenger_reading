import win32gui
import win32con
import ctypes
import time
import sys

# Ensure Korean output works
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def find_kbond_input_field(target_title):
    target_hwnd = None
    
    def enum_top_cb(hwnd, param):
        nonlocal target_hwnd
        if win32gui.IsWindowVisible(hwnd):
            cls = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            if cls == "TfrmDccChat" and target_title in title:
                target_hwnd = hwnd
                return False
        return True

    try:
        win32gui.EnumWindows(enum_top_cb, None)
    except Exception:
        pass
    
    if not target_hwnd:
        return None

    input_field_hwnd = None
    def enum_child_cb(hwnd, param):
        nonlocal input_field_hwnd
        cls = win32gui.GetClassName(hwnd)
        if "RichEdit" in cls:
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            is_readonly = bool(style & win32con.ES_READONLY)
            if not is_readonly:
                input_field_hwnd = hwnd
                return False
        return True

    try:
        win32gui.EnumChildWindows(target_hwnd, enum_child_cb, None)
    except Exception:
        pass
    return input_field_hwnd

def send_message(target_title, text):
    hwnd = find_kbond_input_field(target_title)
    if not hwnd:
        print(f"Error: Could not find input field for window '{target_title}'")
        return False

    print(f"Found input field (HWND: {hwnd}) for '{target_title}'")
    
    # Set text
    win32gui.SendMessage(hwnd, win32con.WM_SETTEXT, 0, text)
    time.sleep(0.5)
    
    # Verify text was set
    length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    buffer = ctypes.create_unicode_buffer(length + 1)
    win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length + 1, buffer)
    if buffer.value == text:
        print(f"Successfully set text in input field: '{buffer.value}'")
    else:
        print(f"Warning: Text in input field is different: '{buffer.value}'")

    # Simulate Enter key to send
    # Some Delphi apps need both WM_KEYDOWN and WM_KEYUP or WM_CHAR
    win32gui.SendMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    time.sleep(0.1)
    win32gui.SendMessage(hwnd, win32con.WM_CHAR, win32con.VK_RETURN, 0)
    time.sleep(0.1)
    win32gui.SendMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
    
    print(f"Sent message trigger to '{target_title}'")
    return True

if __name__ == "__main__":
    target = "정민후"
    message = "자동메세지 테스트입니다"
    send_message(target, message)
