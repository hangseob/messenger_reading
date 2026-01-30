import win32gui
import win32con
import time
import ctypes

def find_input_hwnd(target_title):
    target_hwnd = None
    def enum_top(hwnd, param):
        nonlocal target_hwnd
        if win32gui.IsWindowVisible(hwnd):
            if target_title in win32gui.GetWindowText(hwnd) and win32gui.GetClassName(hwnd) == "TfrmDccChat":
                target_hwnd = hwnd
                return False
        return True
    try: win32gui.EnumWindows(enum_top, None)
    except: pass
    
    if not target_hwnd: return None
    
    input_hwnd = None
    def enum_child(hwnd, param):
        nonlocal input_hwnd
        if "RichEdit" in win32gui.GetClassName(hwnd):
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            if not (style & win32con.ES_READONLY):
                input_hwnd = hwnd
                return False
        return True
    try: win32gui.EnumChildWindows(target_hwnd, enum_child, None)
    except: pass
    return input_hwnd

def send_v4(target_title, text):
    hwnd = find_input_hwnd(target_title)
    if not hwnd:
        print(f"Window or input for {target_title} not found.")
        return False
        
    print(f"Found input HWND: {hwnd}")
    
    # 1. Clear existing text
    win32gui.SendMessage(hwnd, win32con.WM_SETTEXT, 0, "")
    
    # 2. Use EM_REPLACESEL to insert text
    # This is often more successful than WM_SETTEXT for RichEdit
    win32gui.SendMessage(hwnd, win32con.EM_REPLACESEL, True, text)
    
    # 3. Verify
    length = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
    buf = ctypes.create_unicode_buffer(length + 1)
    win32gui.SendMessage(hwnd, win32con.WM_GETTEXT, length + 1, buf)
    if buf.value != text:
        print(f"Verification failed. Text is: '{buf.value}'")
        print("Tip: KBond may be running as Admin. Please run terminal as Admin.")
    else:
        print("Successfully set text using EM_REPLACESEL.")
        
    # 4. Trigger Enter
    win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
    win32gui.PostMessage(hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)
    print("Sent Enter trigger.")
    return True

if __name__ == "__main__":
    send_v4("정민후", "자동메세지 테스트입니다")
